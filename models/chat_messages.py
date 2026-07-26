from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func, Enum, Index
from database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id         = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    role       = Column(Enum("user", "assistant", name="chat_role_enum"), nullable=False)
    content    = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_chat_messages_session_id", "session_id"),
    )
