from fastapi import APIRouter,  HTTPException,Depends
from sqlmodel import Session, select,SQLModel,Field,Column,create_engine
from .db import engine, get_session
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER,JSON 
from pydantic import EmailStr,validator,BaseModel
from typing import List, Optional,Dict, Any 
from datetime import datetime   
from routes.company import Company
from routes.commonflds import CommonFields 

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

@router.get("/getcurrency", response_model=List[Pcurrency])
def get_currency(session: Session = Depends(get_session)):
    currencies = session.exec(select(Currency)).all()
    return currencies

@router.get("/getcurrencybyid/{currency_id}", response_model=Pcurrency)
def get_currency_by_id(currency_id: int, session: Session = Depends(get_session)):
    db_currency = session.get(Currency, currency_id)
    if not db_currency:
        raise HTTPException(status_code=404, detail="Currency not found.")
    return db_currency

@router.delete("/deletecurrency/{currency_id}")
def delete_currency(currency_id: int, session: Session = Depends(get_session)):
    db_currency = session.get(Currency, currency_id)
    if not db_currency:
        raise HTTPException(status_code=404, detail="Currency not found.")
    session.delete(db_currency)
    session.commit()
    return {"detail": "Currency deleted successfully."}