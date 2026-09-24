from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from . import models

from routers import hospitals, blood, icu, organs, equipment, admin

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Tech4Life API",
    description="Hospital Resource Management and Integration Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
          "https://tech4life-frontend.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hospitals.router)
app.include_router(blood.router)
app.include_router(icu.router)
app.include_router(organs.router)
app.include_router(equipment.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {
        "message": "Welcome to Tech4Life API",
        "status": "running"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}