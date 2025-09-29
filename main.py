from fastapi import FastAPI
from sqlmodel import SQLModel
from routes.db import engine
from routes import all_routers
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(
    title="Pro-Bill - Billing/Invoicing API",
    description="This is my custom FastAPI project with user management.",
    version="1.0.0",
    docs_url="/swagger",
    redoc_url="/redocs",
)

# CORS configuration
orgin = ["*"]   #["http://localhost:3000"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                   "http://127.0.0.1:8000"
                   ],  # Adjust as needed for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# Include all routers dynamically
for router in all_routers:
    app.include_router(router)

# Sample root endpoint
# @app.get("/")
# async def index():
#     return {"message": "Hi Kumar"}


 