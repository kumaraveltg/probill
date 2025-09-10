from sqlmodel import SQLModel,create_engine,Session
from sqlalchemy.orm import sessionmaker,declarative_base
import psycopg2 

DATABASE_URL = ("postgresql://probill:log@127.0.0.1:5432/postgres")
engine = create_engine(DATABASE_URL,echo=False)
def get_session():
    with Session(engine) as session:
       yield session
Base = declarative_base()