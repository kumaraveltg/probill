from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select, SQLModel, Field ,delete
from .db import engine, get_session
from pydantic import  validator, BaseModel
from typing import List 
from routes.commonflds import CommonFields  
from datetime import datetime


router = APIRouter( tags=["TaxMaster"])

class TaxHeader(CommonFields, table=True):
    __tablename__ = "taxheader"
    __table_args__ = {"extend_existing": True} 
    companyid: int = Field(foreign_key="company.id", nullable=False)
    taxtype: str = Field(nullable=False)
    taxname: str = Field(index=True,nullable=False)
    taxrate: float = Field(default=0.0, nullable=False)
    active: bool = True  # default value

class TaxMasterDetail(SQLModel, table=True):
    __tablename__ = "taxdetail"
    __table_args__ = {"extend_existing": True} 
    id: int | None = Field(default=None, primary_key=True)
    taxheaderid: int = Field(foreign_key="taxheader.id", nullable=False)
    rowno: int = Field(default=1, nullable=False)
    taxsupply: str = Field(nullable=False)
    taxslabname: str = Field(index=True,nullable=False)
    taxrate: float = Field(default=0.0,nullable=False) 

class PTaxHeader(BaseModel):  
    createdby: str = Field(nullable=False)
    modifiedby: str = Field(nullable=False)
    companyid: int = Field(default=0,nullable=False)
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

class PTaxDetail(BaseModel):
    taxheaderid: int = Field(default= 0,nullable=False)
    rowno: int = Field(default=1, nullable=False)
    taxsupply: str = Field(nullable=False)
    taxslabname: str = Field(nullable=False)
    taxrate: float = Field(default=0.0,nullable=False) 
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

def generate_taxdetails(taxheaderid: int, taxtype: str, taxrate: float ) -> List[PTaxDetail]:
    tax_details = []

    if taxtype.upper() == "GST":
            half_rate = taxrate / 2
            slabs = [
                ("Inter", f"IGST {taxrate}%", taxrate),
                ("Intra", f"CGST {half_rate}%", half_rate),
                ("Intra", f"SGST {half_rate}%", half_rate)
            ]
         
    else:
        slabs = []

    for idx, (supply, name, rate) in enumerate(slabs, start=1):
        tax_details.append(PTaxDetail(
            taxheaderid=taxheaderid,
            rowno=idx,
            taxsupply=supply,
            taxslabname=name,
            taxrate=rate
        ))
    return tax_details

@router.post("/taxmaster/", response_model=PTaxHeader)
def create_taxmaster(tax: PTaxHeader, session: Session = Depends(get_session)):
    statement= select(TaxHeader).where(TaxHeader.companyid==tax.companyid, TaxHeader.taxname==tax.taxname )
    results = session.exec(statement)
    existing_tax = results.first()
    if existing_tax:
        raise HTTPException(status_code=400, detail="Tax with this name already exists for the company.")   

    db_tax = TaxHeader.from_orm(tax)
    session.add(db_tax)
    session.commit()
    session.refresh(db_tax)

    tax_details = generate_taxdetails(db_tax.id, db_tax.taxtype, db_tax.taxrate )
    for detail in tax_details:
        db_detail = TaxMasterDetail.from_orm(detail)
        session.add(db_detail)
    session.commit()

    return tax

@router.post("/taxupdate/{taxheaderid}", response_model=Taxupdate)
def update_taxmaster(taxheaderid: int,tax: Taxupdate, session: Session = Depends(get_session)):
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
    tax_details = generate_taxdetails(db_tax.id, db_tax.taxtype, db_tax.taxrate )
    for detail in tax_details:
        db_detail = TaxMasterDetail.from_orm(detail)
        session.add(db_detail)
    session.commit()

    return tax

@router.get("/gettax/{companyid}", response_model=Ptaxread)
def read_taxes(companyid: int, session: Session = Depends(get_session)):
    tax_header = session.get(TaxHeader, companyid)
    if not tax_header:
        raise HTTPException(status_code=404, detail="Tax header not found")

    statement = select(TaxMasterDetail).where(TaxMasterDetail.taxheaderid == tax_header.id)
    results = session.exec(statement)
    tax_details = results.all()

    return Ptaxread(taxheader=PTaxHeader.from_orm(tax_header), taxdetails=[PTaxDetail.from_orm(detail) for detail in tax_details])      

@router.get("/gettaxdetails/{taxheaderid}", response_model=Ptaxread)
def read_taxdetails(taxheaderid: int, session: Session = Depends(get_session)): 
    tax_header = session.get(TaxHeader, taxheaderid)
    if not tax_header:
        raise HTTPException(status_code=404, detail="Tax header not found")

    statement = select(TaxMasterDetail).where(TaxMasterDetail.taxheaderid == taxheaderid)
    results = session.exec(statement)
    tax_details = results.all()

    return Ptaxread(taxheader=PTaxHeader.from_orm(tax_header), taxdetails=[PTaxDetail.from_orm(detail) for detail in tax_details])      

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
