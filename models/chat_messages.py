from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id                = Column(String(36), primary_key=True, default=generate_uuid)
    session_id        = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role              = Column(String(20), nullable=False)
    content           = Column(Text, nullable=False)
    client_message_id = Column(String(255), nullable=True, unique=True)
    created_at        = Column(DateTime, nullable=False, server_default=func.now())
