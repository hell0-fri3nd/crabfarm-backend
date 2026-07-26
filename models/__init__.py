from .users import Users
from .scheduler_settings import SchedulerSettings
from .crab import Crab
from .crab_logs import CrabLogs
from .activity_logs import ActivityLogs
from .sensor_logs import SensorLogs
from .chat_sessions import ChatSession
from .chat_messages import ChatMessage
from .batch_crab import BatchCrab
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
