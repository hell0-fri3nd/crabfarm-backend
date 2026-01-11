from sqlalchemy import Column, Integer, String, DateTime, func, Numeric,text
from database import Base

class Crab(Base):
    __tablename__ = "crab"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(50), unique=True, nullable=False)
    width      = Column(Numeric(10,2), nullable=False, server_default=text("0"))
    weight     = Column(Numeric(10,2), nullable=False, server_default=text("0"))
    group_by   = Column(String(50), nullable=False)

    