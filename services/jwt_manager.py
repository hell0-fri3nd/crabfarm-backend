import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from os import getenv

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
        payload = jwt.decode(token, self.__secret_key, algorithms=[self.__algorithm])
        return payload

    def create_refresh_token(self, data: dict, days = 1) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=days)
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, self.__secret_key, algorithm=self.__algorithm)
        return token