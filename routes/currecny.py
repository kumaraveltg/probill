from fastapi import APIRouter,  HTTPException,Depends
from sqlmodel import Session, select,SQLModel,Field,Column,create_engine
from .db import engine, get_session
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER,JSON 
from pydantic import EmailStr,validator,BaseModel
from typing import List, Optional,Dict, Any 
from datetime import datetime   
from routes.company import Company
router = APIRouter()    

# Model
class Currency(SQLModel, table=True):
    __table_args__ = {"extend_existing": True} 
    id: int | None = Field(default=None, primary_key=True)
    cancel: str ="F"
    currencyname: str = Field(index=True,nullable=False)
    currencycode: str = Field(index=True,nullable=False)
    symbol: Optional[str]=None
    createdby: str = Field(nullable=False)
    createdon: datetime = Field(default_factory=datetime.now)  
    modifiedby: str= Field(nullable=False)
    modifiedon:  datetime = Field(default_factory=datetime.now,sa_column_kwargs={"onupdate":datetime.now})  
    active: bool = True  # default value


#schema/ pydantic
class Pcurrency(BaseModel): 
    currencyname: str = Field(nullable=False)
    currencycode: str = Field(nullable=False)
    symbol: Optional[str]=None
    createdby: str = Field(nullable=False)
    modifiedby: str = Field(nullable=False)
    active: bool = True 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }
