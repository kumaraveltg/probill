from sqlmodel import SQLModel,Field  
from datetime import datetime  
from typing import Optional


class CommonFields(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    cancel: str ="F"
    sourceid: int = Field(default=0, nullable=False)
    createdby: str = Field(nullable=False)
    createdon: datetime = Field(default_factory=datetime.now)  
    modifiedby: str= Field(nullable=False)
    modifiedon:  datetime = Field(default_factory=datetime.now,sa_column_kwargs={"onupdate":datetime.now})  
    app_desc: Optional[int]= Field(default=1, nullable=False)
    app_level: Optional[int]= Field(default=0, nullable=False)
    app_owner: Optional[str]=None
    