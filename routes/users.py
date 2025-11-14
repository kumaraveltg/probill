from fastapi import APIRouter,  HTTPException,Depends,Query
from sqlmodel import Session, select,SQLModel,Field,Column,create_engine,and_,func,any_,cast
from .db import engine, get_session
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER
from pydantic import EmailStr,validator
from typing import List, Optional,Dict, Any
from datetime import datetime,timedelta
from pydantic import BaseModel
from routes.utils import hash_password
from routes.company import Company 
from routes.userauth import get_current_user
from routes.user_role import UserRole
from sqlalchemy.exc import IntegrityError



router = APIRouter(prefix="/users", tags=["Users"])

 
# Model

class Users(SQLModel, table=True):
    __table_args__ = {"extend_existing": True} 
    id: int | None = Field(default=None, primary_key=True)
    cancel: str ="F"
    createdby: str = Field(nullable=False)
    createdon: datetime = Field(default_factory=datetime.now) 
    modifiedby: str= Field(nullable=False)
    modifiedon:  datetime = Field(default_factory=datetime.now,sa_column_kwargs={"onupdate":datetime.now}) 
    username: str = Field(index=True,nullable=False)
    password: str = Field(default="123456")
    hpassword : Optional[str] = None 
    firstname: Optional[str]=None
    emailid: Optional[EmailStr]= None
    usertype: Optional[str]= None
    userroleids: Optional[List[int]] = Field(
        sa_column=Column(ARRAY(INTEGER))
    )
    active: bool = True  # default value
    companyid: int = Field(default=1, nullable=False)
    companyno: str
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
     }


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
    usertype: Optional[str]= None
    active: bool = True 
    sourceid:Optional[int]= None
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
    usertype: Optional[str]= None
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
    password: Optional[str] = None
    firstname: str
    emailid: str
    userroleids: List[int]
    rolename:Optional[str]= None
    usertype: Optional[str]= None
    active: bool
    companyid: Optional[int] = None 
    companyno: str
    companyname: str | None = None
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
   
class UsersSearch(BaseModel):
   id : int
   username: str
   password: Optional[str] = None
   firstname: str
   emailid: str
   userroleids: List[int]
   rolename: Optional[str] = None
   usertype: Optional[str]= None
   active: bool
   companyid: Optional[int] = None 
   companyno: str
   companyname: str | None = None

class UserResponse(BaseModel):
    list_users: List[UserWithCompany]  
    total: int

class Config:
        orm_mode = True
   
# ✅ Create user
@router.post("/users/", response_model=Puser)
def create_user(user: Puser , current_user: dict = Depends(get_current_user)):
    with Session(engine) as session:
        user_dict = user.dict()
        user_dict["hpassword"] = hash_password(user_dict.get("password", "123456"))

        # Use user_dict here, not user.dict()
        user_data = Users(**user_dict)

        existing_user = session.exec(
        select(Users).where(
            (Users.username == user.username) &
            (Users.companyno == user.companyno) &
            (Users.usertype == user.usertype)
            )  ).first()

        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        session.add(user_data)
        session.commit()
        session.refresh(user_data)
        return Puser.from_orm(user_data)
#

@router.post("/updateuser/{id}")
def update_user(id: int,update_user:Upduser,session: Session=Depends(get_session),current_user: dict = Depends(get_current_user)):
    db_users = session.get(Users,id)
    if not db_users:
       raise HTTPException(status_code=404,detail="User name not found")
    for key,Value in update_user.dict(exclude_unset=True).items():
       setattr(db_users,key,Value) 
    session.add(db_users)
    session.commit()
    session.refresh(db_users)
    return {"message":f"User - {db_users.username} has been updated"}

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
            password = row.password,
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


@router.get("/search/{companyid}", response_model=List[UsersSearch])
def search_user( 
     companyid: int,
     field: str = Query(...),
     value: str = Query(...),     
     db: Session = Depends(get_session)
    ):
    query = (
    db.query(
        Users.id,
        Users.username,
        Users.firstname,
        Users.emailid,
        Users.userroleids,
        func.array_agg(UserRole.rolename).label("rolenames"),
        Users.usertype,
        Users.active,
        Users.companyid,
        Company.companyname,
        Company.companyno,
    )
    .join(Company, Users.companyid == Company.id, isouter=True)
    .join(UserRole, UserRole.id == any_(cast(Users.userroleids, ARRAY(INTEGER))), isouter=True)
    .where(and_(Users.active == True, Users.companyid == companyid))
    .group_by(
        Users.id,
        Users.username,
        Users.firstname,
        Users.emailid,
        Users.userroleids,
        UserRole.rolename,
        Users.usertype,
        Users.active,
        Users.companyid,
        Company.companyname,
        Company.companyno,
    )
    .order_by(Users.username)
    )

    if field == "username":
        Query = query.filter(Users.username.ilike(f"%{value}%"))
    elif field == "firstname":
        Query = query.filter(Users.firstname.ilike(f"%{value}%")) 
    else:
        raise HTTPException(status_code=400, detail="Invalid search field")
    
    results = Query.all()  
    return [
        {   "id": r.id,
            "username": r.username,
            "firstname":r.firstname,
            "emailid" : r.emailid, 
            "userroleids":r.userroleids,
            "usertype":r.usertype,
            "active" : r.active,
            "companyid":r.companyid,
            "companyname": r.companyname,
            "companyno" :r.companyno
        }   
        for r in results
    ]

@router.get("/users/{companyid}", response_model=UserResponse)
def users_company(
    companyid: int,
    skip: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session),
    current_user: Dict = Depends(get_current_user)
):
    query = (
        select(Users, Company.companyname, Company.id, Company.companyno,UserRole.rolename)
        .join(Company, Users.companyid == Company.id, isouter=True)
        .join(UserRole, UserRole.id == any_(cast(Users.userroleids, ARRAY(INTEGER))), isouter=True)
        .where(and_(Users.active == True, Users.companyid == companyid))
        .order_by(Users.username)
        .offset(skip)
        .limit(limit)
    )

    user_list = session.exec(query).all()

    totalcount = session.exec(
        select(func.count(Users.id)).where(
            and_(Users.active == True, Users.companyid == companyid)
        )
    ).one()

    result = []
    for row in user_list:
        users = row[0]
        companyname = row[1]
        companyid = row[2]
        companyno = row[3]
        rolename = row[4]

        user_data = UserWithCompany.from_orm(users)
        user_data.companyname = companyname
        user_data.companyid = companyid
        user_data.companyno = companyno
        user_data.rolename = rolename
        result.append(user_data.dict())

    return { "list_users": result,"total": totalcount}



#delete
@router.delete("/delete/{id}")
def delete_user(id: int,session: Session=Depends(get_session)):
  try:
   db_user = session.get(Users,id)
   if not db_user:
      raise HTTPException(status_code=404,detail="User Not found")
   session.delete(db_user)
   session.commit()
   return {"message":f"User Name {db_user.username} has been deleted "}
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
   