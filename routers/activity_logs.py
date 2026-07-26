from fastapi import APIRouter, Depends,status, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import SessionLocal, engine
from models import Base, ActivityLogs, SensorLogs, Users
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
        query = select(ActivityLogs, Users.name).join(Users, ActivityLogs.user_id == Users.id, isouter=True)
        rows = db.execute(query).all()

        data = [
            {
                "id": log.id,
                "activity_type": log.activity_type,
                "description": log.description,
                "value": float(log.value) if log.value is not None else None,
                "user_id": log.user_id,
                "name": name,
                "created_at": log.created_at.isoformat(),
            }
            for log, name in rows
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

        token = request.cookies.get("access_token")
        decoded = jwt_manager.decode_token(token.encode("utf-8"))
        user_id = decoded.get("id")

        new_log = ActivityLogs(
            activity_type=activity_type,
            description=description,
            value=value,
            user_id=user_id
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
        
        
@Logs.get("/sensor")
@jwt_manager.requires_access
async def read_sensor_logs(request: Request, db: Session = Depends(get_db)):
    
    try:
        result = db.execute(select(SensorLogs))
        sensorLogs = result.scalars().all()
        
        data = [
            {
                "id": log.id,
                "sensor_type": log.sensor_type,
                "status": log.status,
                "value": float(log.value) if log.value is not None else None,
                "created_at": log.created_at.isoformat(),
            }
            for log in sensorLogs
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
     