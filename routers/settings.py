
from fastapi import APIRouter, Depends,status, HTTPException, Request,Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, desc
from database import SessionLocal, engine
from models import SchedulerSettings, Base
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

@Settings.post("/schedules")
@jwt_manager.requires_access
async def post_schedules(request: Request, db: Session = Depends(get_db)):
    
    try:
        
        data    = await request.json()  
        type    = data.get("type")
        hour    = data.get("hour")
        seconds = data.get("seconds")
        is_enabled = data.get("is_enabled")
        scheduler_type = data.get("scheduler_type")
        created_by = data.get("created_by")
        
        new_schedule = SchedulerSettings(
            type=type,
            hour=hour,
            seconds=seconds,
            is_enabled=is_enabled,
            scheduler_type=scheduler_type,
            created_by=created_by
        )
        db.add(new_schedule)
        db.commit()
        db.refresh(new_schedule)
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status_code": status.HTTP_201_CREATED,
                "detail": "New Schedules inserted successfully"
            }
        )   

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )   
        
@Settings.put("/schedules")
@jwt_manager.requires_access
async def put_schedules(request: Request, db: Session = Depends(get_db)):
    
    try:
        
        data    = await request.json()  
        schedule_id = data.get("id")
        
        if not schedule_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Schedule ID is required for update"
            )
        
        schedule = db.query(SchedulerSettings).filter(
            SchedulerSettings.id == schedule_id
        ).first()
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )
            
        # Update fields only if provided
        schedule.type = data.get("type", schedule.type)
        schedule.hour = data.get("hour", schedule.hour)
        schedule.seconds = data.get("seconds", schedule.seconds)
        schedule.is_enabled = data.get("is_enabled", schedule.is_enabled)
        schedule.scheduler_type = data.get("scheduler_type", schedule.scheduler_type)

        db.commit()
        db.refresh(schedule)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "Schedule updated successfully"
            }
        )   

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )   
        
@Settings.delete("/schedules/{schedule_id}", status_code=status.HTTP_200_OK)
@jwt_manager.requires_access
async def delete_schedules(schedule_id: int, request: Request, db: Session = Depends(get_db)):
    
    try:
        schedule = db.query(SchedulerSettings).filter(
                SchedulerSettings.id == schedule_id
            ).first()
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )
        
        db.delete(schedule)
        db.commit()
    
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "Schedule deleted successfully"
            }
        )   

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )