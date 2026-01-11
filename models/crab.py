from sqlalchemy import Column, Integer, String, DateTime, func
from database import Base

class Crab(Base):
    __tablename__ = "crab"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(50), unique=True, nullable=False)
    group_by   = Column(String(50), nullable=False)

    