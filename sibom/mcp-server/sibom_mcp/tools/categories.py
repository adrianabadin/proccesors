"""Herramienta para listar y consultar la taxonomía de categorías."""
from typing import Any
from ..db import Database
from ..enrichment import get_all_categories_with_counts


def list_categories(db: Database, incluir_vacias: bool = False) -> dict[str, Any]:
    """Lista todas las categorías disponibles y conteos de normas asignadas."""
    categories = get_all_categories_with_counts(db, incluir_vacias=incluir_vacias)
    return {
        "categories": categories,
        "total": len(categories),
        "incluir_vacias": incluir_vacias
    }
