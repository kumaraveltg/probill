from fastapi import APIRouter, HTTPException, Depends,Query
from sqlmodel import Session, select, SQLModel, Field, delete,func
from .db import engine, get_session
from pydantic import  validator, BaseModel
from typing import List, Optional
from routes.commonflds import CommonFields  
from datetime import datetime   
from routes.company import Company
from routes.state import State
from routes.country import Country

router = APIRouter( tags=["City"])

class City(CommonFields, table=True):
    __tablename__ = "city"
    __table_args__ = {"extend_existing": True} 
    countryid: int = Field(foreign_key="country.id", nullable=False)
    stateid: int = Field(foreign_key="state.id", nullable=False)
    citycode: str = Field(index=True, nullable=False)
    cityname: str = Field(index=True, nullable=False)
    active: bool = True  # default value

class PCity(BaseModel):
    createdby: str = Field(nullable=False)
    modifiedby: str = Field(nullable=False)
    countryid: int = Field(default=0,nullable=False)
    stateid: int = Field(default=0,nullable=False)
    citycode: str = Field(nullable=False)
    cityname: str = Field(nullable=False)    
    active: bool = True 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class CityUpdate(BaseModel):
    modifiedby: str = Field(nullable=False)
    countryid: int = Field(default=0,nullable=False)
    stateid: int = Field(default=0,nullable=False)
    citycode: str = Field(nullable=False)
    cityname: str = Field(nullable=False)    
    active: bool = True 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class CityRead(BaseModel):
    id: int
    countryid: int
    countryname: Optional[str] = None
    stateid: int
    statename: Optional[str] = None
    statecode: Optional[str] = None
    countrycode: Optional[str] = None
    citycode: str
    cityname: str
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
class CityResponse(BaseModel):
    total: int
    city_list: List[CityRead] = []
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }
class CitySearch(BaseModel):
    id: int
    citycode: str
    cityname: str
    active: bool
    stateid: int
    statecode: Optional[str] = None
    statename: Optional[str] = None
    countryid: int
    countryname: Optional[str] = None
    countrycode: Optional[str] = None

@router.post("/city/", response_model=CityRead)
def create_city(city: PCity, session: Session= Depends(get_session)):   
    db_city = session.exec(select(City).where(City.citycode == city.citycode)).first()
    if db_city:
        raise HTTPException(status_code=400, detail="City code already exists")
    db_state = session.get(State, city.stateid)
    db_city = session.exec(select(City).where(City.cityname == city.cityname, City.stateid == city.stateid)).first()
    if db_city:   
        raise HTTPException(status_code=400, detail="City name already exists in the state")
    if not db_state:
        raise HTTPException(status_code=400, detail="State ID does not exist")
    db_country = session.get(Country, city.countryid)
    if not db_country:
        raise HTTPException(status_code=400, detail="Country ID does not exist")    
    db_city = City.from_orm(city)
    session.add(db_city)
    session.commit()
    session.refresh(db_city)
    return  db_city

@router.post("/cityupdate/{cityid}", response_model=CityUpdate)
def update_city(cityid: int, city:  CityUpdate, session: Session= Depends(get_session)):
    db_city = session.get(City, cityid)
    if not db_city:
        raise HTTPException(status_code=404, detail="City not found")   
    db_state = session.get(State, city.stateid)
     
    for key, value in city.model_dump().items():
        setattr(db_city, key, value)    
    session.add(db_city)
    session.commit()    
    session.refresh(db_city)
    return city

@router.get("/city/search/", response_model=List[CitySearch])
def search_state(field: str = Query(...) , value: str = Query(...),
                  db: Session = Depends(get_session)):
    query = db.query(
        City.id,
        City.citycode,
        City.cityname,  
        City.active,
        City.stateid,   
        State.statename,
        State.statecode,
        City.countryid,     
        Country.countryname,
        Country.countrycode
        ).join(State, City.stateid == State.id).join(Country, City.countryid == Country.id)  
    apply_filter = False
    if field == "citycode":
        query = query.filter(City.citycode.ilike(f"%{value}%"))
    elif field == "cityname":
        query = query.filter(City.cityname.ilike(f"%{value}%")) 
    elif field == "active": 
        active_value = value.lower() in ["yes", "true", "1"]
        query = query.filter(City.active == active_value)   
    elif field == "statename":
        query = query.filter(State.statename.ilike(f"%{value}%"))   
    elif field == "countryname":
        query = query.filter(Country.countryname.ilike(f"%{value}%"))   
    results = query.all()

    return [
    {
        "id": row.id,
        "citycode": row.citycode,
        "cityname": row.cityname,
        "active": row.active,
        "stateid": row.stateid,
        "statename": row.statename,
        "countryid": row.countryid,
        "countryname": row.countryname,
        "statecode": row.statecode,
        "countrycode": row.countrycode
    }
    for row in results
]
   
@router.get("/cities/", response_model=CityResponse)
def read_cities(skip: int = 0, limit: int = 10, session : Session = Depends(get_session)):
    cities = session.exec(select(City).order_by (City.cityname).offset(skip).limit(limit)).all()
    totalcount = session.exec(select(func.count()).select_from(City)).one()
    city_list = []
    for city in cities:
        db_state = session.get(State, city.stateid)
        db_country = session.get(Country, city.countryid)
        city_data = CityRead(
            id=city.id,
            countryid=city.countryid,
            countryname=db_country.countryname if db_country else None,
            stateid=city.stateid,
            statename=db_state.statename if db_state else None,
            citycode=city.citycode,
            cityname=city.cityname,
            active=city.active,
            createdby=city.createdby,
            createdon=city.createdon,
            modifiedby=city.modifiedby,
            modifiedon=city.modifiedon,
            statecode=db_state.statecode if db_state else None,
            countrycode=db_country.countrycode if db_country else None
        )
        city_list.append(city_data)
    return {"city_list": city_list , "total":totalcount}  

@router.get("/cities/{city_id}", response_model=CityRead)   
def read_city(city_id: int, session: Session = Depends(get_session)):
    db_city = session.exec(select(City).where(City.id == city_id)).first()
    if not db_city:
        raise HTTPException(status_code=404, detail="City not found")
    db_state = session.get(State, db_city.stateid)
    db_country = session.get(Country, db_city.countryid)
    return CityRead(
        id=db_city.id,
        countryid=db_city.countryid,
        countryname=db_country.countryname if db_country else None,
        stateid=db_city.stateid,
        statename=db_state.statename if db_state else None,
        citycode=db_city.citycode,
        cityname=db_city.cityname,
        active=db_city.active,
        createdby=db_city.createdby,
        createdon=db_city.createdon,
        modifiedby=db_city.modifiedby,
        modifiedon=db_city.modifiedon
    )            
@router.delete("/city/{city_id}")
def delete_city(city_id: int, session: Session = Depends(get_session)):     
    city = session.get(City, city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    session.delete(city)
    session.commit()
    return {"ok": True}            

@router.delete("/cities/")
def delete_all_cities(session: Session = Depends(get_session)):    
    session.exec(delete(City))
    session.commit()
    return {"ok": True}