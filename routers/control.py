from fastapi import APIRouter, Depends, Request, status, HTTPException
from fastapi.responses import JSONResponse

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