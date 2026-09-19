"""Herramienta para resumir texto con LLM y caché."""
from typing import Any
from ..db import Database
from ..summary_provider import SummaryProvider


def summarize_texto(
    db: Database,
    texto: str,
    longitud: int = 50,
    estilo: str = "formal",
    mock_response: str | None = None
) -> dict[str, Any]:
    """Genera un resumen conciso del texto provisto respetando estilo y longitud."""
    provider = SummaryProvider(db)
    return provider.generate_summary(
        texto=texto,
        longitud=longitud,
        estilo=estilo,
        mock_response=mock_response
    )
