from fastapi import FastAPI
from routers import Auth, Crabs, Settings, Gateway, Prediction, Control, WebSockets, ChatAI
from fastapi.middleware.cors import CORSMiddleware
from routers.activity_logs import Logs
from services import SchedulerManager
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from os import getenv

load_dotenv()
scheduler_service = SchedulerManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler_service.load_all()
    yield
    
app = FastAPI(lifespan=lifespan)


origins = [
    "http://localhost:7987",
    "http://192.168.1.19:7987"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=getenv("CORS_ORIGINS").split(","),  # or ["*"] for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(Auth)
app.include_router(Crabs)
app.include_router(Settings)
app.include_router(Gateway)
app.include_router(Prediction)
app.include_router(Control)
app.include_router(Logs)

app.include_router(WebSockets)

app.include_router(ChatAI)