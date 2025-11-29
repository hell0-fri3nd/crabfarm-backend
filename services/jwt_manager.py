from jwt import ExpiredSignatureError, InvalidTokenError
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from os import getenv
from fastapi import Request, HTTPException, status
from functools import wraps

class JWTManager:
    def __init__(self):
        load_dotenv()
        self.__secret_key = getenv("JWT_SECRET_KEY")
        self.__algorithm  = getenv("JWT_ALGORITHM")

    def create_access_token(self, data: dict, expire_minutes = 15) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, self.__secret_key, algorithm=self.__algorithm)
        return token

    def decode_token(self, token: str) -> dict:
        """Decodes the JWT token and returns the payload."""
        try:
            payload = jwt.decode(token, self.__secret_key, algorithms=[self.__algorithm])
            
            return payload
        
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid token"
            )

    def create_refresh_token(self, data: dict, days = 1) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=days)
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, self.__secret_key, algorithm=self.__algorithm)
        return token
    
    def requires_access(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if not request:
                raise HTTPException(status_code=500, detail="Request object not found for auth check")

            # Extract token from the Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    detail="Authorization header missing or invalid format (Bearer token required)"
                )
            
            token = auth_header.split(" ")[1]
            try:
                self.decode_token(token)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid or expired token: {str(e)}"
                )
    
            return await func(*args, **kwargs)
        
        return wrapper
    
    def requires_refresh(self, func):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            
            request: Request = kwargs.get("request") or args[0]
            refresh_token = request.cookies.get("refresh_token")
            
            if not refresh_token:
                raise HTTPException(status_code=401, detail="Refresh token missing")


            try:
                payload = self.decode_token(refresh_token)
                # Token is valid and not expired
            except ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Refresh token expired")
            except InvalidTokenError:
                raise HTTPException(status_code=401, detail="Invalid refresh token")


            return await func(*args, **kwargs)
        
        return wrapper