from sqlalchemy import Column, Integer, TIMESTAMP, func, Enum, Boolean, text
from database import Base


class SchedulerSettings(Base):
    __tablename__ = "scheduler_settings"

    id             = Column(Integer, primary_key=True, index=True)
    type           = Column(Enum("feeding", "valve", name="scheduler_type_enum"), nullable=False)
    scheduler_type = Column(Enum('daily', 'weekly', 'monthly', 'custom', name="scheduler_enum"), nullable=False)
    hour           = Column(Integer, server_default=text("0"))
    seconds        = Column(Integer, server_default=text("0"))
    is_enabled     = Column(Boolean, nullable=False, server_default=text("false"))
    created_at     = Column(TIMESTAMP, nullable=False, server_default=func.now())
    user_id        = Column(Integer, nullable=False, index=True)
