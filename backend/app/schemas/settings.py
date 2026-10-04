from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class AutonomySettings(BaseModel):
    autonomy_level: int = 2
    require_confirmation_for_high_risk: bool = True
    emergency_stop_active: bool = False
    allow_background_execution: bool = True

class ModelProviderConfig(BaseModel):
    provider_name: str
    model_name: str
    model_type: str = "REASONING"
    api_key_configured: bool = False
    is_default: bool = False
    endpoint_url: Optional[str] = None

class UserPreferences(BaseModel):
    theme: str = "dark"
    preferred_language: str = "en"
    preferred_output_folder: str = "data/outputs"
    preferred_doc_format: str = "DOCX"
    preferred_code_language: str = "python"
    sound_notifications: bool = True
    desktop_notifications: bool = True

class SystemSettingsRead(BaseModel):
    app_name: str
    app_version: str
    environment: str
    autonomy: AutonomySettings
    preferences: UserPreferences
    models: List[ModelProviderConfig] = Field(default_factory=list)
    system_status: Dict[str, Any] = Field(default_factory=dict)

class SystemSettingsUpdate(BaseModel):
    autonomy_level: Optional[int] = None
    emergency_stop_active: Optional[bool] = None
    require_confirmation_for_high_risk: Optional[bool] = None
    theme: Optional[str] = None
    preferred_output_folder: Optional[str] = None
    default_model_provider: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
