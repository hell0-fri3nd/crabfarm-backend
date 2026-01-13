
from fastapi import APIRouter, Depends,status, HTTPException, Request,Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, desc
from database import SessionLocal, engine
from models import Crab,SchedulerSettings, Base
from services import JWTManager

Settings = APIRouter(prefix="/api/v1/settings", tags=["Settings"])

Base.metadata.create_all(bind=engine)
jwt_manager = JWTManager()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@Settings.get("/schedules")
@jwt_manager.requires_access
async def read_schedules(request: Request, db: Session = Depends(get_db)):
    
    try:
        result = db.execute(select(SchedulerSettings).order_by(desc(SchedulerSettings.created_at)))
        schedules = result.scalars().all()
        
        data = [
            {   
                "id": sched.id,
                "type": sched.type,
                "scheduler_type": sched.scheduler_type,
                "hour": sched.hour,
                "seconds": sched.seconds,
                "is_enabled": sched.is_enabled
            }
            for sched in schedules
        ]
                
        return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status_code": status.HTTP_200_OK,
                    "detail": "Success",
                    "data": data
                }
            )   

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
