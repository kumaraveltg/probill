from fastapi import  FastAPI, APIRouter, HTTPException, Depends,Query
from sqlmodel import Session, select, SQLModel, Field ,delete ,func ,Table,MetaData,and_ 
from .db import engine, get_session
#from sqlalchemy.orm import aliassed
from pydantic import  validator, BaseModel ,EmailStr 
from typing import List, Optional
from routes.commonflds import CommonFields  
from datetime import datetime,date  
from routes.company import Company  
from routes.city import City
from routes.state import State
from routes.country import Country
from routes.currecny import Currency
from routes.userauth import get_current_user

router = APIRouter( tags=["Customer"])

class CustomerHeader(CommonFields, table=True):
    __tablename__ = "customer"
    __table_args__ = {"extend_existing": True} 
    companyid: int = Field(foreign_key="company.id", nullable=False)
    companyno: str 
    customer_type:str 
    customername: str = Field(index=True, nullable=False) 
    contactperson: str = Field(default="", nullable=False)
    currencyid:int = Field(foreign_key="currenc.id",nullable=False)
    customer_phone: str = Field(default="", nullable=False)
    customer_mobile: Optional[str] = None
    customer_email: Optional[str] = None
    customer_website: Optional[str]= None   
    address1: str = Field(default="", nullable=False)
    address2: Optional[str] = None
    cityid: int = Field(foreign_key="city.id", nullable=False)
    stateid: int = Field(foreign_key="state.id", nullable=False)
    countryid: int = Field(foreign_key="country.id", nullable=False)
    pincode: str = Field(default="", nullable=False)
    shipping_address1: str = Field(default="", nullable=False)
    shipping_address2: Optional[str] = None
    shipping_cityid: int = Field(foreign_key="city.id", nullable=False)
    shipping_stateid: int = Field(foreign_key="state.id", nullable=False)
    shipping_countryid: int = Field(foreign_key="country.id", nullable=False)
    shipping_pincode: str = Field(default="", nullable=False)    
    gsttype: str = Field(default="B2C",nullable=False)
    gstin: Optional[str] = None 
    placeof_supply: str
    active: bool = True  # default value
    sameas:bool = False
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }
    # contacts: List["CustomerContacts"] = Relationship(back_populates="customer")

class CustomerContacts(SQLModel, table=True):
    __tablename__ = "customer_contacts"
    __table_args__ = {"extend_existing": True} 
    id: int | None = Field(default=None, primary_key=True)
    customerid: int = Field(foreign_key="customer.id", nullable=False)
    rowno: int = Field(default=1, nullable=False)
    contact_type : str
    contact_person: str
    contact_mobile: str
    contact_phone: str
    contact_email: Optional[EmailStr]= None
    
   # customer: Optional[CustomerHeader] = Relationship(back_populates="contacts")


#customer View from DbView customer,Contacts

class CustomerViewHeader(SQLModel,table=True):
    __tablename__ = "vw_customer"
    id: int | None = Field(default=None, primary_key=True)
    createdby:str
    modifiedby: str
    createdon: datetime
    modifiedon: datetime
    companyid: int  
    companyno: str 
    customer_type:str 
    customername: str = Field(index=True, nullable=False) 
    contactperson: str = Field(default="", nullable=False)
    currencyid:int = Field(foreign_key="currenc.id",nullable=False)
    customer_phone: str = Field(default="", nullable=False)
    customer_mobile: Optional[str] = None
    customer_email: Optional[str] = None
    customer_website: Optional[str]= None   
    address1: str = Field(default="", nullable=False)
    address2: Optional[str] = None
    cityid: int
    stateid: int
    countryid: int
    cityname: str
    statename: str
    countryname: str
    pincode: str = Field(default="", nullable=False)
    shipping_address1: str = Field(default="", nullable=False)
    shipping_address2: Optional[str] = None
    shipping_cityid: int  
    shipping_cityname:str
    shipping_stateid: int  
    shipping_statename: str
    shipping_countryid: int 
    shipping_countryname: str 
    shipping_pincode: str = Field(default="", nullable=False)    
    gsttype: str = Field(default="B2C",nullable=False)
    gstin: Optional[str] = None 
    placeof_supply: str
    active: bool = True  # default value
    sameas:bool = False
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }


class PostCust_Contact(BaseModel):
    id: int  
    customerid: int  
    rowno: int  
    contact_type : str
    contact_person: str
    contact_mobile: str
    contact_phone: str
    contact_email: Optional[EmailStr]= None 


class Postcustomer(BaseModel):
    companyid: int  
    companyno: str 
    customer_type:str 
    customername: str  
    contactperson: Optional[str] = None 
    currencyid: int
    customer_phone:Optional[str] = None 
    customer_mobile: Optional[str] = None
    customer_email: Optional[str] = None
    customer_website: Optional[str]= None   
    address1: str = Field(default="", nullable=False)
    address2: Optional[str] = None
    cityid: int  
    stateid: int  
    countryid: int  
    pincode: str  
    shipping_address1: str  
    shipping_address2: Optional[str] = None
    shipping_cityid: int 
    shipping_stateid: int  
    shipping_countryid: int 
    shipping_pincode: str     
    gsttype: str  
    gstin: Optional[str] = None 
    placeof_supply: Optional[str] = None 
    active: bool = True  # default value
    sameas:bool = False
    createdby:str
    modifiedby: str
    contacts: List[PostCust_Contact] = []

class UpdateContact(BaseModel):
    id: Optional[int] = None       # existing contact id (for updates)
    contact_type: Optional[str] = None
    contact_person: Optional[str] = None
    contact_mobile: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None

class UpdateCustomer(BaseModel): 
    companyid: int  
    companyno: str 
    customer_type:str 
    customername: str  
    contactperson: Optional[str] = None 
    currencyid: int
    customer_phone:Optional[str] = None 
    customer_mobile: Optional[str] = None
    customer_email: Optional[str] = None
    customer_website: Optional[str]= None   
    address1: str = Field(default="", nullable=False)
    address2: Optional[str] = None
    cityid: int  
    stateid: int  
    countryid: int  
    pincode: str  
    shipping_address1: str  
    shipping_address2: Optional[str] = None
    shipping_cityid: int 
    shipping_stateid: int  
    shipping_countryid: int 
    shipping_pincode: str     
    gsttype: str  
    gstin: Optional[str] = None 
    placeof_supply: Optional[str] = None 
    active: bool = True  # default value 
    sameas:bool = False
    modifiedby: str
    contacts: Optional[List[UpdateContact]] = []
 

class CustomerSearch(BaseModel):
    id: int  
    createdby:str
    modifiedby: str
    createdon: datetime
    modifiedon: datetime
    companyid: int  
    companyno: str 
    customer_type:str 
    customername: str = Field(index=True, nullable=False) 
    contactperson: str = Field(default="", nullable=False)
    currencyid:int = Field(foreign_key="currenc.id",nullable=False)
    customer_phone: str = Field(default="", nullable=False)
    customer_mobile: Optional[str] = None
    customer_email: Optional[str] = None
    customer_website: Optional[str]= None   
    address1: str = Field(default="", nullable=False)
    address2: Optional[str] = None
    cityid: int
    stateid: int
    countryid: int
    cityname: str
    statename: str
    countryname: str
    pincode: str = Field(default="", nullable=False)
    shipping_address1: str = Field(default="", nullable=False)
    shipping_address2: Optional[str] = None
    shipping_cityid: int  
    shipping_cityname:str
    shipping_stateid: int  
    shipping_statename: str
    shipping_countryid: int 
    shipping_countryname: str 
    shipping_pincode: str = Field(default="", nullable=False)    
    gsttype: str = Field(default="B2C",nullable=False)
    gstin: Optional[str] = None 
    placeof_supply: str
    active: bool = True  # default value
    sameas:bool = False

class CustomerResponse(BaseModel):
    total :int
    customer_list:List[CustomerViewHeader] 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }
class CustomerContactsResponse(BaseModel):
    custhdr: CustomerViewHeader
    custdtl: List[CustomerContacts]
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

@router.post("/addcustomer", response_model=Postcustomer)
def create_customer(payload: Postcustomer, session: Session = Depends(get_session)):
    try:
        with session:
            exists = session.exec(
                select(CustomerHeader.customername)
                .join(Company, Company.id == CustomerHeader.companyid)
                .where(
                    CustomerHeader.customername == payload.customername,
                    Company.companyno == payload.companyno
                )
            ).first()

            if exists:
                raise HTTPException(status_code=400, detail="Customer name already exists.")

            db_customer = CustomerHeader.from_orm(payload)
            session.add(db_customer)
            session.flush()

            if getattr(payload, "contacts", None):
                for contact in payload.contacts:
                    contact_data = PostCust_Contact.from_orm(contact)
                    contact_data.customerid = db_customer.id
                    session.add(contact_data)

            session.commit()
            session.refresh(db_customer)

        return db_customer
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving customer: {str(e)}")

@router.post("/updatecustomer/{customerid}",response_model=UpdateCustomer)
def update_customer(customerid: int , upd:UpdateCustomer, session: Session = Depends(get_session),
                    # cu:dict = Depends(get_current_user),
                    ):
    db_customer = session.get(CustomerHeader,customerid) 

    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    for key, value in upd.model_dump().items():
        setattr(db_customer, key, value)
    session.add(db_customer)
    session.commit()
    session.refresh(db_customer)
    if upd.contacts:
        for contact in upd.contacts:
            if contact.id:  # existing contact → update
                db_contact = session.get(CustomerContacts, contact.id)
                if db_contact:
                    for key, value in contact.model_dump(exclude_unset=True).items():
                        setattr(db_contact, key, value)
                    session.add(db_contact)
                else:
                    # contact.id given but not found → create new
                    new_contact = CustomerContacts(customerid=customerid, **contact.model_dump())
                    session.add(new_contact)
            else:  # new contact → insert
                new_contact = CustomerContacts(customerid=customerid, **contact.model_dump())
                session.add(new_contact)

        session.commit()

    return upd

@router.get("/customer/search/{companyid}", response_model=List[CustomerSearch])
def customer_search(
    companyid: int,
    field: str = Query(...),
    value: str = Query(...),
    db: Session = Depends(get_session),
):
    c = CustomerViewHeader
    comp = Company

    # ✅ Base query with join
    query = (
        db.query(c, comp.companyname.label("companyname"), comp.companyno.label("companyno"))
        .join(comp, c.companyid == comp.id, isouter=True)
        .filter(comp.id == companyid)
    )

    # ✅ Dynamic filter based on field
    field_map = {
        "customername": c.customername,
        "gstin": c.gstin,
        "companyname": comp.companyname,
    }

    if field not in field_map:
        raise HTTPException(status_code=400, detail="Invalid search field")

    query = query.filter(field_map[field].ilike(f"%{value}%"))

    # ✅ Execute query
    results = query.all()

    # ✅ Convert to list of dicts automatically
    response_data = []
    for r, companyname, companyno in results:
    # r is SQLModel object
     record = r.model_dump()  # ✅ convert to plain dict
     record["companyname"] = companyname
     record["companyno"] = companyno
     response_data.append(CustomerSearch(**record))  # ✅ Pydantic model instance

    return response_data



@router.get("/getcustomer/{companyid}", response_model=CustomerResponse)
def read_customer(
    companyid: int,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    # current_user: dict = Depends(get_current_user)
):
    c = CustomerViewHeader

    # Fetch paginated customers
    customer_header = session.exec(
        select(c)
        .where(and_(c.active == True, c.companyid == companyid))
        .order_by(c.customername)
        .offset(skip)
        .limit(limit)
    ).all()

    if not customer_header:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Total count
    totalcount = session.exec(
        select(func.count(c.id)).where(c.companyid == companyid)
    ).first() or 0

    # Response
    return CustomerResponse(
        total=totalcount,
        customer_list=customer_header
    )

@router.get("/getcustcontacts/{customerid}",response_model=CustomerContactsResponse)
def get_contacts(customerid: int, session: Session = Depends(get_session),
                  current_user: dict = Depends(get_current_user)
                 ):
    cust_header = session.get(CustomerViewHeader, customerid)
    if not cust_header:
        raise HTTPException(status_code=404, detail="Customer header not found")

    statement = select(CustomerContacts).where(CustomerContacts.customerid == customerid) 
    results = session.exec(statement)
    cust_details = results.all() 

    return CustomerContactsResponse(custhdr=cust_header, custdtl=cust_details)

@router.delete("/custdelete/{customerid}", response_model=dict)
def delete_taxmaster(customerid: int, session: Session = Depends(get_session)):    
    db_tax = session.get(CustomerHeader, customerid)
    if not db_tax:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Delete associated tax details first
    session.exec(delete(CustomerContacts).where(CustomerContacts.customerid == customerid))
    session.commit()

    # Delete the tax header
    session.delete(db_tax)
    session.commit()

    return {"detail": "Customer deleted successfully"}

