from fastapi import APIRouter
from backend.models.schemas import ChatRequest, ChatResponse
from backend.services.dialogue_service import generate_reply
from backend.services.memory_agent import BasicMemoryAgent
from typing import Dict, Any

router = APIRouter()

# Dictionary to store memory agents per session
session_agents: Dict[str, BasicMemoryAgent] = {}


def get_agent_for_session(session_id: str) -> BasicMemoryAgent:
    """Get or create a memory agent for a specific session."""
    if session_id not in session_agents:
        session_agents[session_id] = BasicMemoryAgent()
    return session_agents[session_id]


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat with memory using session-based agents."""
    # Use default session if no session specified in request
    session_id = getattr(request, 'session_id', 'default_session')
    
    # Get the agent for this session
    agent = get_agent_for_session(session_id)
    
    # If history is provided in the request, load it into the agent
    if request.history:
        agent.load_memory_from_history(request.history)
    
    # Generate reply using the agent
    reply = await agent.chat(request.message)
    
    return ChatResponse(reply=reply)


@router.post("/chat_with_session", response_model=ChatResponse)
async def chat_with_session(session_id: str, request: ChatRequest):
    """Handle chat with memory using a specific session ID."""
    agent = get_agent_for_session(session_id)
    
    # If history is provided in the request, load it into the agent
    if request.history:
        agent.load_memory_from_history(request.history)
    
    # Generate reply using the agent
    reply = await agent.chat(request.message)
    
    return ChatResponse(reply=reply)


@router.get("/session_memory/{session_id}")
async def get_session_memory(session_id: str):
    """Get the memory (conversation history) for a specific session."""
    if session_id not in session_agents:
        return {"session_id": session_id, "memory": [], "message": "Session not found or no memory yet"}
    
    agent = session_agents[session_id]
    memory = agent.get_memory()
    return {"session_id": session_id, "memory": memory}


@router.delete("/session_memory/{session_id}")
async def clear_session_memory(session_id: str):
    """Clear the memory for a specific session."""
    if session_id in session_agents:
        agent = session_agents[session_id]
        agent.clear_memory()
        return {"session_id": session_id, "message": "Memory cleared successfully"}
    
    return {"session_id": session_id, "message": "Session not found"}


@router.get("/active_sessions")
async def get_active_sessions():
    """Get a list of all active sessions."""
    return {"sessions": list(session_agents.keys()), "count": len(session_agents)}
