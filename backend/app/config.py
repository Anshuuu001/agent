import os
from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    APP_NAME: str = "Universal Autonomous Desktop AI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Server configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000", "*"]
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATA_DIR / 'desktop_ai.db'}"
    SYNC_DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'desktop_ai.db'}"
    
    # Security & Autonomy
    DEFAULT_AUTONOMY_LEVEL: int = 2  # 1: Assisted, 2: Supervised, 3: Autonomous, 4: Full Workflow
    EMERGENCY_STOP_ACTIVE: bool = False
    REQUIRE_CONFIRMATION_FOR_HIGH_RISK: bool = True
    
    # Model configuration
    DEFAULT_MODEL_PROVIDER: str = "heuristic"  # heuristic, openai, anthropic, ollama, local
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str = Field(default="", env="ANTHROPIC_API_KEY")
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Storage paths
    OUTPUT_DIRECTORY: str = str(DATA_DIR / "outputs")
    CHECKPOINTS_DIRECTORY: str = str(DATA_DIR / "checkpoints")
    LOGS_DIRECTORY: str = str(DATA_DIR / "logs")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure required directories exist
for path_str in [settings.OUTPUT_DIRECTORY, settings.CHECKPOINTS_DIRECTORY, settings.LOGS_DIRECTORY]:
    Path(path_str).mkdir(parents=True, exist_ok=True)
