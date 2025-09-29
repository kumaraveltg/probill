from fastapi import APIRouter, HTTPException, Depends,status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError 
from sqlmodel import Session, select 
from passlib.context import CryptContext
from pydantic import BaseModel
from .db import get_session  

# -------------------------------
# JWT settings
# -------------------------------
SECRET_KEY = "mysecret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    from routes.users import Users
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token") 
        user = session.exec(select(Users).where(Users.username == username)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
