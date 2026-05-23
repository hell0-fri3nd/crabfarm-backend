from sqlalchemy import (
    Column, 
    Integer, 
    TIMESTAMP, 
    func,
    Enum,
    Index,
    Numeric,
    text,
    String
)
from database import Base

class SensorLogs(Base):
    __tablename__   = "sensor_logs"
    id              = Column(Integer, primary_key=True, index=True)
    sensor_type     = Column(Enum("temperature", "turbidity", "ph", "tds", "ammonium", "do", name="sensor_type_enum"), nullable=False)
    status          = Column(Enum("NORMAL", "WARNING", "DANGER", name="sensor_status_enum"), nullable=False)
    value           = Column(Numeric(10,2), nullable=True, server_default=text("0"))
    created_at      = Column(TIMESTAMP, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_sensor_logs_id", "id"),
        Index("idx_sensor_logs_type", "sensor_type"),
        Index("idx_sensor_logs_status", "status"),
    )