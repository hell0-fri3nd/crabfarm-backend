from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from models import ChatSession, ChatMessage
from services.agents import AiAssistant
from datetime import datetime, timezone

def _ownership_filter(query, user_id: int | None):
    return query.filter(ChatSession.user_id == user_id)


class ChatManager:
    def create_session(self, db: Session, user_id: int | None = None) -> ChatSession:
        session = ChatSession(
            user_id=user_id,
            status="active"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_session(self, db: Session, session_id: str, user_id: int | None = None) -> ChatSession | None:
        return _ownership_filter(
            db.query(ChatSession).filter(ChatSession.id == session_id),
            user_id
        ).first()

    def list_sessions(self, db: Session, user_id: int | None = None, limit: int = 20, offset: int = 0) -> list[ChatSession]:
        return _ownership_filter(
            db.query(ChatSession), user_id
        ).order_by(desc(ChatSession.updated_at)).offset(offset).limit(limit).all()

    def get_messages(self, db: Session, session_id: str, limit: int = 30, offset: int = 0) -> tuple[list[ChatMessage], int]:
        total = db.query(func.count(ChatMessage.id)).filter(
            ChatMessage.session_id == session_id
        ).scalar()
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).offset(offset).limit(limit).all()
        return messages, total

    def send_message(
        self, db: Session, session_id: str, user_id: int | None = None,
        content: str | None = None
    ) -> dict | None:
        session = self.get_session(db, session_id, user_id)
        if not session:
            return None
        if session.status == "ended":
            return {"error": "session_ended"}

        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=content
        )
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        history = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.id != user_msg.id
        ).order_by(ChatMessage.created_at).all()

        response_text, _ = AiAssistant().chat_from_db(content, history)

        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=response_text
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)

        session.updated_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "message": "success",
            "user_message": {
                "id": user_msg.id,
                "content": user_msg.content,
                "created_at": user_msg.created_at.isoformat(),
            },
            "assistant_message": {
                "id": assistant_msg.id,
                "content": assistant_msg.content,
                "created_at": assistant_msg.created_at.isoformat(),
            }
        }

    def end_session(self, db: Session, session_id: str, user_id: int | None = None) -> bool:
        session = self.get_session(db, session_id, user_id)
        if not session:
            return False
        session.status = "ended"
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
        return True

    def delete_session(self, db: Session, session_id: str, user_id: int | None = None) -> bool:
        session = self.get_session(db, session_id, user_id)
        if not session:
            return False
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        db.delete(session)
        db.commit()
        return True
