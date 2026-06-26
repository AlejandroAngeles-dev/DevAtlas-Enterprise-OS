import logging
from fastapi import APIRouter
from pydantic import BaseModel

from app.orchestrator.orchestrator import Orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()
orchestrator = Orchestrator()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    message: str
    agents_used: list[str]
    conversation_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    logger.info(f"Received message: {request.message[:80]}")

    # El orquestador decide qué agentes activan
    routing = await orchestrator.route(request.message)

    # Por ahora devolvemos el reasoning del orquestador
    # En el siguiente paso aquí invocaremos los agentes reales
    return ChatResponse(
        message=routing.get("reasoning", "Procesando..."),
        agents_used=routing.get("agents", []),
        conversation_id=request.conversation_id or "temp-id",
    )