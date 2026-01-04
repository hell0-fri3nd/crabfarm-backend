from sqlalchemy import (
    Column, 
    Integer, 
    TIMESTAMP, 
    func,
    Enum,
    Index
)
from database import Base

class CrabLogs(Base):
    __tablename__ = "crab_logs"

    id         = Column(Integer, primary_key=True, index=True)
    crab_id    = Column(Integer, index=True)
    type       = Column(Enum("prediction", "actual", name="crab_logs_enum"),nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_crab_logs_id", "id"),
        Index("idx_crab_logs_type", "type"),
    )
    