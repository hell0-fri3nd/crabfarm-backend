
from fastapi import APIRouter, Depends,status, HTTPException, Request,Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import SessionLocal, engine
from models import Crab,Base
from services import JWTManager

Crabs = APIRouter(prefix="/api/v1/crabs", tags=["Crab Management"])

Base.metadata.create_all(bind=engine)
jwt_manager = JWTManager()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@Crabs.get("/")
@jwt_manager.requires_access
async def read_root(request: Request, db: Session = Depends(get_db)):
    result = db.execute(select(Crab))
    crabs = result.scalars(). all()
    return {"data": crabs}
