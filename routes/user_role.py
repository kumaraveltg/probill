from fastapi import APIRouter,  HTTPException,Depends
from sqlmodel import Session, select,SQLModel,Field,Column,create_engine
from .db import engine, get_session
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER,JSON
from pydantic import EmailStr,validator,BaseModel
from typing import List, Optional,Dict, Any
from datetime import datetime 
router = APIRouter()

 
# Model

class User_Role(SQLModel, table=True):
    __table_args__ = {"extend_existing": True} 
    id: int | None = Field(default=None, primary_key=True)
    cancel: str ="F"
    createdby: str = Field(nullable=False)
    createdon: datetime = Field(default_factory=datetime.now) 
    modifiedby: str= Field(nullable=False)
    modifiedon:  datetime = Field(default_factory=datetime.now,sa_column_kwargs={"onupdate":datetime.now}) 
    rolename: str = Field(index=True,nullable=False)
    active: bool = True  # default value
    permissions: list[dict] = Field(
        sa_column=Column(JSON), default=[]
    )
    companyid: int = Field(default=1, nullable=False)
 