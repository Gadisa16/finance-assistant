import os
from pydantic import BaseSettings, AnyUrl


class Settings(BaseSettings):
    app_name: str = "Finance Assistant"
    environment: str = os.getenv("ENV", "dev")
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/finance")
    llm_api_url: str = os.getenv("LLM_API_URL", "stub://local")
    llm_api_key: str | None = os.getenv("LLM_API_KEY")
    upload_dir: str = os.getenv("UPLOAD_DIR", "/data/uploads")
    alembic_ini: str = os.getenv("ALEMBIC_INI", "/app/alembic.ini")


settings = Settings()
