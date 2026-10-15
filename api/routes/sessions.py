from api.routes.authentication import get_current_admin
from api.schemas.message_schema import (
    ChatSessionOut,
    ChatSessionModel,
    ChatMessageModel,
    ChatSessionIn,
    RenameSessionRequest,
)
import json
from uuid import uuid4
from mongoengine import Q
from database.user import User
from datetime import datetime
from api.database.chat import ChatSession
from api.database.chat import ChatMessage
from fastapi import APIRouter, HTTPException, Query, Depends
from mongoengine import DoesNotExist
from database.chat import ChatMessage

session_router = APIRouter()


@session_router.get("/list")
async def list_sessions(
    user_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),  # frontend is passing page number!
    # days: Optional[int] = None,
    current_user: User = Depends(get_current_admin),
):
    """List active chat sessions based on user_id."""
    try:
        user = User.objects.get(id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        query = Q(user_id=user)

        total = ChatSession.objects(query).count()

        #  Convert page number to real skip offset
        real_offset = offset * limit

        sessions = (
            ChatSession.objects(query)
            .order_by("-last_activity")
            .skip(real_offset)
            .limit(limit)
        )

        session_list = [
            {
                "session_id": session.session_id,
                "user_id": str(session.user_id.id),
                "message_count": len(session.messages),
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "name": session.name,
            }
            for session in sessions
        ]

        if not session_list:
            return {"sessions": []}

        return {
            "sessions": session_list,
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@session_router.get("/messages-ids/{session_id}", response_model=list[str])
async def get_messages_ids(session_id: str):
    messages = ChatMessage.objects(session_id=session_id)
    if not messages:
        raise HTTPException(
            status_code=404, detail="No messages found for this session"
        )
    return [str(msg.id) for msg in messages]


@session_router.post("/", response_model=ChatSessionOut)
async def create_session(
    user_id: ChatSessionIn, current_user: User = Depends(get_current_admin)
):
    """Create a new chat session."""

    session_id = str(uuid4())
    session = ChatSession(
        session_id=session_id,
        name="New Chat",
        messages=[],
        user_id=user_id.user_id,
        created_at=datetime.now(),
        last_activity=datetime.now(),
    )
    session.save()

    session.update(set__last_activity=datetime.now())

    return ChatSessionOut(
        session_id=session.session_id,
        name=session.name,
        created_at=session.created_at,
        last_activity=session.last_activity,
    )


@session_router.get("/message-ids")
async def get_message_ids(session_id: str):
    chats = ChatMessage.objects(session_id=session_id)
    if not chats:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message_ids": [str(chat.id) for chat in chats]}


@session_router.delete("/{session_id}", status_code=200)
async def delete_session(
    session_id: str, current_user: User = Depends(get_current_admin)
):
    """Delete an existing chat session."""
    try:
        session = ChatSession.objects.get(session_id=session_id)
        session.delete()  # Delete the session and its messages
        return {"message": "Session deleted successfully"}
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Session not found")


@session_router.get("/{session_id}", response_model=ChatSessionModel)
async def get_session(
    session_id: str,
    skip: int = Query(0, ge=0, description="Number of most recent messages to skip"),
    limit: int = Query(
        20, gt=0, le=100, description="Maximum number of messages to return"
    ),
    # current_user: User = Depends(get_current_admin),
):
    """Get a chat session by session ID with reverse pagination (most recent first)."""
    try:
        session = ChatSession.objects.get(session_id=session_id)

        # Reverse the list of messages to start from the most recent
        reversed_messages = list(reversed(session.messages))

        # Apply pagination (skip most recent `skip`, then take `limit`)
        paginated_reversed = reversed_messages[skip : skip + limit]

        # Sort the paginated messages back to chronological order for UI display
        paginated_sorted = sorted(
            paginated_reversed, key=lambda m: getattr(m, "timestamp", datetime.now())
        )

        messages = [
            ChatMessageModel(
                session_id=session.session_id,
                message=msg.message,
                response=msg.response,
                timestamp=getattr(msg, "timestamp", datetime.now()),
                metadata=msg.metadata,
                message_id=str(msg.id),
            )
            for msg in paginated_sorted
        ]

        return ChatSessionModel(
            session_id=session.session_id,
            messages=messages,
            created_at=session.created_at,
            last_activity=session.last_activity,
        )
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@session_router.patch("/rename-session")
async def rename_session(
    data: RenameSessionRequest, current_user: User = Depends(get_current_admin)
):
    """Rename only the name field of a chat session."""
    session = ChatSession.objects(session_id=data.session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.name = data.name
    session.save()
    return {"message": "Session name updated successfully"}
