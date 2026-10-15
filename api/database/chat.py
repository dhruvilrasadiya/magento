from mongoengine import (
    Document,
    StringField,
    ListField,
    ReferenceField,
    DictField,
    DateTimeField,
)
from .user import User
from typing import List, Dict
from datetime import datetime


class ChatMessage(Document):
    """Model for chat messages."""

    session_id = StringField(required=True)
    message = StringField(required=True)
    response = StringField(required=True)
    metadata = DictField(default={})
    timestamp = DateTimeField(default=datetime.now)

    meta = {
        "collection": "messages",  # Collection name in MongoDB
        "indexes": ["session_id"],  # Index for efficient query by session_id
    }

    def to_dict(self):
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "message": self.message,
            "response": self.response,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class ChatSession(Document):
    """Model for chat sessions."""

    session_id = StringField(required=True, unique=True)
    user_id = ReferenceField(User, required=True, reverse_delete_rule=2)
    name = StringField(default="New Chat")
    messages = ListField(ReferenceField(ChatMessage))
    created_at = DateTimeField(default=datetime.now)
    last_activity = DateTimeField(default=datetime.now)

    meta = {
        "collection": "sessions",  # Collection name in MongoDB
        "indexes": ["session_id"],  # Index for efficient query by session_id
    }


def fetch_chat_history(session_id: str, n: int = 2) -> List[Dict[str, str]]:
    """Fetches the chat history for a session in the required format."""

    try:
        # Find all messages belonging to the session
        messages = (
            ChatMessage.objects(session_id=session_id)
            .order_by("-timestamp")
            .limit(n * 2)
        )  # 2 messages per chat

        messages = list(messages)[::-1]
        chat_history = []
        for msg in messages:
            # Add user message
            chat_history.append({"role": "user", "content": msg.message})
            # Add assistant response
            chat_history.append(
                {
                    "role": "assistant",
                    "content": msg.response or "",  # in case response is None
                }
            )

        return chat_history

    except Exception as e:
        print(f"Error fetching chat history: {e}")
        return []
