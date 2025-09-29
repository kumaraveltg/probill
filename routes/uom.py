from fastapi import APIRouter,  HTTPException,Depends,Query
from sqlmodel import Session, select,SQLModel,Field,Column,Relationship,func,and_
from .db import engine, get_session
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER,JSON
from pydantic import EmailStr,validator,BaseModel
from typing import List, Optional,Dict, Any 
from routes.commonflds import CommonFields
from datetime import datetime, timedelta, date
from routes.company import Company  
from routes.userauth import get_current_user

router = APIRouter(tags=["UOM"])

class UOM(CommonFields, table=True):
    __tablename__ = "uom"
    __table_args__ = {"extend_existing": True} 
    companyid: int = Field(foreign_key="company.id", nullable=False)
    uomname: str = Field(index=True,nullable=False)
    uomcode: str = Field(index=True,nullable=False)
    active: bool = True  # default value

#schema/ pydantic
class PUOM(BaseModel):
    companyid: int = Field(default= 0,nullable=False)
    createdby: str = Field(nullable=False)
    modifiedby: str = Field(nullable=False)
    uomname: str = Field(nullable=False)
    uomcode: str = Field(nullable=False)
    active: bool = True 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }
    @validator( "modifiedby","uomname","uomcode" )
    def must_not_be_empty(cls, v):
      if not v or not v.strip():
         raise ValueError("This field is required")
      return v
    
class UOMUpdate(BaseModel):
    uomname: Optional[str] = None
    uomcode: Optional[str] = None
    modifiedby: Optional[str]= None
    active: Optional[bool] = None   
    @validator( "modifiedby" )
    def must_not_be_empty(cls, v):
      if not v or not v.strip():
         raise ValueError("This field is required")
      return v
    
class UOMRead(BaseModel):
    id: int
    createdby: str
    createdon: datetime 
    modifiedby: str
    modifiedon: datetime   
    companyid: int
    companyname: Optional[str] = None     
    uomname: str
    uomcode: str
    active: bool

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }
class UOMDelete(BaseModel):
    id: int
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }
class UomSearch(BaseModel):
    id: int
    uomname: str
    uomcode: str
    active: bool
    companyid: int
    companyname: Optional[str] = None

class UomResponse(BaseModel):
    total: int
    uoms: List[UOMRead]   


@router.post("/uom/", response_model=UOMRead)
def create_uom(uom: PUOM, session: Session = Depends(get_session)):
    if uom.companyid !=0:
        company = session.get(Company, uom.companyid)
        if not company:
            raise HTTPException(status_code=400, detail="Invalid company ID")
    if not uom.uomname or not uom.uomname.strip():
        raise HTTPException(status_code=400, detail="UOM name is required")
    if not uom.uomcode or not uom.uomcode.strip():
        raise HTTPException(status_code=400, detail="UOM code is required")
    existing_uom = session.exec(
        select(UOM,Company.companyname).join(Company, UOM.companyid == Company.id).where(UOM.uomcode == uom.uomcode)   
    ).first()
    if existing_uom:
        raise HTTPException(status_code=400, detail="UOM code already exists")
    
    db_uom = UOM.from_orm(uom)
    session.add(db_uom)
    session.commit()
    session.refresh(db_uom)
    return db_uom 
  
@router.post("/uom/{uom_id}", response_model=UOMRead)
def update_uom(uom_id: int, uom_update: UOMUpdate, session: Session = Depends(get_session),
               current_user: dict=Depends(get_current_user)):
    db_uom = session.get(UOM, uom_id)
    if not db_uom:
        raise HTTPException(status_code=404, detail="UOM not found")
    
    for key, value in uom_update.model_dump(exclude_unset=True).items():
        setattr(db_uom, key, value)
    
    session.add(db_uom)
    session.commit()
    session.refresh(db_uom)
    return db_uom

@router.get("/uom/search/{companyid}", response_model=List[UomSearch])
def search_uom( 
     companyid: int,
     field: str = Query(...),
     value: str = Query(...),     
    db: Session = Depends(get_session)
):
    Query = db.query(
        UOM.id,
        UOM.uomname,
        UOM.uomcode,
        UOM.active,
        UOM.companyid,
        Company.companyname
    ).join(Company, UOM.companyid == Company.id ,isouter=True ).filter(Company.id== companyid) 

    if field == "uomname":
        Query = Query.filter(UOM.uomname.ilike(f"%{value}%"))
    elif field == "uomcode":
        Query = Query.filter(UOM.uomcode.ilike(f"%{value}%"))
    elif field == "companyname":
        Query = Query.filter(Company.companyname.ilike(f"%{value}%"))
    else:
        raise HTTPException(status_code=400, detail="Invalid search field")
    
    results = Query.all()  
    return [
        {   "id": r.id,
            "uomname": r.uomname,
            "uomcode": r.uomcode,
            "active": r.active,
            "companyid": r.companyid,
            "companyname": r.companyname,
        }   
        for r in results
    ]


@router.get("/uomlist/{company_id}/",response_model= UomResponse)
def uom_list( company_id: int,skip: int = 0, limit: int = 10,  session: Session=Depends(get_session)
             ,current_user:dict=Depends(get_current_user)):
    uom_list = session.exec(
        select(UOM, Company.companyname,Company.id).join(Company, UOM.companyid == Company.id ,isouter=True )
        .where( and_( UOM.active==True 
        , UOM.companyid == company_id )).order_by(UOM.uomname).offset(skip).limit(limit )).all()
    totalcount = session.exec(
        select(func.count(UOM.id)).where( and_( UOM.active==True
        , UOM.companyid == company_id ))  ).one()
    
    result = []
    for uom, companyname,companyid in uom_list:
        uom_data = UOMRead.from_orm(uom)
        uom_data.companyname = companyname
        uom_data.companyid = companyid
        result.append(uom_data)
    
    return { "total": totalcount, "uoms": result }


@router.delete("/uomdelete/{uom_id}", response_model=UOMDelete)
def delete_uom(uom_id: int, session: Session = Depends(get_session)):
    uom = session.get(UOM, uom_id)
    if not uom:
        raise HTTPException(status_code=404, detail="UOM not found")
    session.delete(uom)
    session.commit()
    uom_data = UOMDelete.from_orm(uom)
    return uom_data
