from fastapi import APIRouter
from backend.app.api.v1.brain import router as brain_router
from backend.app.api.v1.tasks import router as tasks_router
from backend.app.api.v1.agents import router as agents_router
from backend.app.api.v1.tools import router as tools_router
from backend.app.api.v1.approvals import router as approvals_router
from backend.app.api.v1.memory import router as memory_router
from backend.app.api.v1.workflows import router as workflows_router
from backend.app.api.v1.audit import router as audit_router
from backend.app.api.v1.settings import router as settings_router
from backend.app.api.v1.websocket import router as ws_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(brain_router)
api_v1_router.include_router(tasks_router)
api_v1_router.include_router(agents_router)
api_v1_router.include_router(tools_router)
api_v1_router.include_router(approvals_router)
api_v1_router.include_router(memory_router)
api_v1_router.include_router(workflows_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(settings_router)

__all__ = ["api_v1_router", "ws_router"]
