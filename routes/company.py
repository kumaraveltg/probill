from fastapi import APIRouter,  HTTPException,Depends,Query 
from sqlmodel import Session, select,SQLModel,Field,func,and_
from .db import engine, get_session
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER,JSON
from pydantic import EmailStr,validator,BaseModel
from typing import List, Optional 
from datetime import datetime  
 

#router = APIRouter()
router = APIRouter(prefix="/company", tags=["Company"])

#Model

class Company(SQLModel, table=True):
    __tablename__ = "company"
    __table_args__ = {"extend_existing": True} 
    id: int | None = Field(default=None, primary_key=True)
    cancel: str ="F"
    createdby: str = Field(nullable=False)
    createdon: datetime = Field(default_factory=datetime.now) 
    modifiedby: str= Field(nullable=False)
    modifiedon:  datetime = Field(default_factory=datetime.now,sa_column_kwargs={"onupdate":datetime.now}) 
    companyname: str = Field(index=True,nullable=False)
    companycode: str = Field(index=True,nullable=False)
    adress: Optional[str]=None
    phone: Optional[str]=None
    emailid: Optional[EmailStr]= None
    contactperson: Optional[str]=None
    gstno: Optional[str]=None  
    currency:int = Field(default=0, nullable=False)
    active: bool = True  # default value
    
    
#schema/ pydantic
class Pcompany(BaseModel):
    createdby: Optional[datetime]= None
    modifiedby: Optional[datetime]= None
    companyname: str = Field(nullable=False)
    companycode: str = Field(nullable=False)
    adress: Optional[str]=None
    phone: Optional[str]=None
    emailid: Optional[EmailStr]= None
    contactperson: Optional[str]=None
    gstno: Optional[str]=None  
    currency:int = Field(default=0, nullable=False)
    createdby: str = Field(nullable=False)
    modifiedby: str = Field(nullable=False)
    active: bool = True 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class CompanyUpdate(BaseModel):
    companyname: Optional[str] = None
    companycode: Optional[str] = None
    adress: Optional[str]=None
    phone: Optional[str]=None
    emailid: Optional[EmailStr]= None
    contactperson: Optional[str]=None
    gstno: Optional[str]=None  
    currency: Optional[int] = None
    modifiedby: str = Field(nullable=False)
    active: Optional[bool] = None 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }
    @validator( "modifiedby","companyname","companycode" )
    def must_not_be_empty(cls, v):
     if not v or not v.strip():
        raise ValueError("This field is required")
     return v

class CompanyRead(BaseModel):
    id: int
    cancel: str
    createdby: str
    createdon: datetime
    modifiedby: str
    modifiedon: datetime
    companyname: str
    companycode: str
    adress: Optional[str]
    phone: Optional[str]
    emailid: Optional[EmailStr]
    contactperson: Optional[str]
    gstno: Optional[str]  
    currency:Optional[int]
    currencycode: Optional[str] = None
    active: bool 
    model_config = {
        "from_attributes": True,        
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class CompanySearch(BaseModel):
    id: int
    companyname: str
    companycode: str
    adress: Optional[str]
    phone: Optional[str]
    emailid: Optional[EmailStr]
    contactperson: Optional[str]
    gstno: Optional[str]  
    currency:Optional[int]
    currencycode: Optional[str] = None
    active: bool  

class CompanyResponse(BaseModel):
    company_list: list[CompanyRead]
    total: int = Field(default =0)

# ✅ Create company
@router.post("/createcompany",response_model=Pcompany) 
def create_company(company: Pcompany, session: Session = Depends(get_session)):
   
   # Check if company with the same name already exists
   # model = Company , schema is assigned to company you have to check in model
   existing_companyname = session.exec(
            select(Company).where(Company.companyname == company.companyname)
        ).first()

   if existing_companyname:
            raise HTTPException(status_code=400, detail="Company Name already exists")
   existing_companycode = session.exec(
            select(Company).where(Company.companycode == company.companycode)
        ).first()

   if existing_companycode:
            raise HTTPException(status_code=400, detail="Company Code already exists")
   
   
   db_company = Company.from_orm(company)
   session.add(db_company)
   session.commit()
   session.refresh(db_company)
   return Pcompany.from_orm(db_company)

@router.post("/Updatecompany/{company_id}",response_model=Pcompany)
def update_company(company_id: int, company_update: CompanyUpdate, session: Session = Depends(get_session)):
    db_company = session.get(Company, company_id)
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    # Update fields
    for key, value in company_update.model_dump(exclude_unset=True).items():
        setattr(db_company, key, value)
    
    session.add(db_company)
    session.commit()
    session.refresh(db_company)
    return Pcompany.from_orm(db_company)

@router.get("/company/search",response_model=List[CompanySearch])
def company_search( 
    field: str = Query(...),
    value: str = Query(...),
    db: Session = Depends(get_session)
):
     from routes.company import Company  # import here, not at the top
     from routes.currecny import Currency

     query = db.query(
        Company.id,
        Company.companycode,
        Company.companyname,
        Company.adress,
        Company.emailid,
        Company.gstno,
        Company.phone,
        Company.contactperson,
        Company.active,
        Company.currency,
        Currency.currencycode
    ).join(Currency, Company.currency == Currency.id)
# Apply filters
     if field == "companycode":
        query = query.filter(Company.companycode.ilike(f"%{value}%"))
     elif field == "companyname":
        query = query.filter(Company.companyname.ilike(f"%{value}%"))
     elif field == "active":
         active_value = value.lower() in ["yes", "true", "1"]
         query = query.filter(Company.active == active_value)
     elif field == "currencycode":
        query = query.filter(Currency.currencycode.ilike(f"%{value}%"))

     results = query.all()

    # Each row is a tuple → map to dict
     return [
        {
            "id": r.id,
            "companycode": r.companycode,
            "companyname": r.companyname,
            "adress": r.adress,
            "phone": r.phone,
            "emailid": r.emailid,
            "contactperson": r.contactperson,
            "gstno": r.gstno,
            "active": r.active,  
            "currency": r.currency,
            "currencycode": r.currencycode,
        }
        for r in results
    ]

@router.get("/getcompany/", response_model=CompanyResponse)
def get_company(
    session: Session = Depends(get_session),
    skip: int = Query(0, ge=0),   # default = 0, must be >= 0
    limit: int = Query(10, ge=1), # default = 10, must be >= 1
):
    # local import avoids circular import
    
    from routes.currecny import Currency
    from routes.company import Company 

    # base query
    statement = (
        select(Company, Currency.currencycode)
        .join(Currency, Company.currency == Currency.id, isouter=True)
        .offset(skip)
        .limit(limit)
    )
    result = session.exec(statement).all()

    if not result:
        raise HTTPException(status_code=404, detail="Company not found")

    # total count of all companies (without pagination)
    totalcount = session.exec(select(func.count()).select_from(Company)).one()

    company_list = []
    for company, currency_code in result:
        company_list.append(
            CompanyRead(
                id=company.id,
                cancel=company.cancel,
                createdby=company.createdby,
                createdon=company.createdon,
                modifiedby=company.modifiedby,
                modifiedon=company.modifiedon,
                companyname=company.companyname,
                companycode=company.companycode,
                adress=company.adress,
                phone=company.phone,
                emailid=company.emailid,
                contactperson=company.contactperson,
                gstno=company.gstno,
                currency=company.currency,
                currency_code=currency_code or "N/A",
                active=company.active,
            )
        )

    return {"company_list": company_list, "total": totalcount}



@router.get("/companylist/{companyid}",response_model=List[CompanyRead])
def company_list(companyid: int,session: Session=Depends(get_session)):
    from routes.company import Company
    from routes.currecny import Currency
    
    statement = select(Company, Currency.currencycode).join(Currency, Company.currency == Currency.id, isouter=True).where(and_(Company.active == True,Company.id==companyid)).order_by(Company.id.desc())
    results = session.exec(statement)
    company_list = [
        CompanyRead(
            id=company.id,
            cancel=company.cancel,
            createdby=company.createdby,    
            createdon=company.createdon,
            modifiedby=company.modifiedby,
            modifiedon=company.modifiedon,
            companyname=company.companyname,              
            companycode=company.companycode,
            adress=company.adress,
            phone=company.phone,
            emailid=company.emailid,
            contactperson=company.contactperson,
            gstno=company.gstno,
            currency=company.currency,
            currencycode=currency_code or "N/A",
            active=company.active
        )
        for company, currency_code in results
    ]
    return company_list


@router.delete("/deletecompany/{company_id}")
def delete_company(company_id: int, session: Session = Depends(get_session)):
    db_company = session.get(Company, company_id)
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    session.delete(db_company)
    session.commit()
    return {"detail": "Company deleted successfully"}