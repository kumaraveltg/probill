from fastapi import APIRouter, HTTPException, Depends,status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta
from sqlmodel import Session, select,Field
from passlib.context import CryptContext
from pydantic import BaseModel
from .db import get_session  
from routes.company import Company

router = APIRouter(tags=["Login"])

class LoginRequest(BaseModel):
    project: str = Field(default="probill")
    companyno: str
    username: str
    password: str
    

class RefreshRequest(BaseModel):
    refresh_token: str

class GlobalParams(BaseModel):
    username: str | None = None
    companyno: str | None = None
    companyid: int | None = None
    companycode: str | None = None
global_params = GlobalParams()

SECRET_KEY = "mysecret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_token(data: dict, expires_minutes: int):
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode = {**data, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)




@router.post("/login")
def login( data:LoginRequest, session: Session = Depends(get_session)): 
    
    from .users import Users
    user = session.exec(select(Users).where(Users.username == data.username)).first()
    if not user or not verify_password(data.password, user.hpassword):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_token({"sub": user.username}, ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token = create_token({"sub": user.username}, REFRESH_TOKEN_EXPIRE_MINUTES)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh")
def refresh_token(request: RefreshRequest):
    try:
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access = create_token({"sub": username}, ACCESS_TOKEN_EXPIRE_MINUTES)
    return {"access_token": new_access, "token_type": "bearer"}
 
def set_global_params(username: str, companyno: str, db: Session):
    # Fetch company details
    stmt = select(Company).where(Company.companyno == companyno)
    company = db.exec(stmt).first()
    
    if not company:
        raise ValueError("Invalid company number")

    # Store globally
    global_params.username = username
    global_params.companyno = companyno
    global_params.companyid = company.id
    global_params.companycode = company.companycode

    print(global_params.companyid) 
    return global_params
 
 
@router.post("/set_company")
def set_company(username: str, companyno: str, db: Session = Depends(get_session)):
    params = set_global_params(username, companyno, db)
    return {"status": "ok", "params": params.dict()}