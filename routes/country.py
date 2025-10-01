from fastapi import APIRouter, HTTPException, Depends,Query
from sqlmodel import Session, select, SQLModel, Field, delete ,func
from .db import engine, get_session
from pydantic import  validator, BaseModel
from typing import List, Optional
from routes.commonflds import CommonFields  
from datetime import datetime  
from routes.userauth import get_current_user

router = APIRouter( tags=["Country"])

class Country(CommonFields, table=True):
    __tablename__ = "country"
    __table_args__ = {"extend_existing": True} 
    countrycode: str = Field(index=True, nullable=False)
    countryname: str = Field(index=True, nullable=False)
    active: bool = True  # default value    

class PCountry(BaseModel):
    createdby: str = Field(nullable=False)
    modifiedby: str = Field(nullable=False)
    countrycode: str = Field(nullable=False)
    countryname: str = Field(nullable=False)    
    active: bool = True 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class CountryUpdate(BaseModel):
    modifiedby: str = Field(nullable=False)
    countrycode: str = Field(nullable=False)
    countryname: str = Field(nullable=False)    
    active: bool = True 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class CountryRead(BaseModel):
    id: int
    countrycode: str
    countryname: str
    active: bool 
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
class CountrySearch(BaseModel):
    countrycode: str
    countryname: str
    active: Optional[bool] = None

    class Config:
        orm_mode = True

@router.post("/country/", response_model=CountryRead)
def create_country(country: PCountry, session: Session= Depends(get_session)):
    db_country = session.exec(select(Country).where(func.upper(Country.countrycode) == country.countrycode.upper())).first()
    if db_country:
        raise HTTPException(status_code=400, detail="Country code already exists")
    db_country = session.exec(select(Country).where(func.upper(Country.countryname) == country.countryname.upper())).first()
    if db_country:
        raise HTTPException(status_code=400, detail="Country name already exists")  
    
    db_country = Country.from_orm(country)
    session.add(db_country)
    session.commit()
    session.refresh(db_country)
    return db_country

@router.post("/countryupdate/{id}", response_model=CountryUpdate)
def update_country(id :int, country: CountryUpdate, session: Session= Depends(get_session)):
    db_country = session.exec(select(Country).where(Country.id == id)).first()
    if not db_country:
        raise HTTPException(status_code=404, detail="Country code not found")
    db_country_name = session.exec(select(Country).where(Country.countryname == country.countryname, Country.id != db_country.id)).first()
    if db_country_name:
        raise HTTPException(status_code=400, detail="Country name already exists")  
    
    db_country.modifiedby = country.modifiedby
    db_country.countrycode = country.countrycode
    db_country.countryname = country.countryname
    db_country.active = country.active
    session.add(db_country)
    session.commit()
    session.refresh(db_country)
    return db_country

@router.get("/country/", response_model=List[CountryRead])
def read_countries(skip: int = 0, limit: int = 10, session: Session = Depends(get_session),
                   current_user: dict = Depends(get_current_user)):
    countries = session.exec(select(Country).offset(skip).limit(limit)).all()
    return countries

@router.get("/country/search", response_model=List[CountrySearch])
def search_country(field: str = Query(...), value: str = Query(...), db: Session = Depends(get_session)):
    query = db.query(Country)

    if field == "countrycode":
        query = query.filter(Country.countrycode.ilike(f"%{value}%"))
    elif field == "countryname":
        query = query.filter(Country.countryname.ilike(f"%{value}%"))
    elif field == "active":
        active_value = value.lower() in ["yes", "true", "1"]
        query = query.filter(Country.active == active_value)
    
    results = query.all()
    return [
        {
            "countrycode": c.countrycode,
            "countryname": c.countryname,
            "active": c.active
        } 
        for c in results
    ]

@router.get("/country/{country_id}", response_model=CountryRead)
def read_country(country_id: int, session: Session = Depends(get_session)):
    country = session.get(Country, country_id)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country
@router.delete("/country/{country_id}")
def delete_country(country_id: int, session: Session = Depends(get_session)):    
    country = session.get(Country, country_id)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    statement = delete(Country).where(Country.id == country_id)
    session.exec(statement)
    session.commit()
    return {"ok": True, "message": "Country deleted successfully"}

