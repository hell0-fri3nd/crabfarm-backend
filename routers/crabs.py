from fastapi import APIRouter, Depends,status, HTTPException, Request,Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from database import SessionLocal, engine
from models import Crab, CrabLogs, Base, ActivityLogs, BatchCrab
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
        
def log_activity(db, activity_type, description,user_id):
    
    log = ActivityLogs(
        activity_type=activity_type,
        description=description,
        user_id=user_id
    )

    db.add(log)
    db.commit()
    db.refresh(log)
    return log

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

@Crabs.get("/batch")
@jwt_manager.requires_access
async def get_batches(request: Request, db: Session = Depends(get_db)):
    try:
        result = db.execute(select(BatchCrab))
        batches = result.scalars().all()

        data = [
            {
                "id": b.id,
                "user_id": b.user_id,
                "description": f"BATCH-{b.id}",
            }
            for b in batches
        ]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "Success",
                "data": data,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@Crabs.post("/batch")
@jwt_manager.requires_access
async def create_batch(request: Request, db: Session = Depends(get_db)):
    try:
        token = request.cookies.get("access_token")
        decoded = jwt_manager.decode_token(token.encode("utf-8"))
        email = decoded["email"]
        user_id = decoded["id"]

        new_batch = BatchCrab(user_id=user_id)
        db.add(new_batch)
        db.commit()
        db.refresh(new_batch)
        
        log_activity(db, "crab_logs", f"User {email} created a new batch with ID {new_batch.id}", user_id)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status_code": status.HTTP_201_CREATED,
                "detail": "Batch created successfully",
                "data": {
                    "id": new_batch.id,
                    "user_id": new_batch.user_id,
                    "description": f"BATCH-{new_batch.id}",
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
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
        
        token = request.cookies.get("access_token")
        token_bytes = token.encode('utf-8')
        
        decoded = jwt_manager.decode_token(token_bytes)
        email = decoded['email']
        user_id = decoded["id"]
        log_activity(db, "crab_logs", f"User {email} inserted crab log for crab ID {crab_id}", user_id)

        new_log = CrabLogs(
            crab_id=crab_id,
            type=type,
            width=width,
            weight=weight,
            user_id=user_id
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
async def view_all_logs(log_type: str, request: Request, page: int = 1, limit: int = 70, db: Session = Depends(get_db)): 
    
    try:
        
        query = select(CrabLogs, Crab).join(Crab, CrabLogs.crab_id == Crab.id)
        
        conditions = []
        if log_type.lower() != "all":
            conditions.append(CrabLogs.type == log_type)
        
        if conditions:
            query = query.where(or_(*conditions))
        
        # offset = (page - 1) * limit
        # query = query.offset(offset).limit(limit)
        
        crab_logs = db.execute(query).all()

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
                "group_by": crab.group_by,
                "batch_id": crab.batch_id,
                "batch_description": f"BATCH-{crab.batch_id}" if crab.batch_id else None
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
                "crab_name": crab.name,
                "group_by": crab.group_by,
                "batch_id": crab.batch_id,
                "batch_description": f"BATCH-{crab.batch_id}" if crab.batch_id else None
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

