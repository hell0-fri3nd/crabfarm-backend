from .users import Users
from .calibration_settings  import CalibrationSettings
from .scheduler_settings import SchedulerSettings
from .crab import Crab
from .crab_logs import CrabLogs

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass 