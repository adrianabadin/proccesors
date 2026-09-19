"""Pruebas para herramientas semánticas (similar, búsqueda de normas y artículos)."""
from sibom_mcp.db import Database
from sibom_mcp.tools.similar import similar_normas
from sibom_mcp.tools.semantic import (
    semantic_search,
    semantic_search_articulos,
    full_semantic_search
)


def test_similar_normas(test_env):
    """Verifica búsqueda de normas similares por vector de referencia."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    # Norma 1 tiene vector vec_habitat idéntico a Norma 2 y Norma 3
    res = similar_normas(db, norma_id=1, limit=5, umbral=0.8)
    assert res["returned_count"] >= 2
    # La norma consultada (1) NO debe estar en los resultados
    result_ids = [item["id"] for item in res["items"]]
    assert 1 not in result_ids
    assert 2 in result_ids
    assert 3 in result_ids
    assert all(item["score"] >= 0.8 for item in res["items"])


def test_similar_normas_filtro_municipio(test_env):
    """Verifica que el filtro de municipio acote los similares encontrados."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    # Filtrar solo similares en Saladillo (108)
    res = similar_normas(db, norma_id=1, municipio=108, limit=5, umbral=0.5)
    result_ids = [item["id"] for item in res["items"]]
    assert 2 in result_ids
    # Norma 3 pertenece a 130, no debe aparecer
    assert 3 not in result_ids


def test_semantic_search_mock(test_env):
    """Verifica búsqueda semántica con query libre y modelo mock."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    res = semantic_search(db, query="vivienda social", limit=5, umbral=0.0, mock=True)
    assert res["search_method"] == "semantic_normas"
    assert res["returned_count"] >= 1
    assert "score" in res["items"][0]


def test_semantic_search_articulos_mock(test_env):
    """Verifica búsqueda semántica en artículos individuales."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    res = semantic_search_articulos(db, query="banco de tierras", limit=5, umbral=-1.0, mock=True)
    assert res["search_method"] == "semantic_articulos"
    assert res["returned_count"] >= 1
    item = res["items"][0]
    assert "articulo_id" in item
    assert "norma_id" in item
    assert "texto" in item
    assert "norma" in item


def test_full_semantic_search_mock(test_env):
    """Verifica búsqueda combinada de normas y artículos con identidades diferenciadas."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    res = full_semantic_search(db, query="habitat y vivienda", limit=5, umbral=0.0, mock=True)
    assert res["search_method"] == "full_semantic_hybrid"
    assert res["returned_count"] >= 2
    types = {item["identity_type"] for item in res["items"]}
    assert "norma" in types or "articulo" in types
