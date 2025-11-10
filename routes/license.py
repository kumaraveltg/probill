from fastapi import APIRouter, HTTPException, Depends,Query
from sqlmodel import Session, select, SQLModel, Field ,delete,func,and_
from .db import engine, get_session
from pydantic import  validator, BaseModel
from sqlalchemy.orm import aliased
from typing import List,Optional
from routes.commonflds import CommonFields  
from datetime import datetime,date,timedelta
from routes.userauth import get_current_user
from routes.taxmaster import TaxHeader
from routes.company import Company
import uuid


router = APIRouter( tags=["License"])

class Licenses(CommonFields, table=True):
    __tablename__ = "licenses"
    __table_args__ = {"extend_existing": True} 
    companyid: int = Field(foreign_key="company.id", nullable=False)
    companyno: Optional[str]=None 
    planname: Optional[str]=None 
    planperiod: str=Field(nullable=False)
    startdate: date = Field(nullable=False)
    enddate : date  = Field(nullable=False)  
    userlimit: int=Field(default=0,nullable=True)
    liecensekey:Optional[str]=None
    active : bool = Field(default=True,nullable=True)
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class LicensePost(BaseModel):
    companyid: int = Field(foreign_key="company.id", nullable=False)
    companyno: Optional[str]=None 
    planname: Optional[str]=None     
    planperiod:Optional[str]=None
    userlimit: int=Field(default=0,nullable=True)
    liecensekey:Optional[str]=None
    active : bool = Field(default=True,nullable=True)
    createdby: str
    modifiedby: str

class LicenseUpdate(BaseModel):
    companyid: int = Field(foreign_key="company.id", nullable=False)
    companyno: Optional[str]=None 
    planname: Optional[str]=None  
    planperiod:str
    startdate: date = Field(nullable=False)
    enddate : date  = Field(nullable=False)  
    userlimit: int=Field(default=0,nullable=True)
    liecensekey:Optional[str]=None
    active : bool = Field(default=True,nullable=True) 
    modifiedby: str
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }      

class LicenseRead(BaseModel):
    id:int
    companyid: int = Field(foreign_key="company.id", nullable=False)
    companyno: Optional[str]=None 
    planname: Optional[str]=None 
    planperiod: Optional[str]=None  
    startdate: date = Field(nullable=False)
    enddate : date  = Field(nullable=False)  
    userlimit: int=Field(default=0,nullable=True)
    liecensekey:Optional[str]=None
    active : bool = Field(default=True,nullable=True)
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

class LicenseSearch(BaseModel):
    id:int
    companyid: int = Field(foreign_key="company.id", nullable=False)
    companyno: Optional[str]=None 
    planname: Optional[str]=None  
    planperiod: Optional[str]=None  
    startdate: date = Field(nullable=False)
    enddate : date  = Field(nullable=False)  
    userlimit: int=Field(default=0,nullable=True)
    active : bool = Field(default=True,nullable=True)
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

class LicenseResponse(BaseModel):
    license_list: List[LicenseRead]
    total: int

def generate_license_key():
    return str(uuid.uuid4()).upper().replace("-", "")



@router.post("/addlicense/", response_model=LicensePost)
def create_license(license_input: LicensePost, session: Session = Depends(get_session)):

    # Only check Licenses table, not LicensePost
    if license_input.planname.upper() == "TRIAL":
        plan_count = session.exec(
            select(func.count())
            .select_from(Licenses)  # <-- ORM table, not Pydantic model
            .where(
                and_(
                    Licenses.companyid == license_input.companyid,
                    Licenses.planname == "TRIAL"
                )
            )
        ).one()
        if plan_count >= 1:
            raise HTTPException(status_code=400, detail="Trial plan can be assigned only once.")
        
        license_key = generate_license_key()

    # Set start and end dates
    start_date = date.today()
    if license_input.planname.upper() == "TRIAL":
        end_date = start_date + timedelta(days=7)
    elif (license_input.planname.upper() == "PRO" or license_input.planname.upper() == "ENTERPRISES") and license_input.planperiod.upper() == "MONTHLY" :
        end_date = start_date + timedelta(days=30)
    elif (license_input.planname.upper() == "PRO" or license_input.planname.upper() == "ENTERPRISES") and license_input.planperiod.upper() == "YEARLY" :
        end_date = start_date + timedelta(days=365)
    else:
        raise HTTPException(status_code=400, detail="Invalid plan name")

    # Create ORM object
    db_license = Licenses(
        companyid=license_input.companyid,
        companyno=license_input.companyno,
        planname=license_input.planname.upper(),
        planperiod=license_input.planperiod,
        liecensekey=license_key,
        startdate=start_date,
        enddate=end_date,
        userlimit=license_input.userlimit,
        active=license_input.active,
        createdby=license_input.createdby,
        modifiedby=license_input.modifiedby
    )

    session.add(db_license)
    session.commit()
    session.refresh(db_license)
    return db_license
