from fastapi import APIRouter, HTTPException, Depends,Query
from sqlmodel import Session, select, SQLModel, Field ,delete,func,and_
from .db import engine, get_session
from pydantic import  validator, BaseModel
from sqlalchemy.orm import aliased
from typing import List,Optional
from routes.commonflds import CommonFields  
from datetime import datetime,date
from routes.userauth import get_current_user
from routes.taxmaster import TaxHeader
from routes.company import Company


router = APIRouter( tags=["HSN"])

class HSN(CommonFields, table=True):
    __tablename__ = "hsn"
    __table_args__ = {"extend_existing": True}       
    companyid: int = Field(foreign_key="company.id", nullable=False)
    companyno: str
    hsncode: str = Field(nullable=False)
    hsndescription: str = Field(index=True,nullable=False)
    taxname: int = Field(foreign_key="taxheader.id", nullable=False)
    taxrate: float = Field(default=0.0, nullable=False)
    effective_date: date
    active: bool = True  # default value
    class Config:
        orm_mode = True

class HsnPost(BaseModel):
    companyid:int
    companyno: str
    hsncode: str
    hsndescription: str
    taxname: int
    taxrate: float
    effective_date: date
    active: bool = True
    createdby: str
    modifiedby: str 

class HsnRead(BaseModel):
    id: int
    companyid: int
    companyno : str
    companyname: str
    hsncode: str
    hsndescription: str
    taxheaderid:int
    taxname: str    
    taxrate: float
    effective_date: date
    active: bool
    createdby: str
    modifiedby: str
    createdon: datetime
    modifiedon: datetime
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }       

class HsnUpdate(BaseModel): 
    companyid:int
    companyno: str
    hsncode: str
    hsndescription: str
    taxname: int
    taxrate: float
    effective_date: date
    active: bool     
    modifiedby: str    
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }      
class HsnSearch(BaseModel):
    id: int
    companyid:int
    companyno: str
    companyname:str
    hsncode: str
    hsndescription: str 
    taxheaderid:int
    taxname: str
    taxrate: float
    effective_date: date
    active: bool    

class HsnResponse(BaseModel):
    total: int
    hsnlist: List[HsnRead]

@router.post("/addhsn/", response_model=HsnPost)
def create_hsn(HSNP: HsnPost, session: Session = Depends(get_session),
            #    current_user: dict = Depends(get_current_user)
               ): 
    # Check duplicate
    db_HSN = session.exec(select(HSN).where(
        HSN.hsncode == HSNP.hsncode,
        HSN.companyid == HSNP.companyid
    )).first()
    if db_HSN:
        raise HTTPException(status_code=400, detail="HSN code already exists for this company")

    # Create HSN object
    db_HSN = HSN.from_orm(HSNP)
    session.add(db_HSN)
    session.commit()
    session.refresh(db_HSN)
    return db_HSN 


@router.post("/hsnupdate/{hsnid}", response_model=HsnUpdate)
def update_state(hsnid:int,hsn: HsnUpdate, session: Session= Depends(get_session),
                #   current_user :dict = Depends(get_current_user)
                 ):
    db_hsn = session.exec(select(HSN).where(HSN.id == hsnid)).first()
    if not db_hsn:
        raise HTTPException(status_code=400, detail="HSN Not found")
        
    for key, value in hsn.dict(exclude_unset=True).items():
        setattr(db_hsn, key, value)
    session.add(db_hsn)
    session.commit()
    session.refresh(db_hsn)
    return db_hsn

@router.get("/hsn/search/{companyid}", response_model=List[HsnSearch])
def search_state(
    companyid: int,
    field: str = Query(...),
    value: str = Query(...),
    db: Session = Depends(get_session)
):
    # Aliases (optional)
    t = TaxHeader
    c = Company
    # Base query: pick only columns you need
    query = db.query(
        HSN.id,
        HSN.companyid,
        c.companyname,
        c.companyno,
        HSN.hsncode,
        HSN.hsndescription,
        t.id.label("taxheaderid"),
        t.taxname,
        t.taxrate,
        HSN.effective_date,
        HSN.active, 
    ).join(c, HSN.companyid == c.id).join(t, HSN.taxname == t.id ).filter(c.id== companyid)  

    # Apply filters
    if field == "hsncode":
        query = query.filter(HSN.hsncode.ilike(f"%{value}%"))
    elif field == "hsndescription":
        query = query.filter(HSN.hsndescription.ilike(f"%{value}%"))  

    results = query.all()

    # Each row is a tuple → map to dict
    return [
        {
            "id": r.id,
            "hsncode": r.hsncode,
            "hsndescription": r.hsndescription,
            "active": r.active,
            "taxheaderid": r.taxheaderid,
            "taxname":r.taxname,
            "taxrate": r.taxrate,
            "effective_date":r.effective_date,
            "companyid":r.companyid,
            "companyname":r.companyname,
            "companyno":r.companyno,
        }
        for r in results
    ]

@router.get("/hsn/{companyid}", response_model=HsnResponse)
def read_hsn(companyid: int, skip: int = 0, limit: int = 10, session: Session = Depends(get_session),
                 current_user :dict = Depends(get_current_user)
                ):
    # Aliases (optional)
    t = TaxHeader
    c = Company

# Query HSN with joins
    hsnreadvalue = session.exec(
    select(
        HSN,
        t.id.label("taxheaderid"),
        t.taxname,
        t.taxrate,
        c.companyno,
        c.companyname
     )
    .join(c, HSN.companyid == c.id)                # join company
    .outerjoin(t, HSN.taxname == t.id)            # left join taxheader
    .where(c.id == companyid)
    .order_by(HSN.hsncode)
    .offset(skip)
    .limit(limit)
    ).all()

# Total count of HSN for the company
    totalcount = session.exec(select(func.count()).select_from(HSN).where(HSN.companyid == companyid)).one()
    hsnlist = [      
            HsnRead(
               id = t[0].id,
                hsncode= t[0].hsncode,
                hsndescription= t[0].hsndescription,
                taxheaderid= t[1] ,
                taxname= t[2] ,
                taxrate= t[3] ,
                effective_date= t[0].effective_date,
                active= t[0].active,
                createdby= t[0].createdby,
                modifiedby= t[0].modifiedby,
                createdon= t[0].createdon,
                modifiedon= t[0].modifiedon,
                companyid=t[0].companyid,
                companyno=t[4],
                companyname=t[5],
            ) for t in  hsnreadvalue
        
    ]
    return { "hsnlist":hsnlist , "total":totalcount}

@router.delete("/hsn/hsndelete/{hsnid}")
def delete_hsn(hsnid: int, session: Session = Depends(get_session)):     
    HSNDel = session.get(HSN, hsnid)
    if not HSN:
        raise HTTPException(status_code=404, detail="City not found")
    session.delete(HSNDel)
    session.commit()
    return {"ok": True}   