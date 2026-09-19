"""Configuración centralizada para SIBOM MCP Server."""
import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
SIBOM_ROOT = PROJECT_ROOT.parent


class Settings(BaseSettings):
    """Ajustes del servidor MCP SIBOM."""
    # Base de datos SIBOM SQLite de solo lectura
    sibom_db_path: str = Field(
        default_factory=lambda: os.getenv(
            "SIBOM_DB_PATH",
            str((SIBOM_ROOT / "sibom.db").resolve())
        )
    )

    # Base de datos del índice derivado (categorías, entidades, artículos)
    index_db_path: str = Field(
        default_factory=lambda: os.getenv(
            "SIBOM_INDEX_DB_PATH",
            str((PROJECT_ROOT / "data" / "sibom-index.db").resolve())
        )
    )

    # Directorio de anexos PDF
    anexos_dir: str = Field(
        default_factory=lambda: os.getenv(
            "SIBOM_ANEXOS_DIR",
            str((SIBOM_ROOT / "anexos").resolve())
        )
    )

    # Modelo de embeddings
    embedding_model: str = Field(
        default="paraphrase-multilingual-MiniLM-L12-v2"
    )
    embedding_dimension: int = 384

    # Límites
    max_query_limit: int = 100
    default_query_limit: int = 20
    sqlite_timeout: float = 30.0

    # Proveedor LLM para resúmenes
    groq_api_key: str | None = Field(default_factory=lambda: os.getenv("GROQ_API_KEY"))
    openai_api_key: str | None = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    llm_model: str = "llama-3.3-70b-versatile"

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


settings = Settings()
