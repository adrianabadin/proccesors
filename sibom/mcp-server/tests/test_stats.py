"""Pruebas para estadísticas y métricas del corpus."""
from sibom_mcp.db import Database
from sibom_mcp.tools.stats import get_stats


def test_get_stats_global(test_env):
    """Verifica cálculo de métricas globales del fixture."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    stats = get_stats(db)
    assert stats["total_normas"] >= 5
    assert stats["ordenanzas"] >= 4
    assert stats["decretos"] >= 1
    assert stats["anios_desconocidos"] >= 1
    assert len(stats["distribucion_por_municipio"]) >= 3
    assert stats["cobertura_embeddings"]["embedding_summary"] >= 4


def test_get_stats_filtrado_por_municipio(test_env):
    """Verifica métricas acotadas a un único municipio."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    stats = get_stats(db, municipio=108)
    assert stats["municipio_filtro"]["id"] == 108
    assert stats["total_normas"] >= 3
    assert stats["distribucion_por_municipio"] == []
