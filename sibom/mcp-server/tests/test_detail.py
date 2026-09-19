"""Pruebas para herramientas de detalle de norma y anexo."""
import pytest
from sibom_mcp.db import Database
from sibom_mcp.tools.detail import get_norma, get_anexo


def test_get_norma_completa(test_env):
    """Verifica recuperación completa de una norma con artículos, referencias y anexos."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    norma = get_norma(db, norma_id=1)
    assert norma["id"] == 1
    assert norma["numero"] == 10
    assert norma["anio"] == 2021
    assert "Hábitat" in norma["titulo"]
    assert len(norma["articulos"]) >= 2
    assert len(norma["anexos"]) >= 1
    assert "urbanismo-suelo" in [c.lower() for c in norma["categorias"]] or "vivienda social" in [c.lower() for c in norma["categorias"]]


def test_get_norma_inexistente(test_env):
    """Verifica que un ID inexistente arroje error explícito."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])
    with pytest.raises(ValueError) as exc_info:
        get_norma(db, norma_id=999999)
    assert "no se encontró" in str(exc_info.value).lower()


def test_get_anexo_seguro(test_env):
    """Verifica consulta de anexo y prevención de path traversal."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])
    anexos_dir = test_env["anexos_dir"]

    # Anexo existente en fixture
    res = get_anexo(db, anexo_id=1, anexos_dir=anexos_dir)
    assert res["id"] == 1
    assert res["norma_id"] == 1
    assert "plano" in res["nombre"].lower()
    assert res["archivo_local"] is not None

    # Anexo inexistente
    with pytest.raises(ValueError):
        get_anexo(db, anexo_id=9999)
