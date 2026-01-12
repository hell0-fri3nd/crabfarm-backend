
from fastapi import APIRouter, Depends,status, HTTPException, Request,Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from database import SessionLocal, engine
from models import Crab,CrabLogs, Base
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
    
    try:
        result = db.execute(select(Crab))
        crabs = result.scalars().all()
        
        data = [
            {
                "id": crab.id,
                "name": crab.name,
                "group_by": crab.group_by,
            }
            for crab in crabs
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

@Crabs.post("/logs")
@jwt_manager.requires_access
async def insert_logs(request: Request, db: Session = Depends(get_db)):
    
    try:
        data    = await request.json()  
        crab_id = data.get("crab_id")
        type    = data.get("type")
        width   = data.get("width")
        weight  = data.get("width")
        
        
        new_log = CrabLogs(
            crab_id=crab_id,
            type=type,   # must match Enum values
            width=width,
            weight=weight
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status_code": status.HTTP_201_CREATED,
                "detail": "Crab log inserted successfully"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
    )


@Crabs.get("/logs/{log_type}/{crab_id}/") 
@jwt_manager.requires_access
async def view_logs(log_type: str, crab_id: int, request: Request, db: Session = Depends(get_db)): 
    
    try:
        
        query = select(
            CrabLogs, Crab
        ).join(Crab, CrabLogs.crab_id == Crab.id)
        
        # OR conditions
        conditions = []
        if crab_id is not None:
            conditions.append(CrabLogs.crab_id == crab_id)
        if log_type  is not None:
            conditions.append(CrabLogs.type == log_type)
        
        if conditions:
            query = query.where(or_(*conditions))
            
        crab_logs = db.execute(query).all()  # returns list of (CrabLogs, Crab)

        if not crab_logs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No logs found matching criteria")
    
        data = [
            {
                "log_id": log.id,
                "crab_id": log.crab_id,
                "type": log.type,
                "width": float(log.width),
                "weight": float(log.weight),
                "created_at": log.created_at.isoformat(),
                "crab_name": crab.name
            }
            for log, crab in crab_logs
        ]
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "Logs fetched successfully",
                "data": data
            }
        )
                
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@Crabs.get("/logs/{log_type}") 
@jwt_manager.requires_access
async def view_all_logs(log_type: str, request: Request, db: Session = Depends(get_db)): 
    
    try:
        
        query = select(CrabLogs, Crab).join(Crab, CrabLogs.crab_id == Crab.id)
        
        # OR conditions
        conditions = []
        if log_type.lower() != "all":
            conditions.append(CrabLogs.type == log_type)
        
        if conditions:
            query = query.where(or_(*conditions))
            
        crab_logs = db.execute(query).all()  # returns list of (CrabLogs, Crab)

        if not crab_logs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No logs found matching criteria")
    
        data = [
            {
                "log_id": log.id,
                "crab_id": log.crab_id,
                "type": log.type,
                "width": float(log.width),
                "weight": float(log.weight),
                "created_at": log.created_at.isoformat(),
                "crab_name": crab.name
            }
            for log, crab in crab_logs
        ]
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "Logs fetched successfully",
                "data": data
            }
        )
                
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
