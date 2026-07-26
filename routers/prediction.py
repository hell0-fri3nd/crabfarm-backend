from fastapi import APIRouter, Depends,status, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import insert, select
from database import SessionLocal, engine
from models import CrabLogs, ActivityLogs, Base
from services import JWTManager, CrabPrediction

Prediction = APIRouter(prefix="/api/v1/predictions", tags=["Crab Prediction"])
Base.metadata.create_all(bind=engine)
jwt_manager = JWTManager()
crab_prediction = CrabPrediction()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def log_activity(db, activity_type, description, user_id=None):
    log = ActivityLogs(
        activity_type=activity_type,
        description=description,
        user_id=user_id
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
        

@Prediction.get("/")
async def root():
    return {"status": "server running"}

@Prediction.get("/{crab_id}")
@jwt_manager.requires_access
async def prediction(crab_id: str,request: Request, db: Session = Depends(get_db)):
    try:
        result = db.execute(
            select(CrabLogs)
            .where(
                CrabLogs.crab_id == crab_id,
                CrabLogs.type == "actual"
            )
            .order_by(CrabLogs.created_at.desc())
            .limit(7)
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
                "detail": f"Predicted next 7 days successfully",
                "data": results
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
        
@Prediction.post("/{crab_id}")
@jwt_manager.requires_access
async def insert_prediction(crab_id: str,request: Request, db: Session = Depends(get_db)):
    
    try:
        
        token = request.cookies.get("access_token")
        token_bytes = token.encode('utf-8')
        decoded = jwt_manager.decode_token(token_bytes)
        email = decoded["email"]
        user_id = decoded["id"]
        
        data    = await request.json()  
        batch_id = data.get("batch_id")
        
        result = db.execute(
            select(CrabLogs)
            .where(
                CrabLogs.crab_id == crab_id,
                CrabLogs.type == "actual",
                CrabLogs.batch_id == batch_id
            )
            .order_by(CrabLogs.created_at.desc())
            .limit(7)
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
                "weight": float(weight),
                "type": "prediction",
                "user_id": user_id,
                "batch_id": batch_id
            }
            for  created_at, width, weight in crab_prediction.predict_next_days(data_list=data)
        ]
        
        min_date = min(result["created_at"] for result in results)
        max_date = max(result["created_at"] for result in results)
        
        existing = db.execute(
            select(CrabLogs.id).where(
                CrabLogs.crab_id == crab_id,
                CrabLogs.created_at >= min_date,
                CrabLogs.created_at <= max_date,
                CrabLogs.type == "prediction"
            ).limit(1)
        ).first()
        
        if existing:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status_code": status.HTTP_200_OK,
                    "detail":  "this crab already has predictions for the next 7 days"
                }
            )
        
        stmt = insert(CrabLogs).values(results)
        db.execute(stmt)
        db.commit()
        
        log_activity(db, "crab_logs", f"User {email} inserted prediction for crab ID {crab_id}", user_id)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status_code": status.HTTP_201_CREATED,
                "detail": f"{len(results)} crab logs inserted successfully"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )