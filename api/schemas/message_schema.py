from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class ChatMessageModel(BaseModel):
    """Model for chat messages."""

    session_id: str
    message: str
    response: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    message_id: str


class ChatSessionModel(BaseModel):
    """Model for chat sessions."""

    session_id: str
    messages: List[ChatMessageModel] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)


class VectorSearchResult(BaseModel):
    """Model for vector search results."""

    query_id: str
    session_id: str
    data_type: str  # 'order', 'pdf', or 'crm'
    query: str
    results: List[Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentResponse(BaseModel):
    """Model for individual agent responses."""

    agent_type: str
    response: str
    confidence: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CombinedResponse(BaseModel):
    """Model for combined agent responses."""

    query: str
    responses: List[AgentResponse]
    final_response: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatMessageIn(BaseModel):
    message: str
    response: str


class ChatSessionIn(BaseModel):
    user_id: str


class ChatSessionOut(BaseModel):
    session_id: str
    name: str
    created_at: datetime
    last_activity: datetime


class ChatRequest(BaseModel):
    language: str
    query: str
    session_id: str
    model_name: str = "gpt-4o-mini"
    auto_send_email: Optional[bool] = False
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    response: str
    session_id: str
    message_id: str # Added for email output
    metadata: Optional[Dict[str, Any]] = None
    name: str
    timestamp: datetime


class RenameSessionRequest(BaseModel):
    session_id: str
    name: str