from fastapi import FastAPI
from sqlmodel import SQLModel
from routes.db  import engine,get_session
from routes.users import router as users_router



app = FastAPI(title="Pro-Bill - Billing/Invoicing API",        # 👈 Your name or project name
    description="This is my custom FastAPI project with user management.",
    version="1.0.0",
    docs_url="/swagger",          # 👈 Change URL for Swagger UI (default: /docs)
    redoc_url="/redocs"  )

# Create tables at startup
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# include routers

app.include_router(users_router)

# Sample root endpoint
# @app.get("/")
# async def index():
#     return {"message": "Hi Kumar"}


 