from fastapi import APIRouter, Depends,status, HTTPException, Request,Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from database import SessionLocal, engine
from models import Crab,CrabLogs, Base
from services import JWTManager, CrabPrediction

Crabs = APIRouter(prefix="/api/v1/crabs", tags=["Crab Management"])

Base.metadata.create_all(bind=engine)
jwt_manager = JWTManager()
crab_prediction = CrabPrediction()

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

@Crabs.get("/predict/{crab_id}") 
@jwt_manager.requires_access
async def predict(crab_id: str,request: Request, db: Session = Depends(get_db)):
    
    try:

        result = db.execute(
            select(CrabLogs)
            .where(
                CrabLogs.crab_id == crab_id,
                CrabLogs.type == "actual"
            )
            .order_by(CrabLogs.created_at.desc())
            .limit(5)
        )
        logs = result.scalars().all()
        
        if not logs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No logs found for prediction")
        
        data = [
            {
                "crab_id": log.crab_id,
                "created_at": (log.created_at).strftime('%Y-%m-%d %H:%M:%S'),
                "width": float(log.width),
                "weight": float(log.weight)
            }
            for log in logs
        ]
        
        results = [
            {
                "crab_id": crab_id,
                "created_at": created_at,
                "width": float(width),
                "weight": float(weight)
            }
            for  created_at, width, weight in crab_prediction.predict_next_days(data_list=data)
        ]
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": f"Predicted next 5 days successfully",
                "data": results
            }
        )
                
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
        
@Crabs.get("/{crab_group}")
@jwt_manager.requires_access
async def read_crabs_by_group(crab_group: str, request: Request, db: Session = Depends(get_db)):
    
    try:
        result = db.execute(select(Crab).where(Crab.group_by == crab_group))
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
        weight  = data.get("weight")
        
        
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
                "crab_name": crab.name,
                "group_by": crab.group_by
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

