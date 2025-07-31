from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from app.models import ChatMessage # Assuming models are defined

async def store_chat_message_in_db(message: ChatMessage, session: Session):
    session.add(message)
    session.commit()
    session.refresh(message)
    return message

async def get_chat_history_from_db(chat_id: UUID, session: Session, limit: int = 10) -> List[ChatMessage]:
    return session.query(ChatMessage).filter(ChatMessage.chat_id == chat_id).order_by(ChatMessage.timestamp.asc()).limit(limit).all()