from fastapi import APIRouter,  HTTPException,Depends,Query
from sqlmodel import Session, select,SQLModel,Field,delete, and_,func,cast,String,Text
from .db import engine, get_session
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER,JSON 
from pydantic import EmailStr,validator,BaseModel,model_validator
from typing import List, Optional,Dict, Any 
from routes.commonflds import CommonFields  
from datetime import datetime, timedelta, date
from routes.company import Company   
from routes.userauth import get_current_user
from sqlalchemy.exc import IntegrityError 

router = APIRouter( tags=["FinancialYear"])

class FinYrheader(CommonFields, table=True):
    __tablename__ = "finyr_header"
    __table_args__ = {"extend_existing": True} 
    finyrname: str = Field(index=True,nullable=False)
    hstartdate: date = Field(nullable=False)
    henddate: date = Field(nullable=False)
    active: bool = True  # default value

class Finyrdetail(SQLModel, table=True):
    __tablename__ = "finyr_detail"
    __table_args__ = {"extend_existing": True} 
    id: int | None = Field(default=None, primary_key=True)
    finyrid: int = Field(foreign_key="finyr_header.id", nullable=False)
    periodname: str = Field(index=True,nullable=False)
    startdate: date = Field(nullable=False)
    enddate: date = Field(nullable=False)
    periodno: int = Field(default=0, nullable=False)
    status: str = Field(default ="Open",nullable=False)  # default value 

class PFinYr(BaseModel):
    createdby: str = Field(nullable=False)
    modifiedby: str = Field(nullable=False)
    finyrname: str = Field(nullable=False)
    hstartdate: date = Field(nullable=False)
    henddate: Optional[date] = None
    active: bool = True 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }
    @model_validator(mode="after")
    def set_enddate(self):
        if self.henddate is None:
            self.henddate = self.hstartdate.replace(year=self.hstartdate.year + 1) - timedelta(days=1)
        return self

class Pfinyrdetail(BaseModel):
    finyrid: int = Field(default= 0,nullable=False)
    periodname: str = Field(nullable=False)
    startdate: date = Field(nullable=False)
    enddate: date = Field(nullable=False)
    periodno: int = Field(default=0, nullable=False)
    status: str = Field(default ="Open",nullable=False)  # default value    
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class FinYrResponse(BaseModel):
    finyr: FinYrheader
    periods: List[Finyrdetail]   
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }



class Finyrupdate(BaseModel):   
    modifiedby: str = Field(nullable=False)
    finyrname: Optional[str] = None
    hstartdate: Optional[date] = None
    henddate: Optional[date] = None
    active: Optional[bool] = None
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }  
    @model_validator(mode="after")
    def set_enddate(self):
        if self.henddate is None:
            self.henddate = self.hstartdate.replace(year=self.hstartdate.year + 1) - timedelta(days=1)
        return self    

class FinyrRead(BaseModel):
    id: int
    createdby: str  
    modifiedby: str 
    finyrname: str  
    hstartdate: date  
    henddate: Optional[date] = None
    active: bool = True 
    createdon: datetime
    modifiedon: datetime
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None,     
            date: lambda v: v.strftime("%d/%m/%Y") if v else None        
        }
    }

class FinyrSearch(BaseModel):
    id: int
    finyrname: str
    hstartdate: date
    henddate: Optional[date]= None
    active: bool=True

class FinyrgetResponse(BaseModel):
    finyrs: List[FinyrRead]
    total: int

def generate_periods(start_date: date, end_date: date) -> List[Pfinyrdetail]:
    periods = []
    current_start = start_date
    period_no = 1

    while current_start < end_date:
        current_end = (current_start.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        if current_end > end_date:
            current_end = end_date

        period_name = current_start.strftime("%B %Y")
        periods.append(Pfinyrdetail(
            periodname=period_name,
            startdate=current_start,
            enddate=current_end,
            periodno=period_no,
            status="Open"
        ))

        current_start = current_end + timedelta(days=1)
        period_no += 1

    return periods

@router.post("/generate_periods", response_model=list[Pfinyrdetail])
def generate_periods_api(payload: dict):
    try:
        def parse_date(date_str):
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Invalid date format: {date_str}")

        start_date = parse_date(payload["startdate"])
        end_date = parse_date(payload["enddate"])

        periods = generate_periods(start_date, end_date)
        return periods

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/addfinyr", response_model=FinYrheader)
def create_finyr(finyr: PFinYr, session: Session = Depends(get_session)):
    # Check for overlapping financial years
    overlapping_finyr = session.exec(
        select(FinYrheader).where(
            (FinYrheader.hstartdate <= finyr.henddate) & (FinYrheader.henddate >= finyr.hstartdate)
        )
    ).first()
    if overlapping_finyr:
        raise HTTPException(status_code=400, detail="Financial year overlaps with an existing one.")

    new_finyr = FinYrheader.from_orm(finyr)
    session.add(new_finyr)
    session.commit()
    session.refresh(new_finyr)

    # Generate and add periods
    periods = generate_periods(finyr.hstartdate, finyr.henddate)
    for period in periods:
        period.finyrid = new_finyr.id
        new_period = Finyrdetail.from_orm(period)
        session.add(new_period)

    session.commit()
    return {"message":"Financial year and periods created successfully"}

@router.post("/updatefinyr/{finyr_id}", response_model=FinYrheader)
def update_finyr(finyr_id: int, finyr_update: Finyrupdate, session: Session = Depends(get_session)):
    finyr = session.get(FinYrheader, finyr_id)
    if not finyr:
        raise HTTPException(status_code=404, detail="Financial year not found")

    # Update fields if provided
    if finyr_update.finyrname is not None:
        finyr.finyrname = finyr_update.finyrname
    if finyr_update.hstartdate is not None:
        finyr.hstartdate = finyr_update.hstartdate
    if finyr_update.henddate is not None:
        finyr.henddate = finyr_update.henddate
    if finyr_update.active is not None:
        finyr.active = finyr_update.active
    if finyr_update.modifiedby is not None:
        finyr.modifiedby = finyr_update.modifiedby

    # Check if periods need to be updated
    update_periods = False
    if finyr_update.hstartdate is not None or finyr_update.henddate is not None:
        update_periods = True

    session.add(finyr)
    session.commit()
    session.refresh(finyr)

    if update_periods:
        # Delete existing periods
        session.exec(delete(Finyrdetail).where(Finyrdetail.finyrid == finyr_id))
        session.commit()

        # Generate and add new periods
        new_start = finyr_update.hstartdate if finyr_update.hstartdate is not None else finyr.hstartdate
        new_end = finyr_update.henddate if finyr_update.henddate is not None else finyr.henddate
        periods = generate_periods(new_start, new_end)
        for period in periods:
            period.finyrid = finyr.id
            new_period = Finyrdetail.from_orm(period)
            session.add(new_period)
        session.commit()

    return finyr

@router.get("/finyr/search",response_model=list[FinyrSearch])
def finyr_search( 
     field: str = Query(...),
     value: str = Query(...),     
     db: Session = Depends(get_session)):
 query = db.query(
     FinYrheader.id,   
     FinYrheader.finyrname,
     FinYrheader.hstartdate,
     FinYrheader.henddate,
     FinYrheader.active,
    ) 

 if field == "finyrname":
    query = query.filter(FinYrheader.finyrname.ilike(f"%{value}%"))
 elif field == "hstartdate":
    try:
        if "/" in value:
            date_value = datetime.strptime(value, "%d/%m/%Y").date()
        else:
            date_value = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use dd/mm/yyyy or yyyy-mm-dd.")
    
    query = query.filter(FinYrheader.hstartdate == date_value)
 else:
    raise HTTPException(status_code=400, detail="Invalid Search")

 result = query.all()

 return [
        {
            "id":r.id,
            "finyrname":r.finyrname,
            "hstartdate": r.hstartdate.isoformat() if r.hstartdate else None,
            "henddate": r.henddate.isoformat() if r.henddate else None,
            "active": r.active,  
            
        } for r in result
        ]



@router.get("/header", response_model=FinyrgetResponse)
def list_finyrs(
    skip: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    finyrs = session.exec(
        select(FinYrheader)
        .order_by(FinYrheader.hstartdate.desc())
        .offset(skip)
        .limit(limit)
    ).all()

    totalcount = session.exec(select(func.count(FinYrheader.id))).one()

    if not finyrs:
        raise HTTPException(status_code=404, detail="finyrs not found")

    # ✅ Correctly loop through the list
    finyr_list = [
        FinyrRead(
            id=f.id,
            createdby=f.createdby,
            modifiedby=f.modifiedby,
            finyrname=f.finyrname,
            hstartdate=f.hstartdate,
            henddate=f.henddate,
            active=f.active,
            createdon=f.createdon,
            modifiedon=f.modifiedon,
        )
        for f in finyrs
    ]

    # ✅ Ensure it matches FinyrgetResponse structure
    return FinyrgetResponse(finyrs=finyr_list, total=totalcount)

@router.get("/finyr/{finyr_id}", response_model=FinYrResponse)
def get_finyr(finyr_id: int, session: Session = Depends(get_session)):
    finyr = session.get(FinYrheader, finyr_id)
    if not finyr:
        raise HTTPException(status_code=404, detail="Financial year not found")

    periods = session.exec(select(Finyrdetail).where(Finyrdetail.finyrid == finyr_id).order_by(Finyrdetail.periodno)).all()
    return FinYrResponse(finyr=finyr, periods=periods)


@router.delete("/{finyr_id}", response_model=dict)
def delete_finyr(finyr_id: int, session: Session = Depends(get_session)):    
   try:
    finyr = session.get(FinYrheader, finyr_id)
    if not finyr:
        raise HTTPException(status_code=404, detail="Financial year not found")

    # Delete associated periods first
    session.exec(delete(Finyrdetail).where(Finyrdetail.finyrid == finyr_id))
    session.commit()

    # Then delete the financial year
    session.delete(finyr)
    session.commit()
    return {"message": "Financial year and associated periods deleted successfully"}
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