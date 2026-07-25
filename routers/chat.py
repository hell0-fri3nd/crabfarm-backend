import json
import logging
from fastapi import APIRouter, Depends, status, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, Users
from services.chat_manager import ChatManager
from services.jwt_manager import JWTManager
import jwt

logger = logging.getLogger(__name__)

ChatAI = APIRouter(prefix="/api/v1/ai/chat", tags=["AI Chat"])

Base.metadata.create_all(bind=engine)
chat_manager = ChatManager()
jwt_manager = JWTManager()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def resolve_identity(request: Request, db: Session) -> int | None:
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = jwt_manager.decode_token(token)
            email = payload.get("email")
            if email:
                user = db.query(Users).filter(Users.email == email).first()
                if user:
                    return user.id
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, Exception):
            pass

    return None

@ChatAI.post("/sessions")
@jwt_manager.requires_access
async def create_session(request: Request, db: Session = Depends(get_db)):
    try:
        user_id = resolve_identity(request, db)
        session = chat_manager.create_session(db, user_id)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status_code": status.HTTP_201_CREATED,
                "detail": "Session created",
                "data": {
                    "id": session.id,
                    "user_id": session.user_id,
                    "status": session.status,
                    "created_at": session.created_at.isoformat(),
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create session")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Failed to create session",
                "data": {}
            }
        )

@ChatAI.get("/sessions/{session_id}")
@jwt_manager.requires_access
async def get_session(
    request: Request,
    session_id: str,
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    try:
        user_id = resolve_identity(request, db)
        session = chat_manager.get_session(db, session_id, user_id)
        if not session:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Session not found",
                    "data": {}
                }
            )
        messages, total = chat_manager.get_messages(
            db, session_id, limit=limit, offset=offset
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "Success",
                "data": {
                    "id": session.id,
                    "user_id": session.user_id,
                    "status": session.status,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "messages": [
                        {
                            "id": m.id,
                            "role": m.role,
                            "content": m.content,
                            "created_at": m.created_at.isoformat(),
                        }
                        for m in messages
                    ],
                    "pagination": {
                        "limit": limit,
                        "offset": offset,
                        "total": total,
                        "remaining": max(0, total - (offset + len(messages)))
                    }
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get session")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Failed to get session",
                "data": {}
            }
        )


@ChatAI.post("/sessions/{session_id}/messages")
@jwt_manager.requires_access
async def send_message(
    request: Request, session_id: str, db: Session = Depends(get_db)
):
    try:
        
        body = await request.json()
        content = body.get("content")
        client_message_id = body.get("client_message_id")
        
        user_id = resolve_identity(request, db)
        
        if not content:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Missing content",
                    "data": {}
                }
            )

        result = chat_manager.send_message(
            db, session_id, user_id, content, client_message_id
        )

        if result is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Session not found",
                    "data": {}
                }
            )

        if isinstance(result, dict) and result.get("error") == "session_ended":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Session has ended",
                    "data": {}
                }
            )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status_code": status.HTTP_201_CREATED,
                "detail": "Message sent",
                "data": result
            }
        )
    except HTTPException:
        raise
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "detail": "Invalid JSON body",
                "data": {}
            }
        )
    except Exception as e:
        logger.exception("Failed to send message")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Failed to send message",
                "data": e.__dict__
            }
        )


@ChatAI.patch("/sessions/{session_id}/end")
async def end_session(request: Request, session_id: str, db: Session = Depends(get_db)):
    try:
        user_id = resolve_identity(request, db)
        success = chat_manager.end_session(db, session_id, user_id)
        if not success:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Session not found",
                    "data": {}
                }
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "Session ended"
            }
        )
    except HTTPException:
        raise
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "detail": "Invalid JSON body",
                "data": {}
            }
        )
    except Exception as e:
        logger.exception("Failed to send message")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Failed to send message",
                "data": {}
            }
        )


@ChatAI.delete("/sessions/{session_id}")
async def delete_session(request: Request, session_id: str, db: Session = Depends(get_db)):
    try:
        user_id = resolve_identity(request, db)
        success = chat_manager.delete_session(db, session_id, user_id)
        if not success:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Session not found",
                    "data": {}
                }
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "detail": "Session deleted"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete session")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Failed to delete session",
                "data": {}
            }
        )
