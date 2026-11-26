"""Configuración central vía variables de entorno (pydantic-settings)."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Base de datos
    database_url: str = "postgresql+psycopg://helpdesk:helpdesk@localhost:5432/helpdesk"

    # Seguridad
    jwt_secret: str = "cambia-esta-clave-en-produccion"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720

    # Ollama / modelos locales
    ollama_base_url: str = "http://localhost:11434"
    triage_model: str = "qwen2.5:3b-instruct"
    resolution_model: str = "qwen2.5:3b-instruct"
    embedding_model: str = "nomic-embed-text"

    # Agente de resolución (RAG)
    kb_top_k: int = 4  # fragmentos recuperados por consulta

    # Usuario admin inicial (solo si la BD está vacía)
    # IMPORTANTE: debe ser un email válido con TLD (pydantic EmailStr lo exige);
    # por eso NO usar "@local" sino "@local.dev"
    admin_email: str = "admin@local.dev"
    admin_password: str = "admin1234"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
