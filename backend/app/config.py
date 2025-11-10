import os
from typing import Optional


class Settings:
    """Simple settings wrapper that reads from environment variables.

    We avoid using Pydantic/BaseSettings to simplify packaging inside the
    container (pydantic v2.9 moved BaseSettings to pydantic-settings).
    """

    def __init__(self) -> None:
        self.app_name: str = os.getenv("APP_NAME", "Finance Assistant")
        self.environment: str = os.getenv("ENV", "dev")
        self.database_url: str = os.getenv(
            "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/finance"
        )
        self.llm_api_url: str = os.getenv("LLM_API_URL", "stub://local")
        self.llm_api_key: Optional[str] = os.getenv("LLM_API_KEY")
        self.upload_dir: str = os.getenv("UPLOAD_DIR", "/data/uploads")
        self.alembic_ini: str = os.getenv("ALEMBIC_INI", "/app/alembic.ini")


settings = Settings()
