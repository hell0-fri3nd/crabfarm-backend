from sqlalchemy import Column, Integer, String, DateTime, func
from database import Base
from sqlalchemy.orm import Session
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Users(Base):
    __tablename__ = "users"  # <<< REQUIRED

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    pin = Column(String(100), nullable=False)
    roles = Column(String(255), nullable=False)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    