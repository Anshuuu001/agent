import psutil
import platform
import sys
from fastapi import APIRouter
from backend.app.config import settings
from backend.app.schemas.settings import (
    SystemSettingsRead, SystemSettingsUpdate, AutonomySettings, UserPreferences, ModelProviderConfig
)
from backend.app.core.security import security_manager
from backend.app.core.events import event_bus

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("", response_model=SystemSettingsRead)
async def get_system_settings():
    mem = psutil.virtual_memory()
    return SystemSettingsRead(
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        autonomy=AutonomySettings(
            autonomy_level=security_manager.get_autonomy_level().value,
            require_confirmation_for_high_risk=settings.REQUIRE_CONFIRMATION_FOR_HIGH_RISK,
            emergency_stop_active=security_manager.is_emergency_stop_active,
            allow_background_execution=True
        ),
        preferences=UserPreferences(
            theme="dark",
            preferred_language="en",
            preferred_output_folder=settings.OUTPUT_DIRECTORY,
            preferred_doc_format="DOCX",
            preferred_code_language="python"
        ),
        models=[
            ModelProviderConfig(
                provider_name="Heuristic Offline Engine",
                model_name="rule-and-dag-planner-v1",
                model_type="REASONING",
                api_key_configured=True,
                is_default=True
            ),
            ModelProviderConfig(
                provider_name="OpenAI",
                model_name="gpt-4o",
                model_type="REASONING",
                api_key_configured=bool(settings.OPENAI_API_KEY),
                is_default=False
            ),
            ModelProviderConfig(
                provider_name="Anthropic",
                model_name="claude-3-5-sonnet-20241022",
                model_type="REASONING",
                api_key_configured=bool(settings.ANTHROPIC_API_KEY),
                is_default=False
            ),
            ModelProviderConfig(
                provider_name="Ollama Local",
                model_name="llama3.2",
                model_type="FAST",
                api_key_configured=True,
                is_default=False,
                endpoint_url=settings.OLLAMA_BASE_URL
            )
        ],
        system_status={
            "os": platform.system(),
            "platform": platform.platform(),
            "python_version": sys.version.split()[0],
            "cpu_percent": psutil.cpu_percent(),
            "ram_percent": mem.percent
        }
    )

@router.patch("")
async def update_system_settings(payload: SystemSettingsUpdate):
    if payload.autonomy_level is not None:
        security_manager.set_autonomy_level(payload.autonomy_level)

    if payload.emergency_stop_active is not None:
        if payload.emergency_stop_active:
            security_manager.trigger_emergency_stop()
        else:
            security_manager.resume_from_emergency_stop()
        await event_bus.broadcast("emergency_stop_state", {"active": security_manager.is_emergency_stop_active})

    if payload.openai_api_key is not None:
        settings.OPENAI_API_KEY = payload.openai_api_key

    return {"status": "UPDATED", "emergency_stop_active": security_manager.is_emergency_stop_active, "autonomy_level": security_manager.get_autonomy_level().value}

@router.post("/emergency-stop")
async def toggle_emergency_stop():
    """Global Emergency Stop toggle."""
    if security_manager.is_emergency_stop_active:
        security_manager.resume_from_emergency_stop()
    else:
        security_manager.trigger_emergency_stop()
    
    await event_bus.broadcast("emergency_stop_state", {"active": security_manager.is_emergency_stop_active})
    return {"emergency_stop_active": security_manager.is_emergency_stop_active}
