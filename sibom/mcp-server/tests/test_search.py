"""Pruebas para herramientas de búsqueda (FTS, categorías, rango de años)."""
import pytest
from sibom_mcp.db import Database
from sibom_mcp.tools.search import (
    escape_fts5_query,
    search_normas,
    search_by_category,
    search_by_year_range
)


def test_escape_fts5_query():
    """Verifica que el escapado prevenga errores de sintaxis en FTS5."""
    assert escape_fts5_query('habitat "vivienda"') == '"habitat" OR "vivienda"'
    assert escape_fts5_query('salud* OR NOT: (covid)') == '"salud" OR "OR" OR "NOT" OR "covid"'
    assert escape_fts5_query('') == '""'


def test_search_normas_fts(test_env):
    """Verifica búsqueda full-text con ranking BM25 en fixture."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    # Búsqueda por término relevante
    res = search_normas(db, query="habitat vivienda")
    assert res["returned_count"] >= 2
    assert res["search_method"] == "fts5_bm25"
    assert all(
        "h" in item["titulo"].lower() and "bitat" in item["titulo"].lower() or "vivienda" in item["titulo"].lower()
        for item in res["items"]
    )

    # Búsqueda con filtro de municipio
    res_saladillo = search_normas(db, query="habitat", municipio=108)
    assert res_saladillo["returned_count"] >= 2
    assert all(item["codigo_localidad"] == 108 for item in res_saladillo["items"])

    res_vdemayo = search_normas(db, query="vivienda", municipio=130)
    assert res_vdemayo["returned_count"] >= 1
    assert all(item["codigo_localidad"] == 130 for item in res_vdemayo["items"])


def test_search_by_category(test_env):
    """Verifica filtrado por categoría taxonómica del índice derivado."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    res = search_by_category(db, slug="vivienda-social")
    assert res["returned_count"] >= 2
    assert res["category"]["slug"] == "vivienda-social"

    # Categoría inexistente devuelve error descriptivo
    res_inexistente = search_by_category(db, slug="categoria-fantasma-999")
    assert res_inexistente["returned_count"] == 0
    assert "no encontrada" in res_inexistente.get("error", "").lower()


def test_search_by_year_range(test_env):
    """Verifica búsqueda por rango de años inclusivo."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    res = search_by_year_range(db, desde=2021, hasta=2022)
    assert res["returned_count"] >= 2
    assert all(2021 <= item["anio"] <= 2022 for item in res["items"])
