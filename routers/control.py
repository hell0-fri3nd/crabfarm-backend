from fastapi import APIRouter, Depends, Request, status, HTTPException
from fastapi.responses import JSONResponse
from models.scheduler_settings import SchedulerSettings

from sqlalchemy.orm import Session
from sqlalchemy import select
from services import ESP32Config,JWTManager,SchedulerManager

from database import SessionLocal


Control = APIRouter(prefix="/api/v1/controls", tags=["ESP32 Controller"])
jwt_manager = JWTManager()
get_esp32_client = ESP32Config()
scheduler_manager = SchedulerManager()
        
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@Control.get("/status")
@jwt_manager.requires_access
async def get_esp_status(request: Request):
    try:
        
        result = get_esp32_client.get_system_state()
        data = result if 'error' not in result else []
        status_code = status.HTTP_200_OK if 'error' not in result else status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(
            status_code=status_code,
            content={
                "status_code": status_code,
                "detail": data
            }
        )
        
    except:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                   content={
                    "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                    "detail": "ESP32 is not reachable",
                    "data": {}
                }
        )
        
@Control.post('/start')
@jwt_manager.requires_access
async def start_feeding(request: Request):
    
    result = get_esp32_client.start_feeding()
    message = result if 'error' not in result else result['error']
    status_code = status.HTTP_200_OK if 'error' not in result else status.HTTP_500_INTERNAL_SERVER_ERROR     
          
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status_code": status_code,
            "detail": message
        }
    )
    
@Control.post('/stop')
@jwt_manager.requires_access
async def stop_feeding(request: Request):  
    
    result = get_esp32_client.stop_feeding()
    message = "Feeding process stopped" if 'error' not in result else result['error']
    status_code = status.HTTP_200_OK if 'error' not in result else status.HTTP_500_INTERNAL_SERVER_ERROR    
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status_code": status_code,
            "detail": message
        }
    )
    
@Control.post('/pause')
@jwt_manager.requires_access
async def pause_feeding(request: Request):  
    
    result = get_esp32_client.pause_feeding()
    message = "Feeding process paused" if 'error' not in result else result['error']
    status_code = status.HTTP_200_OK if 'error' not in result else status.HTTP_500_INTERNAL_SERVER_ERROR    
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status_code": status_code,
            "detail": message
        }
    )

@Control.get('/dispensers')
@jwt_manager.requires_access
async def get_dispensers(request: Request):
    
    result = get_esp32_client.get_dispenser_states()
    data = result if 'error' not in result else []
    status_code = status.HTTP_200_OK if 'error' not in result else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status_code": status_code,
            "detail": data
        }
    )


@Control.post('/dispensers/{index}')
@jwt_manager.requires_access
async def set_dispenser(index: int,request: Request):
    
    if not 0 <= index < 25:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "detail": "Invalid dispenser index"
            }
        )
    
    result = get_esp32_client.set_dispenser_state(index, True)
    message = result if 'error' not in result else result['error']
    status_code = status.HTTP_200_OK if 'error' not in result else status.HTTP_500_INTERNAL_SERVER_ERROR     
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status_code": status_code,
            "detail": message
        }
    )

    
@Control.post('/schedule')
@jwt_manager.requires_access
async def insert_schedule( request: Request, db: Session = Depends(get_db)):
    try:
        
        data            = await request.json()  
        type            = data.get("type")
        scheduler_type  = data.get("scheduler_type")
        hour            = data.get("hour")
        seconds         = data.get("seconds")
        is_enabled      = data.get("is_enabled")
        
        token = request.cookies.get("refresh_token")
        token_bytes = token.encode('utf-8')
        decoded = jwt_manager.decode_token(token_bytes)
        
        insert_scheduler = SchedulerSettings(
            type=type,
            scheduler_type=scheduler_type,
            hour=hour,
            seconds=seconds,
            is_enabled=is_enabled,
            created_by=decoded["name"]
        )
        db.add(insert_scheduler)
        db.commit()
        db.refresh(insert_scheduler)
        print("Inserted Schedule ID:", insert_scheduler.id)
        scheduler_manager.sync_job(insert_scheduler)
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status_code": status.HTTP_201_CREATED,
                "detail": "New Schedule inserted successfully"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@Control.get('/schedule')
@jwt_manager.requires_access
async def get_schedules(request: Request, db: Session = Depends(get_db)):
    try:
        
        result = db.execute(select(SchedulerSettings))
        schedules = result.scalars().all()
        
        data = [
            {
                "id": schedule.id,
                "type": schedule.type,
                "scheduler_type": schedule.scheduler_type,
                "hour": schedule.hour,
                "seconds": schedule.seconds,
                "is_enabled": schedule.is_enabled
            }
            for schedule in schedules
        ]
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "Schedules retrieved successfully",
                "data": data
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@Control.patch('/schedule')
@jwt_manager.requires_access
async def update_schedule(request: Request, db: Session = Depends(get_db)):
    try:
        
        data            = await request.json()  
        id              = data.get("id")
        is_enabled      = data.get("is_enabled")
        result = db.execute(select(SchedulerSettings).where(SchedulerSettings.id == id))
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Schedule not found"
                }
            )
            
        schedule.is_enabled = is_enabled
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