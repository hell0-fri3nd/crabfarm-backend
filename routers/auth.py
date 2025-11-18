
from fastapi import APIRouter, Depends

Auth = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Define a GET endpoint at the root path "/"
@Auth.get("/")
async def read_root():
    return {"message": "Hello, Friend!"}