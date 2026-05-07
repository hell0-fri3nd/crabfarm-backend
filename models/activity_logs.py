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

class ActivityLogs(Base):
    __tablename__   = "activity_logs"
    id              = Column(Integer, primary_key=True, index=True)
    activity_type   = Column(Enum("sensors", "auth","crab_logs","scheduler", name="activity_logs_enum"),nullable=False)
    description     = Column(String(100), nullable=False)
    value           = Column(Numeric(10,2), nullable=True, server_default=text("0"))
    created_at      = Column(TIMESTAMP, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_activity_logs_id", "id"),
        Index("idx_activity_logs_type", "activity_type"),
    )
    