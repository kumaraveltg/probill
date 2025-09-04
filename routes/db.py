from sqlmodel import SQLModel,create_engine,Session

DATABASE_URL = ("postgresql://probill:log@127.0.0.1:5432/postgres")
engine = create_engine(DATABASE_URL,echo=False)
def get_session():
    with Session(engine) as session:
       yield session
