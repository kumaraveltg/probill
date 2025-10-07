from fastapi import APIRouter, HTTPException, Depends,Query
from sqlmodel import Session, select, SQLModel, Field ,delete,func,and_
from .db import engine, get_session
from pydantic import  validator, BaseModel
from typing import List,Optional
from routes.commonflds import CommonFields  
from datetime import datetime
from routes.userauth import get_current_user
from routes.company import Company


router = APIRouter( tags=["TaxMaster"])

class TaxHeader(CommonFields, table=True):
    __tablename__ = "taxheader"
    __table_args__ = {"extend_existing": True} 
    companyid: int = Field(foreign_key="company.id", nullable=False)
    companyno: str    
    taxtype: str = Field(nullable=False)
    taxname: str = Field(index=True,nullable=False)
    taxrate: float = Field(default=0.0, nullable=False)
    active: bool = True  # default value
    class Config:
        orm_mode = True
      

class TaxMasterDetail(SQLModel, table=True):
    __tablename__ = "taxdetail"
    __table_args__ = {"extend_existing": True} 
    id: int | None = Field(default=None, primary_key=True)
    taxheaderid: int = Field(foreign_key="taxheader.id", nullable=False)
    rowno: int = Field(default=1, nullable=False)
    taxsupply: str = Field(nullable=False)
    taxslabname: str = Field(index=True,nullable=False)
    gtaxrate: float = Field(default=0.0,nullable=False) 
    class Config:
        orm_mode = True

class PTaxHeader(BaseModel):  
    id: Optional[int] = None 
    createdby: str = Field(nullable=False)
    modifiedby: str = Field(nullable=False)
    companyid: int = Field(default=0,nullable=False)
    companyno: Optional[str] = None
    companyname: Optional[str] = None
    taxtype: str = Field(default="GST",nullable=False)
    taxname: str = Field(nullable=False)
    taxrate: float = Field(default=0.0, nullable=False)
    active: bool = True 
    createdon: datetime
    modifiedon: datetime
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }       

class PTaxDetail(BaseModel):
    taxheaderid: int = Field(default= 0,nullable=False)
    rowno: int = Field(default=1, nullable=False)
    taxsupply: str = Field(nullable=False)
    taxslabname: str = Field(nullable=False)
    gtaxrate: float = Field(default=0.0,nullable=False) 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class Ptaxread(BaseModel):
    taxheader: PTaxHeader
    taxdetails: List[PTaxDetail] = []
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class Taxupdate(BaseModel):
    companyid: int = Field(default=0,nullable=False)
    modifiedby: str = Field(nullable=False)
    taxtype: str = Field(default="GST",nullable=False)
    taxname: str = Field(nullable=False)
    taxrate: float = Field(default=0.0, nullable=False)
    active: bool = True 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }
class TaxResponse(BaseModel):
    total: int
    taxlist: List[PTaxHeader]

class TaxSearch(BaseModel):
    id: int
    companyid:int
    companyname: str
    companyno: str
    taxname: str
    taxtype: str
    taxrate :int

class TaxDetailRequest(BaseModel): 
    taxtype: str
    taxrate: float

class TaxDetailResponse(BaseModel):
    taxhdr: TaxHeader
    taxdtl: List[TaxMasterDetail]   
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }


@router.post("/taxdet", response_model= List[PTaxDetail])
def generate_taxdetails(payload:TaxDetailRequest):
    tax_details = []

    if payload.taxtype.upper() == "GST":
            half_rate = payload.taxrate / 2
            slabs = [
                ("Inter", f"IGST {payload.taxrate}%", payload.taxrate),
                ("Intra", f"CGST {half_rate}%", half_rate),
                ("Intra", f"SGST {half_rate}%", half_rate)
            ]
         
    else:
        slabs = []

    for idx, (supply, name, rate) in enumerate(slabs, start=1):
        tax_details.append(PTaxDetail( 
            rowno=idx,
            taxsupply=supply,
            taxslabname=name,
            gtaxrate=rate, 
        ))
    return tax_details

@router.post("/taxmaster/", response_model=PTaxHeader)
def create_taxmaster(tax: TaxHeader, session: Session = Depends(get_session),
                     cu:dict=Depends(get_current_user)):
    statement= select(TaxHeader).where(TaxHeader.companyid==tax.companyid, TaxHeader.taxname==tax.taxname )
    results = session.exec(statement)
    existing_tax = results.first()
    if existing_tax:
        raise HTTPException(status_code=400, detail="Tax with this name already exists for the company.")   

    db_tax = TaxHeader.from_orm(tax)
    session.add(db_tax)
    session.commit()
    session.refresh(db_tax)

    tax_details = generate_taxdetails( TaxDetailRequest(
        taxtype=tax.taxtype,
        taxrate=tax.taxrate
    ) )
    for detail in tax_details: 
        db_detail = TaxMasterDetail.from_orm(detail)
        db_detail.taxheaderid=db_tax.id
        session.add(db_detail)
        session.commit() 
        
    return db_tax

@router.post("/taxupdate/{taxheaderid}", response_model=Taxupdate)
def update_taxmaster(taxheaderid: int,tax: Taxupdate, session: Session = Depends(get_session),current_user:dict = Depends(get_current_user)):
    db_tax = session.get(TaxHeader, taxheaderid)
    if not db_tax:
        raise HTTPException(status_code=404, detail="Tax not found")

    for key, value in tax.model_dump().items():
        setattr(db_tax, key, value)

    session.add(db_tax)
    session.commit()
    session.refresh(db_tax)

    # Delete existing tax details
    delete_stmt = delete(TaxMasterDetail).where(TaxMasterDetail.taxheaderid == db_tax.id)
    session.exec(delete_stmt)
    session.commit()

    # Generate and add new tax details
    tax_details = generate_taxdetails(TaxDetailRequest( 
        taxtype=db_tax.taxtype,
        taxrate=db_tax.taxrate
    ) )
    for detail in tax_details:
        db_detail = TaxMasterDetail.from_orm(detail)
        db_detail.taxheaderid=db_tax.id
        session.add(db_detail)
        session.commit()

    return tax

@router.get("/tax/search/{companyid}",response_model=List[TaxSearch])
def tax_search( companyid: int,
     field: str = Query(...),
     value: str = Query(...),     
     db: Session = Depends(get_session)
    ):
    query = db.query(
        TaxHeader.id,
        TaxHeader.taxtype,
        TaxHeader.taxname,
        TaxHeader.taxrate,
        TaxHeader.active,
        TaxHeader.companyid,
        Company.companyname,
        Company.companyno
    ).join(Company, TaxHeader.companyid == Company.id ,isouter=True ).filter(Company.id== companyid) 

    if field == "taxname":
        query = query.filter(TaxHeader.taxname.ilike(f"%{value}%")) 
    elif field == "companyname":
        query = query.filter(Company.companyname.ilike(f"%{value}%"))
    else:
        raise HTTPException(status_code=400, detail="Invalid search field")
    
    results = query.all()  

    return [
      {   
            "id": r.id,
            "taxname": r.taxname,
            "taxtype": r.taxtype,
            "taxrate": r.taxrate,
            "active": r.active,
            "companyid": r.companyid,
            "companyname": r.companyname,
            "companyno":r.companyno,
        }      
     for r in results
    ]

@router.get("/gettax/{companyid}", response_model=TaxResponse)
def read_taxes(
    companyid: int,
    skip: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    # Use TaxHeader ORM, not PTaxHeader
    tax_header = session.exec(
        select(TaxHeader, Company.companyname, Company.companyno)
        .join(Company, TaxHeader.companyid == Company.id, isouter=True)
        .where(and_(TaxHeader.active == True, TaxHeader.companyid == companyid))
        .order_by(TaxHeader.taxname)
        .offset(skip)
        .limit(limit)
    ).all()

    if not tax_header:
        raise HTTPException(status_code=404, detail="Tax header not found")

    # Total count
    totalcount = session.exec(
        select(func.count(TaxHeader.id)).where(TaxHeader.companyid == companyid)
    ).first()

    # Map SQLAlchemy ORM + joined fields to Pydantic model
    taxlist = [
        PTaxHeader(
            id=t[0].id,
            createdby=t[0].createdby or "system",
            modifiedby=t[0].modifiedby or "system",
            companyid=t[0].companyid,
            companyno=t[2] if len(t) > 2 else "",
            companyname=t[1] if len(t) > 1 else "",
            taxtype=t[0].taxtype or "GST",
            taxname=t[0].taxname or "",
            taxrate=t[0].taxrate or 0.0,
            active=t[0].active,
            createdon=t[0].createdon,
            modifiedon=t[0].modifiedon,
        )
        for t in tax_header
    ]

    return TaxResponse(total=totalcount, taxlist=taxlist)
 

@router.get("/gettaxdetails/{taxheaderid}", response_model=TaxDetailResponse)
def read_taxdetails(taxheaderid: int, session: Session = Depends(get_session)
                    # , current_user: dict = Depends(get_current_user)
                    ): 
    tax_header = session.get(TaxHeader, taxheaderid)
    if not tax_header:
        raise HTTPException(status_code=404, detail="Tax header not found")

    statement = select(TaxMasterDetail).where(TaxMasterDetail.taxheaderid == taxheaderid) 
    results = session.exec(statement)
    tax_details = results.all() 

    return TaxDetailResponse(taxhdr=tax_header, taxdtl=tax_details)

@router.get("/gettaxbyname/{companyid}/{taxname}", response_model=Ptaxread)
def read_taxbyname(companyid: int,taxname:str, session: Session = Depends(get_session)):
    statement = select(TaxHeader).where(TaxHeader.companyid == companyid, TaxHeader.taxname==taxname)
    results = session.exec(statement)
    tax = results.first()
    if not tax:
        raise HTTPException(status_code=404, detail="Tax not found")
    
    details_stmt = select(TaxMasterDetail).where(TaxMasterDetail.taxheaderid == tax.id)
    taxmaster = session.exec(details_stmt).all()
    return Ptaxread(taxheader=PTaxHeader.from_orm(tax), taxdetails=[PTaxDetail.from_orm(detail) for detail in taxmaster])     

@router.delete("/deletetax/{taxheaderid}", response_model=dict)
def delete_taxmaster(taxheaderid: int, session: Session = Depends(get_session)):    
    db_tax = session.get(TaxHeader, taxheaderid)
    if not db_tax:
        raise HTTPException(status_code=404, detail="Tax not found")

    # Delete associated tax details first
    session.exec(delete(TaxMasterDetail).where(TaxMasterDetail.taxheaderid == taxheaderid))
    session.commit()

    # Delete the tax header
    session.delete(db_tax)
    session.commit()

    return {"detail": "Tax deleted successfully"}
