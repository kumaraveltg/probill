from fastapi import APIRouter, HTTPException, Depends,Query
from sqlmodel import Session, select, SQLModel, Field, delete ,func
from .db import engine, get_session
from pydantic import  validator, BaseModel
from typing import List, Optional
from routes.commonflds import CommonFields  
from datetime import datetime  
from routes.country import Country  

router = APIRouter( tags=["State"])

class State(CommonFields, table=True):
    __tablename__ = "state"
    __table_args__ = {"extend_existing": True} 
    countryid: int = Field(foreign_key="country.id", nullable=False)
    statecode: str = Field(index=True, nullable=False)
    statename: str = Field(index=True, nullable=False)
    active: bool = True  # default value    

class PState(BaseModel):
    createdby: str = Field(nullable=False)
    modifiedby: str = Field(nullable=False)
    countryid: int = Field(default=0,nullable=False)
    statecode: str = Field(nullable=False)
    statename: str = Field(nullable=False)    
    active: bool = True 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class StateUpdate(BaseModel):
    modifiedby: str = Field(nullable=False)
    countryid: int = Field(default=0,nullable=False)
    statecode: str = Field(nullable=False)
    statename: str = Field(nullable=False)    
    active: bool = True 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class StateRead(BaseModel):
    id: int
    countryid: int
    countryname: Optional[str] = None
    countrycode: Optional[str] = None
    statecode: str
    statename: str
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
class Config:
    orm_mode = True

class StateSearch(BaseModel):
    id: int
    statecode: str
    statename: str
    active: bool
    countryid: int
    countryname: str

class StateListResponse(BaseModel):
    state_list: List[StateRead]
    total: int = Field(default=0)

@router.post("/state/", response_model=PState)
def create_state(state: PState, session: Session= Depends(get_session)):
    db_state = session.exec(select(State).where(State.statecode == state.statecode)).first()
    if db_state:
        raise HTTPException(status_code=400, detail="State code already exists")
    db_state = session.exec(select(State).where(State.statename == state.statename)).first()
    if db_state:
        raise HTTPException(status_code=400, detail="State name already exists")
    db_country = session.exec(select(Country).where(Country.id == state.countryid)).first()    
    if not db_country:
        raise HTTPException(status_code=400, detail="Country ID does not exist")
    
    db_state = State.from_orm(state)
    session.add(db_state)
    session.commit()
    session.refresh(db_state)
    return db_state
@router.post("/stateupdate/{stateid}", response_model=StateUpdate)
def update_state(stateid:int,state: StateUpdate, session: Session= Depends(get_session)):
    db_state = session.exec(select(State).where(State.id == stateid)).first()
    if not db_state:
        raise HTTPException(status_code=400, detail="State Not found")
        
    for key, value in state.dict(exclude_unset=True).items():
        setattr(db_state, key, value)
    session.add(db_state)
    session.commit()
    session.refresh(db_state)
    return db_state

@router.get("/state/search", response_model=List[StateSearch])
def search_state(
    field: str = Query(...),
    value: str = Query(...),
    db: Session = Depends(get_session)
):
    # Base query: pick only columns you need
    query = db.query(
        State.id,
        State.statecode,
        State.statename,
        State.active,
        State.countryid,
        Country.countryname
    ).join(Country, State.countryid == Country.id)

    # Apply filters
    if field == "statecode":
        query = query.filter(State.statecode.ilike(f"%{value}%"))
    elif field == "statename":
        query = query.filter(State.statename.ilike(f"%{value}%"))
    elif field == "active":
        active_value = value.lower() in ["yes", "true", "1"]
        query = query.filter(State.active == active_value)
    elif field == "countryname":
        query = query.filter(Country.countryname.ilike(f"%{value}%"))

    results = query.all()

    # Each row is a tuple → map to dict
    return [
        {
            "id": r.id,
            "statecode": r.statecode,
            "statename": r.statename,
            "active": r.active,
            "countryid": r.countryid,
            "countryname": r.countryname,
        }
        for r in results
    ]

@router.get("/states/", response_model=StateListResponse)
def read_states(skip: int = 0, limit: int = 10, session: Session = Depends(get_session)):
    states = session.exec(select(State).order_by(State.statename).offset(skip).limit(limit)).all()
    totalcount= session.exec(select(func.count()).select_from(State)).one()
    
    state_list = []
    for state in states:
        db_country = session.exec(select(Country).where(Country.id == state.countryid)).first()
        countryname = db_country.countryname if db_country else None
        state_data = StateRead.from_orm(state)
        state_data.countryname = countryname
        state_list.append(
            StateRead(
                id=state.id,
                statecode=state.statecode,
                statename=state.statename,
                countryid=state.countryid,
                countryname=countryname,
                countrycode=db_country.countrycode if db_country else None,
                active=state.active,
                createdby=state.createdby,
                createdon=state.createdon,
                modifiedby=state.modifiedby,
                modifiedon=state.modifiedon
            )
        )
    return { "state_list":state_list , "total":totalcount}

@router.get("/states/{state_id}", response_model=StateRead)
def read_state(state_id: int, session: Session = Depends(get_session)):
    db_state = session.exec(select(State).where(State.id == state_id)).first()
    if not db_state:
        raise HTTPException(status_code=404, detail="State not found")
    db_country = session.exec(select(Country).where(Country.id == db_state.countryid)).first()
    countryname = db_country.countryname if db_country else None
    state_data = StateRead.from_orm(db_state)
    state_data.countryname = countryname
    return state_data   


@router.delete("/statedelete/{state_id}")
def delete_state(state_id: int, session: Session = Depends(get_session)):     
    state = session.get(State, state_id)
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    statement = delete(State).where(State.id == state_id)
    session.exec(statement)
    session.commit()