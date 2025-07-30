from fastapi import APIRouter, Depends, BackgroundTasks, status
from sqlmodel import Session, select
from typing import List
from ..database import get_session
import app.models as models
from .auth_router import get_current_active_user
from app.services.agent_service import call_agent_on_message

router = APIRouter(
    prefix="/chat_history",
    tags=["Chat History"]
)

class UserChatMessageInput(models.SQLModel):
    message: str

class ChatResponse(models.SQLModel):
    user_message: models.ChatMessage
    agent_message: models.ChatMessage

@router.post(
    "/messages",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send chat message and get agent reply"
)
async def save_message(
    message_in: UserChatMessageInput,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_active_user)
):
    # Save the user message to DB
    user_msg = models.ChatMessage(
        chat_id=current_user.chat_id,
        is_user=True,
        is_agent=False,
        content=message_in.message
    )
    session.add(user_msg)
    session.commit()
    session.refresh(user_msg)

    # Load chat history for context (last 30 turns)
    chat_history = session.exec(
        select(models.ChatMessage)
        .where(models.ChatMessage.chat_id == current_user.chat_id)
        .order_by(models.ChatMessage.timestamp)
        .limit(30)
    ).all()

    # Call the agent (async)
    agent_reply_content = await call_agent_on_message(
        user_input=message_in.message,
        chat_history=chat_history,
        chat_id=current_user.chat_id
    )

    # Save the agent message to DB
    agent_msg = models.ChatMessage(
        chat_id=current_user.chat_id,
        is_user=False,
        is_agent=True,
        content=agent_reply_content
    )
    session.add(agent_msg)
    session.commit()
    session.refresh(agent_msg)

    return ChatResponse(user_message=user_msg, agent_message=agent_msg)

@router.get(
    "/messages",
    response_model=List[models.ChatMessage],
    summary="Get chat history for the authenticated user",
    description="Retrieves the full chat history for the current user based on their chat_id.", # Updated description
    operation_id="get_chat_history",
    responses={
        200: {"description": "Chat history retrieved successfully."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
    }
)
async def get_chat_history(
    *,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    **Endpoint to retrieve chat history for the authenticated user.**
    """
    chat_id = current_user.chat_id # Get the chat_id from the current user

    history = session.exec(
        select(models.ChatMessage)
        .where(models.ChatMessage.chat_id == chat_id) # Filter by chat_id
        .order_by(models.ChatMessage.timestamp)
        .limit(100)
    ).all()
    return history