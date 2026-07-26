from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, func, Index
from database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id         = Column(String(36), primary_key=True, default=generate_uuid)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status     = Column(Enum("active", "ended", name="chat_status_enum"), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("user_id", "user_id"),
    )
