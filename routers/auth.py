
from fastapi import APIRouter, Depends,status, HTTPException, Request,Response
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Users,Base
from services import JWTManager

Auth = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

Base.metadata.create_all(bind=engine)
jwt_manager = JWTManager()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@Auth.get("/")
async def read_root():
    return {"message": "Hello Friend! please proceed to given API templates"}

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

    # response.set_cookie(
    #     key="access_token",
    #     value=access_token,
    #     httponly=True,
    #     secure=True,          # use HTTPS in production
    #     samesite="Lax",
    #     max_age=60 * 15       # 15 minutes
    # )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age= 60 * 60 * 24 * expiration   # 1 day or 30 days
    )

    return {
        "status_code": status.HTTP_200_OK,
        "detail":"Password Accepted",
        "data": payload,
        "access_token": access_token
    }

@Auth.post("/pin")
@jwt_manager.requires_auth
async def pin(request: Request, response: Response, db: Session = Depends(get_db)):
    data = await request.json() 
    pin_password = data.get("pin_password")
    email = data.get("email")

    if not pin_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing parameter: PIN"
        )
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing parameter: email"
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
            detail="Incorrect password"
        )