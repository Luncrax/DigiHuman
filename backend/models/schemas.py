"""
Data Models and Schemas
Defines the data structures used throughout the application
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


# Enum definitions
class EmotionType(str, Enum):
    happy = "happy"
    sad = "sad"
    angry = "angry"
    surprised = "surprised"
    fear = "fear"
    neutral = "neutral"


class ToolStatus(str, Enum):
    success = "success"
    error = "error"
    pending = "pending"


# Base models
class BaseResponse(BaseModel):
    """Base response model for all API responses"""
    status: str = "success"
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    reply: str


class ChatHistoryResponse(BaseModel):
    """Response model for chat history"""
    session_id: str
    history: List[Dict[str, Any]]


class StartSessionRequest(BaseModel):
    """Request model for starting a new session"""
    user_id: Optional[str] = None
    initial_context: Optional[Dict[str, Any]] = None


class StartSessionResponse(BaseModel):
    """Response model for starting a new session"""
    session_id: str
    user_id: Optional[str]
    status: str


# Request/Response models for tools API
class ToolRequest(BaseModel):
    """Request model for tool execution"""
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool")
    user_id: Optional[str] = Field(None, description="User identifier")


class ToolResponse(BaseModel):
    """Response model for tool execution"""
    result: Any = Field(..., description="Result of the tool execution")
    status: ToolStatus = Field(..., description="Status of the tool execution")
    tool_name: str = Field(..., description="Name of the tool executed")
    execution_time: Optional[float] = Field(None, description="Time taken to execute the tool")


class AvailableToolsResponse(BaseModel):
    """Response model for listing available tools"""
    tools: List[Dict[str, str]]


class ToolInfoResponse(BaseModel):
    """Response model for tool information"""
    tool_name: str
    description: str
    parameters: List[str]


# Models for emotion service
class EmotionDetectionRequest(BaseModel):
    """Request model for emotion detection"""
    text: str = Field(..., description="Text to analyze for emotions")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for emotion analysis")


class EmotionDetectionResponse(BaseModel):
    """Response model for emotion detection"""
    emotion: EmotionType
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for emotion detection")
    response_suggestion: str = Field(..., description="Suggested response based on detected emotion")
    intensity: float = Field(..., ge=0.0, le=1.0, description="Intensity of the detected emotion")


# Models for dialogue service
class ProcessUserInputRequest(BaseModel):
    """Request model for processing user input"""
    user_input: str
    user_id: str
    session_id: str


class ProcessUserInputResponse(BaseModel):
    """Response model for processing user input"""
    response: str
    session_id: str
    user_id: str
    emotion: Optional[EmotionType] = None


# Models for memory operations
class VectorInsertRequest(BaseModel):
    """Request model for inserting a vector"""
    vector: List[float] = Field(..., description="The vector to insert")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata associated with the vector")
    vector_id: Optional[str] = Field(None, description="Optional ID for the vector")


class VectorSearchRequest(BaseModel):
    """Request model for searching similar vectors"""
    query_vector: List[float] = Field(..., description="The query vector for similarity search")
    top_k: int = Field(5, description="Number of top results to return")
    threshold: float = Field(0.5, description="Similarity threshold")


class VectorSearchResponse(BaseModel):
    """Response model for vector search"""
    results: List[Dict[str, Any]]
    query_vector_length: int
    top_k: int
    threshold: float


class KnowledgeEntry(BaseModel):
    """Model for a knowledge entry"""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


# Models for session management
class SessionData(BaseModel):
    """Model for session data"""
    user_id: str
    created_at: datetime
    last_activity: datetime
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UserPreferences(BaseModel):
    """Model for user preferences"""
    language: str = "en"
    timezone: str = "UTC"
    notification_preferences: Dict[str, bool] = Field(
        default_factory=lambda: {"email": True, "push": True}
    )
    customization: Optional[Dict[str, Any]] = Field(default_factory=dict)


# Response models for health checks
class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    services: Dict[str, bool] = Field(default_factory=dict)


class SystemInfoResponse(BaseModel):
    """Response model for system information"""
    version: str = "1.0.0"
    environment: str = "development"
    uptime: Optional[str] = None
    services: List[str] = Field(default_factory=list)
