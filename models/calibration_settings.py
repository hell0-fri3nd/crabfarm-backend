from sqlalchemy import Column, Integer, String, DateTime, func,Numeric,text
from database import Base

class CalibrationSettings(Base):
    __tablename__ = "calibration_settings"

    id               = Column(Integer, primary_key=True, index=True)
    calibration_type = Column(String(50), unique=True, nullable=False, index=True)
    value            = Column(Numeric(10,2), nullable=False, server_default=text("0"))
    updated_at       = Column(DateTime, nullable=False, server_default=func.now())
    updated_by       = Column(String(150), nullable=False)