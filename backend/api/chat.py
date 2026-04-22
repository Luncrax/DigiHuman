from fastapi import APIRouter
from backend.models.schemas import ChatRequest, ChatResponse
from backend.services.dialogue_service import generate_reply

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    reply = await generate_reply(request.message, request.history)
    return ChatResponse(reply=reply)
