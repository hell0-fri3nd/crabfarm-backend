
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Users,Base

Auth = APIRouter(prefix="/api/v1/auth", tags=["auth"])

Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define a GET endpoint at the root path "/"
@Auth.get("/")
async def read_root():
    return {"message": "Hello, Friend!"}

@Auth.get("/test")
async def get_all_users(db: Session = Depends(get_db)):
    users = db.query(Users).all()
    return db.query(Users).all()
