from fastapi import APIRouter, HTTPException, Depends,Query
from sqlmodel import Session, select, SQLModel, Field ,delete,func,and_,update
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
from sqlalchemy.exc import IntegrityError 


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
    licensekey:Optional[str]=None
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
    startdate: Optional[date] = None
    enddate: Optional[date] = None
    sourceid:Optional[int]= None
    active : bool = Field(default=True,nullable=True)
    createdby: str
    modifiedby: str

class LicenseUpdate(BaseModel):
    id:int
    companyid: int = Field(foreign_key="company.id", nullable=False)
    companyno: Optional[str]=None 
    planname: Optional[str]=None  
    planperiod:str
    startdate: date = Field(nullable=False)
    enddate : date  = Field(nullable=False)  
    userlimit: int=Field(default=0,nullable=True)
    licensekey:Optional[str]=None
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
    companyname: Optional[str]=None
    planname: Optional[str]=None 
    planperiod: Optional[str]=None  
    startdate: date = Field(nullable=False)
    enddate : date  = Field(nullable=False)  
    userlimit: int=Field(default=0,nullable=True)
    licensekey:Optional[str]=None
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
def create_license(
    license_input: LicensePost,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):

    # ✅ 1. Trial plan validation
    if license_input.planname.upper() == "TRIAL":
        plan_count = session.exec(
            select(func.count())
            .select_from(Licenses)
            .where(
                and_(
                    Licenses.companyid == license_input.companyid,
                    Licenses.planname == "TRIAL"
                )
            )
        ).one()
        if plan_count >= 1:
            raise HTTPException(status_code=400, detail="Trial plan can be assigned only once.")

    # ✅ 2. Renewal validation (only if enddate is provided)
    today = date.today()
    license_enddate = None

    if license_input.enddate:
        # Convert to date if it's a string
        if isinstance(license_input.enddate, str):
            try:
                license_enddate = datetime.strptime(license_input.enddate, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end date format.")
        else:
            license_enddate = license_input.enddate

        # ✅ Only run this logic if end date exists
        if license_enddate:
            five_days_before_end = license_enddate - timedelta(days=5)
            if today < five_days_before_end:
                raise HTTPException(
                    status_code=400,
                    detail="You can renew only within 5 days before expiry."
                )

    # ✅ 3. Generate license key and compute dates
    license_key = generate_license_key()
    start_date = date.today()

    if license_input.planname.upper() == "TRIAL":
        end_date = start_date + timedelta(days=7)
    elif (
        license_input.planname.upper() in ["PRO", "ENTERPRISES"]
        and license_input.planperiod.upper() == "MONTHLY"
    ):
        end_date = start_date + timedelta(days=30)
    elif (
        license_input.planname.upper() in ["PRO", "ENTERPRISES"]
        and license_input.planperiod.upper() == "YEARLY"
    ):
        end_date = start_date + timedelta(days=365)
    else:
        raise HTTPException(status_code=400, detail="Invalid plan name or period.")

    # ✅ 4. Save license
    db_license = Licenses(
        companyid=license_input.companyid,
        companyno=license_input.companyno,
        planname=license_input.planname.upper(),
        planperiod=license_input.planperiod,
        licensekey=license_key,
        startdate=start_date,
        enddate=end_date, 
        active=license_input.active,
        createdby=license_input.createdby,
        modifiedby=license_input.modifiedby,
        sourceid=license_input.sourceid
        
    )

    session.add(db_license)
    session.commit()
    session.refresh(db_license)

    session.exec(  update(Company)
            .where(Company.id == license_input.companyid)
            .values(licensesid=db_license.id)
        )
    session.commit()
    return db_license


@router.post("/licenseupdate/{licenseid}", response_model=LicenseUpdate)
def update_license(licenseid:int,LicenseUPD: LicenseUpdate, session: Session= Depends(get_session),
                  current_user :dict = Depends(get_current_user)
                 ):
    db_license = session.exec(select(LicenseUPD).where(LicenseUPD.id == licenseid)).first()
    if not db_license:
        raise HTTPException(status_code=400, detail="License Not found")
        
    for key, value in LicenseUPD.dict(exclude_unset=True).items():
        setattr(db_license, key, value)
    session.add(db_license)
    session.commit()
    session.refresh(db_license)

    company = session.exec(select(Company).where(Company.id == LicenseUPD.companyid)).first()
    if company:
        company.licensesid = db_license.id
        session.add(company)
        session.commit()
        session.refresh(company)

    return db_license

@router.get("/licenselist/",response_model=LicenseResponse)
def read_license( 
    skip: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session),
):
    # 1️⃣ Query licenses joined with company
    query = (
        select(Licenses, Company.companyname, Company.id, Company.companyno,Company.companyname)
        .join(Company, Licenses.companyid == Company.id, isouter=True)
        .order_by(Licenses.companyno)
        .offset(skip)
        .limit(limit)
    )

    license_rows = session.exec(query).all()

    # 2️⃣ Count total active licenses for company
    totalcount = session.exec(
        select(func.count(Licenses.id)).where(
            and_(Licenses.active == True)
        )
    ).one()

    # 3️⃣ Build result list
    result = []
    for row in license_rows:
        lic = row[0]
        companyname = row[1]
        compid = row[2]
        companyno = row[3]

        result.append({
            "id": lic.id,
            "companyid": compid,
            "companyname": companyname,
            "companyno": companyno,
            "planname": lic.planname,
            "planperiod": lic.planperiod,
            "startdate": lic.startdate,
            "enddate": lic.enddate,
            "active": lic.active, 
            "licensekey":lic.licensekey,
            "userlimit":lic.userlimit,
            "createdby":lic.createdby,
            "createdon":lic.createdon,
            "modifiedby":lic.modifiedby,
            "modifiedon":lic.modifiedon,
        })

    return {"license_list": result, "total": totalcount}

@router.get("/licensevalid/{companyno}")
def validate_license(companyno: str, session: Session = Depends(get_session)):
    today = date.today()

    # 🔹 Query the license for the given companyno
    query = (
        select(
            Licenses,
            Company.companyname
        )
        .join(Company, Licenses.companyno == Company.companyno, isouter=True)
        .where(
            Licenses.companyno == companyno,
            Licenses.active == True
        )
    )

    license_data = session.exec(query).first()

    if not license_data:
        raise HTTPException(status_code=404, detail="No active license found for this company")

    license_obj, companyname = license_data

    # 🔍 Validate date range
    if not (license_obj.startdate <= today <= license_obj.enddate):
        return {
            "companyno": companyno,
            "companyname": companyname,
            "status": "expired",
            "message": "License has expired or not yet active.",
            "startdate": license_obj.startdate,
            "enddate": license_obj.enddate,
        }

    # ✅ License valid
    return {
        "companyno": companyno,
        "companyname": companyname,
        "status": "valid",
        "message": "License is active and valid.",
        "startdate": license_obj.startdate,
        "enddate": license_obj.enddate,
    }

@router.delete("/licensedelete/{licenseid}")
def delete_license(licenseid: int, session: Session = Depends(get_session)):  
    try:   
        LicDel = session.get(Licenses, licenseid)
        if not LicDel:
            raise HTTPException(status_code=404, detail="License not found")
        session.delete(LicDel)
        session.commit()
        return {"ok": True}
    except IntegrityError as e:
        session.rollback()
        # ✅ Detect foreign key violation and return user-friendly message
        if "foreign key constraint" in str(e.orig).lower():
            raise HTTPException(
                status_code=400,
                detail="Cannot delete this Record because it is referenced in other records."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Database error: {str(e.orig)}"
            )
