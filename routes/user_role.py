from fastapi import APIRouter,  HTTPException,Depends,Query
from sqlmodel import Session, select,SQLModel,Field,Column,func,and_
from .db import engine, get_session
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER,JSON
from pydantic import EmailStr,validator,BaseModel
from typing import List, Optional,Dict, Any 
from routes.commonflds import CommonFields  
from datetime import datetime
from routes.company import Company
from routes.userauth import get_current_user
from sqlalchemy.exc import IntegrityError

router = APIRouter(tags=["UserRole"])

 
 
# Model

class UserRole(CommonFields, table=True):
    __tablename__ = "userrole"
    __table_args__ = {"extend_existing": True} 
    companyid: int = Field(foreign_key="company.id", nullable=False)
    rolename: str = Field(index=True,nullable=False)
    active: bool = True  # default value
    permissions: list[dict] = Field(
        sa_column=Column(JSON), default=[]
    )
    companyno: str = Field(nullable=False)
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

 
#schema/ pydantic
class PUserRole(BaseModel):
    createdby: str = Field(nullable=False)
    modifiedby: str = Field(nullable=False)
    companyid: int = Field(default= 0,nullable=False)
    companyno: str
    rolename: str = Field(nullable=False)
    permissions: Optional[List[Dict[str, Any]]] = []
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class UpdateUserRole(BaseModel):
    modifiedby: Optional[str]= None
    companyid: Optional[int] = None
    companyno: str
    rolename: Optional[str] = None
    permissions: Optional[List[Dict[str, Any]]] = None
    active: Optional[bool] = None

class UserRoleRead(BaseModel):
    id: int
    createdby: str
    createdon: datetime 
    modifiedby: str
    modifiedon: datetime        
    companyid: int
    companyname: Optional[str] = None
    companyno: Optional[str]
    rolename: str
    permissions: List[Dict[str, Any]]
    active: bool 
    model_config = {
            "from_attributes": True,
            "json_encoders": {
                datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
            }
        }

class UserRoleSearch(BaseModel):
    id: int
    companyid: int
    companyname: Optional[str] = None
    companyno: str
    rolename: str
    permissions: List[Dict[str, Any]]

class UserRoleResponse(BaseModel):
    user_rolelist: list[UserRoleRead]
    total: int

@router.post("/adduserrole", response_model=PUserRole)
def add_userrole(userrole: PUserRole, session: Session = Depends(get_session),current_user:dict= Depends(get_current_user)):
    if not userrole.rolename:
        raise HTTPException(status_code=400, detail="Role name is required.") 
    if session.exec(select(UserRole).where(UserRole.rolename == userrole.rolename, UserRole.companyid == userrole.companyid)).first():
        raise HTTPException(status_code=400, detail="Role name already exists for this company.")    
    db_userrole = UserRole.from_orm(userrole)
    session.add(db_userrole)
    session.commit()
    session.refresh(db_userrole)
    return db_userrole  


@router.post("/updateuserrole/{userrole_id}", response_model=UpdateUserRole)
def update_userrole(userrole_id: int, userrole: UpdateUserRole, session: Session = Depends(get_session),current_user:dict= Depends(get_current_user)):
    db_userrole = session.get(UserRole, userrole_id)
    if not db_userrole:
        raise HTTPException(status_code=404, detail="User role not found.")
    userrole_data = userrole.model_dump(exclude_unset=True)
    for key, value in userrole_data.items():
        setattr(db_userrole, key, value)
    session.add(db_userrole)
    session.commit()
    session.refresh(db_userrole)
    return db_userrole  

@router.get("/search/{companyid}",response_model=list[UserRoleSearch])
def userrole_search(companyid: int,
     field: str = Query(...),
     value: str = Query(...),     
     db: Session = Depends(get_session)):
 Query = db.query(
     UserRole.id,     
     UserRole.companyid,
     Company.companyno,
     Company.companyname,
     UserRole.rolename,
     UserRole.permissions,
 ).join(Company,UserRole.companyid==Company.id,isouter=True).filter(Company.id==companyid)

 if field == "rolename":
     Query == Query.filter(UserRole.rolename.ilike(f"%{value}%"))    
 elif field == "companyname":
     Query == Query.filter(Company.Companyname.ilike(f"%{value}%"))
 else:
     raise HTTPException(status_code=400,detail="Invaild Search")

 result = Query.all()

 return [
        {
            "id":r.id,
            "companyid":r.companyid,
            "companyno":r.companyno,
            "companyname":r.companyname,
            "rolename": r.rolename, 
            "permissions": r.permissions
            
        } for r in result
        ]


@router.get("/getuserroles/{companyid}", response_model= UserRoleResponse)
def get_userroles(
    companyid: int | None = None, skip: int = 0, limit: int = 10,
    session: Session = Depends(get_session),current_user:dict= Depends(get_current_user)
):
    from routes.company import Company  # Import here to avoid circular import
    from routes.user_role import UserRole

    query = (
    select(UserRole, Company.companyname)
    .join(Company, UserRole.companyid == Company.id, isouter=True)
    .where(and_(Company.active == True, Company.id == companyid))
    .order_by(UserRole.rolename.desc())
    .offset(skip)
    .limit(limit)
    )
    
    totalcount = session.exec(select(func.count(UserRole.id)).where(and_(Company.active==True,Company.id==companyid))).one()
             
    results = session.exec(query).all()
    if not results:
        raise HTTPException(status_code=404, detail="User roles not found")

    userrole_list = [
        UserRoleRead(
            id=userrole.id,
            createdby=userrole.createdby,
            createdon=userrole.createdon,
            modifiedby=userrole.modifiedby,
            modifiedon=userrole.modifiedon,
            companyid=userrole.companyid,
            companyno= userrole.companyno,
            companyname=companyname,
            rolename=userrole.rolename,
            permissions=userrole.permissions,
            active=userrole.active
        )
        for userrole, companyname in results
    ]
    return { "user_rolelist": userrole_list,"total": totalcount}

@router.get("/getuserroleid/{userrole_id}", response_model=UserRoleRead )
def get_userrole_by_id(userrole_id: int, session: Session = Depends(get_session)):
    from routes.company import Company  # Import here to avoid circular import
    from routes.user_role import UserRole       
    query = select(UserRole, Company.companyname).join(Company, UserRole.companyid == Company.id, isouter=True).where(UserRole.id == userrole_id)
    result = session.exec(query).first()
    if not result:
        raise HTTPException(status_code=404, detail="User role not found")
    userrole, companyname = result
    return UserRoleRead(
        id=userrole.id,
        createdby=userrole.createdby,
        createdon=userrole.createdon,
        modifiedby=userrole.modifiedby,
        modifiedon=userrole.modifiedon,
        companyid=userrole.companyid,
        companyno=userrole.companyno,
        companyname=companyname,
        rolename=userrole.rolename,
        permissions=userrole.permissions,
        active=userrole.active
    )

@router.delete("/deleteuserrole/{userrole_id}")
def delete_userrole(userrole_id: int, session: Session = Depends(get_session)):    
   try: 
    db_userrole = session.get(UserRole, userrole_id)
    if not db_userrole:
        raise HTTPException(status_code=404, detail="User role not found.")
    session.delete(db_userrole)
    session.commit()
    return {"detail": "User role deleted successfully."}
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