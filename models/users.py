from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from database import Base


class Users(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(150), nullable=False)
    email      = Column(String(254), unique=True, nullable=False, index=True)
    password   = Column(String(60), nullable=False)
    pin        = Column(String(60), nullable=False)
    role       = Column(String(6), nullable=False)

    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())
