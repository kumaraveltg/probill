from fastapi import  FastAPI, APIRouter, HTTPException, Depends
from sqlmodel import Session, select, SQLModel, Field ,delete   
from .db import engine, get_session
from pydantic import  validator, BaseModel  
from typing import List, Optional
from routes.commonflds import CommonFields  
from datetime import datetime,date  
from routes.company import Company  

router = APIRouter( tags=["Customer"])

class CustomerHeader(CommonFields, table=True):
    __tablename__ = "customer"
    __table_args__ = {"extend_existing": True} 
    companyid: int = Field(foreign_key="company.id", nullable=False)
    customercode: str = Field(index=True, nullable=False)
    customername: str = Field(index=True, nullable=False)    
    address1: str = Field(default="", nullable=False)
    address2: Optional[str] = None
    city: str = Field(default="", nullable=False)
    state: str = Field(default="", nullable=False)
    country: str = Field(default="", nullable=False)
    pincode: str = Field(default="", nullable=False)
    contactperson: str = Field(default="", nullable=False)
    phone1: str = Field(default="", nullable=False)
    phone2: Optional[str] = None
    email: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    active: bool = True  # default value