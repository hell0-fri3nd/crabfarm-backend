from fastapi import FastAPI
from routers import Auth

app = FastAPI()

app.include_router(Auth)
