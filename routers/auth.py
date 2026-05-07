
from fastapi import APIRouter, Depends,status, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Users,Base
from models.activity_logs import ActivityLogs
from services import JWTManager
from dotenv import load_dotenv
from os import getenv

Auth = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

Base.metadata.create_all(bind=engine)
jwt_manager = JWTManager()
load_dotenv()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def str_to_bool(value: str | None) -> bool:
    return value.lower() == "True" if value else False

def log_activity(db, activity_type, description):
    log = ActivityLogs(
        activity_type=activity_type,
        description=description
    )

    db.add(log)
    db.commit()
    db.refresh(log)
    return log

@Auth.get("/")
async def read_root():
    return {"message": "Hello Friend! please proceed to given API templates"}

@Auth.get("/status")
@jwt_manager.requires_refresh
@jwt_manager.requires_access
async def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    return JSONResponse(
        status_code=status.HTTP_200_OK,
               content={
                "status_code": status.HTTP_200_OK,
                "detail": "Token is valid",
            }
    )

@Auth.post("/login")
async def login(request: Request, response: Response, db: Session = Depends(get_db)):
    data = await request.json()  
    email = data.get("email")
    password = data.get("password")
    remember_me = data.get("remember_me")
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing parameter: email"
        )

    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing parameter: password"
        )
    
    user = db.query(Users).filter(Users.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    if not password == user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    
    payload = {
        "name": user.name,
        "email": user.email,
        "role": user.roles
    }

    expiration = 30 if remember_me else 1
    access_token = jwt_manager.create_access_token(payload)
    refresh_token = jwt_manager.create_refresh_token(payload,days=expiration)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=str_to_bool(getenv("HTTP_ONLY")),
        secure=str_to_bool(getenv("SECURE")),          # use HTTPS in production
        samesite="Lax",
        max_age=60 * 15       # 15 minutes
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=str_to_bool(getenv("HTTP_ONLY")),
        secure=str_to_bool(getenv("SECURE")),         
        samesite="Lax",
        max_age= 60 * 60 * 24 * expiration   # 1 day or 30 days
    )
    
    log_activity(db, "auth", f"User {email} logged in")

    return {
        "status_code": status.HTTP_200_OK,
        "detail":"Login Successfuly",
        "data": payload
    }

@Auth.post("/pin")
@jwt_manager.requires_refresh
async def pin(request: Request, response: Response, db: Session = Depends(get_db)):

    try:
        data = await request.json() 

        token = request.cookies.get("refresh_token")
        token_bytes = token.encode('utf-8')
        
        decoded = jwt_manager.decode_token(token_bytes)
        email = decoded['email']
        pin_password = data.get("pin")

        if not pin_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing parameter: PIN"
            )
        
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        
        if not pin_password == user.pin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect pin"
            )
        
        payload = {
            "name": decoded["name"],
            "email": email,
            "role": decoded["role"]
        }
        
        access_token = jwt_manager.create_access_token(payload)
    
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=str_to_bool(getenv("HTTP_ONLY")),
            secure=str_to_bool(getenv("SECURE")),    
            samesite="Lax",
            max_age=60 * 15       # 15 minutes
        )
        log_activity(db, "auth", f"User {email} pin login")
        return {
            "status_code": status.HTTP_200_OK,
            "detail":"PIN Accepted",        
            "data": payload
        },

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )
    
    
@Auth.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    
    token = request.cookies.get("refresh_token")
    token_bytes = token.encode('utf-8')
    decoded = jwt_manager.decode_token(token_bytes)
    email = decoded['email']
    log_activity(db, "auth", f"User {email} logged out")

    response.delete_cookie("refresh_token")
    response.delete_cookie("access_token")
    
    return {
        "status_code": status.HTTP_200_OK,
        "detail": "Successfully logged out",
    }
    
@Auth.post("/logout-all")
async def logout_and_clear_all(response: Response):
    # This header instructs the browser to clear all cookies for this origin
    response.headers["Clear-Site-Data"] = '"cookies"'
    return {"message": "All cookies have been cleared by the browser"}