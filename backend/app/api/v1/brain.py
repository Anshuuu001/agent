from fastapi import APIRouter, HTTPException
from backend.app.schemas.chat import ChatMessageCreate, BrainResponse
from backend.app.core.brain import ai_brain

router = APIRouter(prefix="/brain", tags=["AI Brain"])

@router.post("/chat", response_model=BrainResponse)
async def chat_with_brain(payload: ChatMessageCreate):
    """
    Primary interface to the Universal Autonomous Desktop AI:
    Accepts user goal in natural language -> AI Brain plans, selects agents/tools, and executes.
    """
    try:
        response = await ai_brain.process_user_input(
            user_message=payload.content,
            session_id=payload.session_id,
            auto_execute=True
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Brain processing error: {str(e)}")
