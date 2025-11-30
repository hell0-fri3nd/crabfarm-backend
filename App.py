from fastapi import FastAPI
from routers import Auth
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:7987",
    "http://192.168.100.11:7987"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(Auth)
