
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
async def login(request: Request, db: Session = Depends(get_db)):
    try:
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
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }

        expiration = 30 if remember_me else 1
        access_token = jwt_manager.create_access_token(payload)
        refresh_token = jwt_manager.create_refresh_token(payload,days=expiration)

            
        log_activity(db, "auth", f"User {email} logged in", user.id)

        json_resp = JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "Login Successfuly",
                "data": payload
            }
        )
        json_resp.set_cookie(
            key="access_token",
            value=access_token,
            httponly=str_to_bool(getenv("HTTP_ONLY")),
            secure=str_to_bool(getenv("SECURE")),
            samesite="Lax",
            max_age=60 * 15
        )
        json_resp.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=str_to_bool(getenv("HTTP_ONLY")),
            secure=str_to_bool(getenv("SECURE")),
            samesite="Lax",
            max_age=60 * 60 * 24 * expiration
        )
        return json_resp
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@Auth.post("/pin")
@jwt_manager.requires_refresh
async def pin(request: Request, db: Session = Depends(get_db)):
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
            "id": decoded["id"],
            "name": decoded["name"],
            "email": email,
            "role": decoded["role"]
        }
        
        access_token = jwt_manager.create_access_token(payload)
    
        log_activity(db, "auth", f"User {email} pin login", decoded["id"])
        json_resp = JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "PIN Accepted",        
                "data": payload
            }
        )
        json_resp.set_cookie(
            key="access_token",
            value=access_token,
            httponly=str_to_bool(getenv("HTTP_ONLY")),
            secure=str_to_bool(getenv("SECURE")),
            samesite="Lax",
            max_age=60 * 15
        )
        return json_resp

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )
    
    
@Auth.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    try:
        token = request.cookies.get("refresh_token")
        token_bytes = token.encode('utf-8')
        decoded = jwt_manager.decode_token(token_bytes)
        email = decoded['email']
        log_activity(db, "auth", f"User {email} logged out", decoded["id"])

        json_resp = JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "Successfully logged out",
            }
        )
        json_resp.delete_cookie("refresh_token")
        json_resp.delete_cookie("access_token")
        return json_resp
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
@Auth.post("/logout-all")
async def logout_and_clear_all(response: Response):
    response.headers["Clear-Site-Data"] = '"cookies"'
    return {"message": "All cookies have been cleared by the browser"}

def _get_current_admin(request: Request) -> dict:
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    decoded = jwt_manager.decode_token(token.encode("utf-8"))
    if decoded.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return decoded

@Auth.get("/profile")
@jwt_manager.requires_refresh
@jwt_manager.requires_access
async def get_profile(request: Request, db: Session = Depends(get_db)):
    try:
        token = request.cookies.get("refresh_token")
        decoded = jwt_manager.decode_token(token.encode("utf-8"))
        user = db.query(Users).filter(Users.id == decoded["id"]).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "Profile retrieved successfully",
                "data": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@Auth.patch("/profile")
@jwt_manager.requires_refresh
@jwt_manager.requires_access
async def update_profile(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        name = data.get("name")
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing parameter: name")
        token = request.cookies.get("refresh_token")
        decoded = jwt_manager.decode_token(token.encode("utf-8"))
        user = db.query(Users).filter(Users.id == decoded["id"]).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user.name = name
        db.commit()
        db.refresh(user)
        log_activity(db, "auth", f"User {user.email} updated their name", user.id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "Profile updated successfully",
                "data": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@Auth.patch("/profile/password")
@jwt_manager.requires_refresh
@jwt_manager.requires_access
async def update_password_or_pin(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        password = data.get("password")
        pin = data.get("pin")
        if not password and not pin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing parameter: password or pin")
        token = request.cookies.get("refresh_token")
        decoded = jwt_manager.decode_token(token.encode("utf-8"))
        user = db.query(Users).filter(Users.id == decoded["id"]).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if password:
            user.password = password
        if pin:
            user.pin = pin
        db.commit()
        log_activity(db, "auth", f"User {user.email} updated password/pin", user.id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "Password/Pin updated successfully"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@Auth.get("/profile/user")
@jwt_manager.requires_refresh
@jwt_manager.requires_access
async def get_all_users(request: Request, db: Session = Depends(get_db)):
    try:
        decoded = _get_current_admin(request)
        users = db.query(Users).filter(Users.id != decoded["id"]).all()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "Users retrieved successfully",
                "data": [
                    {
                        "id": u.id,
                        "name": u.name,
                        "email": u.email,
                        "role": u.role,
                        "created_at": u.created_at.isoformat() if u.created_at else None,
                        "updated_at": u.updated_at.isoformat() if u.updated_at else None,
                    }
                    for u in users
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@Auth.delete("/profile/user/{user_id}")
@jwt_manager.requires_refresh
@jwt_manager.requires_access
async def delete_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    try:
        admin = _get_current_admin(request)
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        db.delete(user)
        db.commit()
        log_activity(db, "auth", f"Admin deleted user {user.email}", admin["id"])
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "User deleted successfully"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@Auth.post("/profile/user")
@jwt_manager.requires_refresh
@jwt_manager.requires_access
async def add_user(request: Request, db: Session = Depends(get_db)):
    try:
        admin = _get_current_admin(request)
        data = await request.json()
        name = data.get("name")
        email = data.get("email")
        role = data.get("role", "user")
        if not name or not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing parameter: name or email")
        existing = db.query(Users).filter(Users.email == email).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
        user = Users(
            name=name,
            email=email,
            password="hellofriend",
            pin="1234",
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        log_activity(db, "auth", f"Admin created user {user.email}", admin["id"])
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status_code": status.HTTP_201_CREATED,
                "detail": "User created successfully",
                "data": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@Auth.put("/profile/user/{user_id}")
@jwt_manager.requires_refresh
@jwt_manager.requires_access
async def reset_user_credentials(request: Request, user_id: int, db: Session = Depends(get_db)):
    try:
        admin = _get_current_admin(request)
        data = await request.json()
        reset_password = data.get("reset_password", False)
        reset_pin = data.get("reset_pin", False)
        if not reset_password and not reset_pin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Specify reset_password or reset_pin")
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if reset_password:
            user.password = "hellofriend"
        if reset_pin:
            user.pin = "1234"
        db.commit()
        log_activity(db, "auth", f"Admin reset credentials for user {user.email}", admin["id"])
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "User credentials reset successfully"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@Auth.put("/profile/user/{user_id}/role")
@jwt_manager.requires_refresh
@jwt_manager.requires_access
async def update_user_role(request: Request, user_id: int, db: Session = Depends(get_db)):
    try:
        admin = _get_current_admin(request)
        data = await request.json()
        role = data.get("role")
        if not role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing parameter: role")
        if role not in ("user", "admin"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role must be 'user' or 'admin'")
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user.role = role
        db.commit()
        log_activity(db, "auth", f"Admin changed role of user {user.email} to {role}", admin["id"])
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "User role updated successfully"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))