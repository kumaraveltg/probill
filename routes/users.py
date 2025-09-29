from fastapi import APIRouter,  HTTPException,Depends
from sqlmodel import Session, select,SQLModel,Field,Column,create_engine
from .db import engine, get_session
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER
from pydantic import EmailStr,validator
from typing import List, Optional,Dict, Any
from datetime import datetime,timedelta
from pydantic import BaseModel
from routes.utils import hash_password
from routes.company import Company 



router = APIRouter(prefix="/users", tags=["Users"])

 
# Model

class Users(SQLModel, table=True):
    __table_args__ = {"extend_existing": True} 
    id: int | None = Field(default=None, primary_key=True)
    cancel: str ="F"
    createdby: str = Field(nullable=False)
    createdon: datetime = Field(default_factory=datetime.now) 
    #createdon: str = Field(default_factory=lambda: datetime.now().strftime("%d/%m/%y %H:%M:%S")) I use get api problem
    modifiedby: str= Field(nullable=False)
    modifiedon:  datetime = Field(default_factory=datetime.now,sa_column_kwargs={"onupdate":datetime.now}) 
    #modifiedon: str = Field(default_factory=lambda: datetime.now().strftime("%d/%m/%y %H:%M:%S"))
    username: str = Field(index=True,nullable=False)
    password: str = Field(default="123456")
    hpassword : Optional[str] = None 
    firstname: Optional[str]=None
    emailid: Optional[EmailStr]= None
    userroleids: Optional[List[int]] = Field(
        sa_column=Column(ARRAY(INTEGER))
    )
    active: bool = True  # default value
    companyid: int = Field(default=1, nullable=False)
    companyno: str

    def __post_init__(self):
        # Automatically hash password
        if self.password and not self.hpassword:
            self.hpassword = hash_password(self.password)
#schema/ pydantic 
    
class Puser(BaseModel):
    companyid: int = Field(default=1, nullable=False)
    companyno: str = Field(default=1, nullable=False)
    createdby: str = Field(nullable=False)
    modifiedby: str = Field(nullable=False)
    username: str = Field(nullable=False)
    firstname: Optional[str] = None
    emailid: Optional[EmailStr] = None
    userroleids: Optional[List[int]] = None
    active: bool = True 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }


    @validator("createdby", "modifiedby","username" )
    def must_not_be_empty(cls, v):
     if not v or not v.strip():
        raise ValueError("This field is required")
     return v
    @validator("userroleids")
    def roles_must_not_be_empty(cls, v):
        if v is None or not v:
            raise ValueError("userroleids must not be empty")
        return v

   
class Upduser(BaseModel):
    modifiedby: str = Field(nullable=False)
    username: str = Field(nullable=False)
    password: str = Field(nullable=False)
    firstname: Optional[str] = None
    emailid: Optional[EmailStr] = None
    userroleids: Optional[List[int]] = None
    active: bool = True 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }


    @validator( "modifiedby","username" )
    def must_not_be_empty(cls, v):
     if not v or not v.strip():
        raise ValueError("This field is required")
     return v
    @validator("userroleids")
    def roles_must_not_be_empty(cls, v):
        if v is None or not v:
            raise ValueError("userroleids must not be empty")
        return v

class UserWithCompany(BaseModel):
    id: int
    username: str
    firstname: str
    emailid: str
    userroleids: List[int]
    active: bool
    companyid: Optional[int] = None 
    companyno: str
    companyname: str | None = None
    createdby: str
    createdon: datetime
    modifiedby: str
    modifiedon: datetime
   


# ✅ Create user
@router.post("/users/", response_model=Puser)
def create_user(user: Puser):
    with Session(engine) as session:
        user_dict = user.dict()
        user_dict["hpassword"] = hash_password(user_dict.get("password", "123456"))

        # Use user_dict here, not user.dict()
        user_data = Users(**user_dict)

        existing_user = session.exec(
            select(Users).where(Users.username == user.username)
        ).first()

        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        session.add(user_data)
        session.commit()
        session.refresh(user_data)
        return Puser.from_orm(user_data)
#

@router.get("/userlist",response_model=List[UserWithCompany])
def users_list(session: Session=Depends(get_session)):
    statement = select(
            Users.id,
            Users.username,
            Users.firstname,
            Users.emailid,
            Users.userroleids,
            Users.active,
            Users.companyid,
            Users.companyno,
            Users.createdby,
            Users.createdon,
            Users.modifiedby,
            Users.modifiedon,
            Company.companyname
        ).join(Company, Users.companyid == Company.id, isouter=True).where(Users.active == True).order_by(Users.id.desc())
    
    results = session.exec(statement)
    get_users_list = [
       UserWithCompany(
            id=row.id,
            username=row.username,
            firstname=row.firstname,
            emailid=row.emailid,
            userroleids=row.userroleids,
            active=row.active,
            companyid=row.companyid,
            companyno= row.companyno,
            companyname=row.companyname,
            createdby=row.createdby,
            createdon=row.createdon,
            modifiedby=row.modifiedby,
            modifiedon=row.modifiedon,
        )
        for row in results
    ]
    return get_users_list
    

@router.post("/updateuser/{id}")
def update_user(id: int,update_user:Upduser,session: Session=Depends(get_session)):
    db_users = session.get(Users,id)
    if not db_users:
       raise HTTPException(status_code=404,detail="User name not found")
    for key,Value in update_user.dict(exclude_unset=True).items():
       setattr(db_users,key,Value) 
    session.add(db_users)
    session.commit()
    session.refresh(db_users)
    return {"message":f"User - {db_users.username} has been updated"}

#delete

@router.delete("/delete/{id}")
def delete_user(id: int,session: Session=Depends(get_session)):
   db_user = session.get(Users,id)
   if not db_user:
      raise HTTPException(status_code=404,detail="User Not found")
   session.delete(db_user)
   session.commit()
   return {"message":f"User Name {db_user.username} has been deleted "}
   