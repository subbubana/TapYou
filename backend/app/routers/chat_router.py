# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import List
# from uuid import UUID
# from datetime import datetime, date

# from app.models import User, ChatMessage
# from app.models import ChatInput, ChatResponse, ChatMessageRead
# from app.database import get_session
# from .auth_router import get_current_active_user, oauth2_scheme
# from app.services.agent_service import call_agent_on_message
# from app.crud import store_chat_message_in_db, get_chat_history_from_db

# from langchain_core.messages import HumanMessage, AIMessage

# router = APIRouter(
#     prefix="/chat",
#     tags=["Chat"],
# )

# async def get_formatted_chat_history(chat_id: UUID, session, limit: int = 10):
#     """Helper function to get formatted chat history for the agent."""
#     messages = await get_chat_history_from_db(chat_id, session, limit=limit)
#     formatted_history = []
#     for msg in messages:
#         if msg.is_user:
#             formatted_history.append(HumanMessage(content=msg.content))
#         else:
#             formatted_history.append(AIMessage(content=msg.content))
#     return formatted_history

# @router.post("/", response_model=ChatResponse, summary="Send a message to the AI agent")
# async def send_message(
#     chat_input: ChatInput,
#     current_user: User = Depends(get_current_active_user),
#     session = Depends(get_session),
#     token: str = Depends(oauth2_scheme)  # Extract the authentication token
# ):
#     print(f"=== CHAT POST ENDPOINT CALLED ===")
#     print(f"Current User ID: {current_user.user_id}")
#     print(f"Username: {current_user.username}")
#     print(f"Message: {chat_input.message}")
#     print(f"User Chat ID: {current_user.chat_id}")
#     print(f"Auth Token: {token[:20]}...")  # Log first 20 chars of token

#     user_chat_id = current_user.chat_id
#     if not user_chat_id:
#         print(f"User has no chat_id: {current_user.user_id}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="User does not have an associated chat_id."
#         )

#     print(f"Creating user message...")
#     user_chat_message = ChatMessage(
#         chat_id=user_chat_id,
#         is_user=True,
#         is_agent=False,
#         content=chat_input.message
#     )
    
#     try:
#         stored_user_message = await store_chat_message_in_db(user_chat_message, session)
#         print(f"User message stored successfully with ID: {stored_user_message.message_id}")
#     except Exception as e:
#         print(f"Failed to store user message: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to store user message: {str(e)}"
#         )

#     # print(f"Getting chat history for agent...")
#     # try:
#     #     chat_history_for_agent = await get_formatted_chat_history(user_chat_id, session, limit=10)
#     #     print(f"Chat history retrieved: {len(chat_history_for_agent)} messages")
#     # except Exception as e:
#     #     print(f"Failed to get chat history: {e}")
#         # Continue without chat history

#     print(f"Calling agent service with authentication token...")
#     agent_response_content = None
#     try:
#         # Create user context for the agent
#         user_context = {
#             "user_id": str(current_user.user_id),
#             "username": current_user.username,
#             "current_date": date.today().isoformat(),
#             "current_datetime": datetime.now().isoformat()
#         }
        
#         print(f"User context for agent: {user_context}")
        
#         agent_response_content = await call_agent_on_message(
#             user_input=chat_input.message,
#             chat_history=chat_history_for_agent,
#             chat_id=str(user_chat_id),
#             auth_token=token,  # Pass the authentication token to agent
#             user_context=user_context  # Pass user context to agent
#         )
#         print(f"Agent response received: {agent_response_content[:100]}...")
#     except Exception as e:
#         print(f"Agent service failed: {e}")
#         print(f"Agent error type: {type(e)}")
#         print(f"Agent error details: {str(e)}")
#         # Don't raise exception, just log the error
#         agent_response_content = "I'm sorry, I'm having trouble processing your request right now. Please try again later."

#     print(f"Creating agent message...")
#     agent_chat_message = ChatMessage(
#         chat_id=user_chat_id,
#         is_user=False,
#         is_agent=True,
#         content=agent_response_content
#     )
    
#     try:
#         stored_agent_message = await store_chat_message_in_db(agent_chat_message, session)
#         print(f"Agent message stored successfully with ID: {stored_agent_message.message_id}")
#     except Exception as e:
#         print(f"Failed to store agent message: {e}")
#         # Still return success since user message was stored
#         return ChatResponse(
#             agent_response=agent_response_content,
#             message_id=stored_user_message.message_id
#         )

#     print(f"=== CHAT POST ENDPOINT COMPLETED SUCCESSFULLY ===")
#     return ChatResponse(
#         agent_response=agent_response_content,
#         message_id=stored_agent_message.message_id
    # )

from fastapi import APIRouter, Depends, HTTPException, status
from app.models import User, ChatInput, ChatResponse, ChatMessage, ChatMessageRead
from app.database import get_session
from .auth_router import get_current_active_user, oauth2_scheme
from app.services.agent_service import call_agent_on_message
from app.crud import store_chat_message_in_db, get_chat_history_from_db


from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime, date

from app.models import User, ChatMessage

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/", response_model=ChatResponse)
async def chat(
    chat_input: ChatInput,
    current_user: User = Depends(get_current_active_user),
    session = Depends(get_session),
    token: str = Depends(oauth2_scheme)
):
    user_chat_id = current_user.chat_id
    if not user_chat_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User does not have an associated chat_id.")

    user_message = ChatMessage(
        chat_id=user_chat_id,
        is_user=True,
        is_agent=False,
        content=chat_input.message
    )

    print(f"Storing user message in database...", user_message)
    await store_chat_message_in_db(user_message, session)

    try:
        agent_reply = await call_agent_on_message(chat_input.message, auth_token=token)
    except Exception as e:
        agent_reply = "Sorry, an error occurred while processing the request."

    agent_message = ChatMessage(
        chat_id=user_chat_id,
        is_user=False,
        is_agent=True,
        content=agent_reply
    )
    await store_chat_message_in_db(agent_message, session)

    return ChatResponse(agent_response=agent_reply, message_id=agent_message.message_id)

@router.get("/history", response_model=List[ChatMessageRead], summary="Retrieve chat history for the authenticated user")
async def get_chat_history(
    current_user: User = Depends(get_current_active_user),
    session = Depends(get_session)
):
    print(f"=== CHAT HISTORY GET ENDPOINT CALLED ===")
    print(f"Current User ID: {current_user.user_id}")
    
    user_chat_id = current_user.chat_id
    if not user_chat_id:
        print(f"User has no chat_id: {current_user.user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an associated chat_id."
        )

    print(f"Fetching messages for chat_id: {user_chat_id}")
    try:
        db_messages = await get_chat_history_from_db(user_chat_id, session, limit=1000)
        print(f"Retrieved {len(db_messages)} messages from database")
        
        # Log message details for debugging
        for i, msg in enumerate(db_messages):
            print(f"Message {i+1}: ID={msg.message_id}, User={msg.is_user}, Content={msg.content[:50]}...")
        
        result = [ChatMessageRead.model_validate(msg) for msg in db_messages]
        print(f"=== CHAT HISTORY GET ENDPOINT COMPLETED SUCCESSFULLY ===")
        return result
    except Exception as e:
        print(f"Failed to get chat history: {e}")
        print(f"Error type: {type(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )

