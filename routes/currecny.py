from fastapi import APIRouter,  HTTPException,Depends,Query
from sqlmodel import Session, select,SQLModel,Field,Column,create_engine,func
from .db import engine, get_session
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER,JSON  
from pydantic import EmailStr,validator,BaseModel
from typing import List, Optional,Dict, Any 
from datetime import datetime   
from routes.company import Company
from routes.commonflds import CommonFields
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/currency", tags=["Currency"])    

# Model
class Currency(CommonFields, table=True):
    __table_args__ = {"extend_existing": True} 
    currencyname: str = Field(index=True,nullable=False)
    currencycode: str = Field(index=True,nullable=False)
    symbol: Optional[str]=None
    active: bool = True  # default value


#schema/ pydantic
class Pcurrency(BaseModel):  
    createdby: str = Field(nullable=False)
    modifiedby: str = Field(nullable=False)
    currencyname: str = Field(nullable=False)
    currencycode: str = Field(nullable=False)
    symbol: Optional[str]=None 
    active: bool = True
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }
    
class UpdateCurrency(BaseModel):
    modifiedby: Optional[str]= None
    currencyname: Optional[str] = None
    currencycode: Optional[str] = None
    symbol: Optional[str]=None 
    active: Optional[bool] = None

class CurrencyRead(BaseModel):
    id: int
    createdby: str  
    modifiedby: str  
    currencyname: str 
    currencycode: str 
    symbol: Optional[str]=None 
    active: bool = True
    createdby: str
    createdon: datetime
    modifiedby: str
    modifiedon: datetime 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class CurrencySearch(BaseModel):
    id: int
    currencycode: str
    currencyname: str
    active: bool

class CurrencyResponse(BaseModel):
 currency_list: List[CurrencyRead]
 total: int = Field(default=0)

 
     

@router.post("/addcurrency", response_model=Pcurrency)
def add_currency(currency: Pcurrency, session: Session = Depends(get_session)):
    if not currency.currencyname or not currency.currencycode:
        raise HTTPException(status_code=400, detail="Currency name and code are required.") 
    if session.exec(select(Currency).where(Currency.currencyname == currency.currencyname)).first():
        raise HTTPException(status_code=400, detail="Currency name already exists.")
    if session.exec(select(Currency).where(Currency.currencycode == currency.currencycode)).first():
        raise HTTPException(status_code=400, detail="Currency code already exists.")    
    
    db_currency = Currency.from_orm(currency)
    session.add(db_currency)
    session.commit()
    session.refresh(db_currency)
    return db_currency

@router.post("/updatecurrency/{currency_id}", response_model=UpdateCurrency)
def update_currency(currency_id: int, currency: UpdateCurrency, session: Session = Depends(get_session)):
    db_currency = session.get(Currency, currency_id)
    if not db_currency:
        raise HTTPException(status_code=404, detail="Currency not found.")
    
    currency_data = currency.model_dump(exclude_unset=True)
    for key, value in currency_data.items():
        setattr(db_currency, key, value)
    
    session.add(db_currency)
    session.commit()
    session.refresh(db_currency)
    return db_currency

@router.get("/search",response_model=List[CurrencySearch])
def currency_search( 
    field: str = Query(...),
    value: str = Query(...),
    db: Session = Depends(get_session)
):
     from routes.currecny import Currency 
     query = db.query(
        Currency.id,
        Currency.currencycode,
        Currency.currencyname,         
        Currency.active,         
    ) 
# Apply filters
     if field == "currencycode":
        query = query.filter(Currency.currencycode.ilike(f"%{value}%"))
     elif field == "currencyname":
        query = query.filter(Currency.currencyname.ilike(f"%{value}%"))
     elif field == "active":
         active_value = value.lower() in ["yes", "true", "1"]
         query = query.filter(Currency.active == active_value)      

     results = query.all()
     # Each row is a tuple → map to dict
     return [
        {
            "id": r.id,            
            "currencycode": r.currencycode,
            "currencyname": r.currencyname,
            "active" : r.active
        }
        for r in results
    ]

@router.get("/getcurrency/", response_model=CurrencyResponse)
def get_currency( skip: int = 0, limit: int = 10,session: Session = Depends(get_session)):
    currencies = session.exec(select(Currency).order_by(Currency.currencycode).offset(skip).limit(limit)).all()
    totalcount = session.exec(select(func.count()).select_from(Currency)).one()
    currency_list=[]

    for currency in currencies:
     currency_list.append(
      CurrencyRead(
        id= currency.id, 
        currencyname=currency.currencyname,
        currencycode = currency.currencycode,
        symbol =currency.symbol,
        active =  currency.active,
        createdby= currency.createdby,
        createdon = currency.createdon,
        modifiedby= currency.modifiedby,
        modifiedon= currency.modifiedon ,
            )
    )
    return {"currency_list":currency_list,"total":totalcount}

@router.get("/getcurrencybyid/{currency_id}", response_model=Pcurrency)
def get_currency_by_id(currency_id: int, session: Session = Depends(get_session)):
    db_currency = session.get(Currency, currency_id)
    if not db_currency:
        raise HTTPException(status_code=404, detail="Currency not found.")
    return db_currency

@router.delete("/deletecurrency/{currency_id}")
def delete_currency(currency_id: int, session: Session = Depends(get_session)):
   try:
    db_currency = session.get(Currency, currency_id)
    if not db_currency:
        raise HTTPException(status_code=404, detail="Currency not found.")
    session.delete(db_currency)
    session.commit()
    return {"detail": "Currency deleted successfully."}
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