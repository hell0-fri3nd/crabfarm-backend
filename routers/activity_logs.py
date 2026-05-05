from fastapi import APIRouter, Depends,status, HTTPException, Request,Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from database import SessionLocal, engine
from models import Crab,CrabLogs, Base, ActivityLogs
from services import JWTManager, CrabPrediction

Logs = APIRouter(prefix="/api/v1/logs", tags=["Activity Logs"])

Base.metadata.create_all(bind=engine)
jwt_manager = JWTManager()
crab_prediction = CrabPrediction()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@Logs.get("/")
@jwt_manager.requires_access
async def read_root(request: Request, db: Session = Depends(get_db)):
    
    try:
        result = db.execute(select(ActivityLogs))
        logs = result.scalars().all()
        
        data = [
            {
                "id": log.id,
                "activity_type": log.activity_type,
                "description": log.description,
                "value": log.value,
                "created_at": log.created_at,
            }
            for log in logs
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
        
@Logs.post("/")
@jwt_manager.requires_access
async def insert_logs(request: Request, db: Session = Depends(get_db)):
    
    try:
        data            = await request.json()  
        activity_type   = data.get("activity_type")
        description     = data.get("description")
        value           = data.get("value")
          
        new_log = ActivityLogs(
            activity_type=activity_type,
            description=description,
            value=value
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status_code": status.HTTP_201_CREATED,
                "detail": "Activity log inserted successfully"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
    )