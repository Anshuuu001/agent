import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.core.events import event_bus
from backend.app.core.brain import ai_brain

logger = logging.getLogger("desktop_ai.websocket")

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await event_bus.connect(websocket)
    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                msg = json.loads(data_text)
                action = msg.get("action")
                
                # Handle direct chat/command input via WebSocket
                if action == "chat":
                    content = msg.get("content", "")
                    session_id = msg.get("session_id")
                    response = await ai_brain.process_user_input(
                        user_message=content,
                        session_id=session_id,
                        auto_execute=True
                    )
                    await websocket.send_text(json.dumps({
                        "event": "brain_response",
                        "data": response.model_dump()
                    }))

                elif action == "ping":
                    await websocket.send_text(json.dumps({"event": "pong"}))

            except Exception as parse_err:
                logger.debug(f"Error handling websocket frame: {parse_err}")
    except WebSocketDisconnect:
        await event_bus.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await event_bus.disconnect(websocket)
