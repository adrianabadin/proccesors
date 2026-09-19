"""Pruebas para taxonomía, categorías y entidades tipadas."""
from sibom_mcp.db import Database
from sibom_mcp.enrichment import seed_taxonomy_from_json
from sibom_mcp.tools.categories import list_categories
from sibom_mcp.tools.entities import search_by_entity


def test_seed_taxonomy_and_list(test_env):
    """Verifica sincronización de taxonomía oficial y listado."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    # Sembrar categorías oficiales desde config/taxonomy.json
    count = seed_taxonomy_from_json(db)
    assert count >= 18

    # Listar categorías que tienen normas asignadas en fixture
    res_con_normas = list_categories(db, incluir_vacias=False)
    assert res_con_normas["total"] >= 2
    slugs = [c["slug"] for c in res_con_normas["categories"]]
    assert "vivienda-social" in slugs or "urbanismo-suelo" in slugs

    # Listar todas (incluyendo vacías)
    res_todas = list_categories(db, incluir_vacias=True)
    assert res_todas["total"] >= 18


def test_search_by_entity(test_env):
    """Verifica búsqueda de normas que mencionan una entidad con evidencia."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    # Entidad existente en fixture: "Ministerio de Hábitat"
    res = search_by_entity(db, nombre="Ministerio de Hábitat")
    assert res["returned_count"] >= 1
    item = res["items"][0]
    assert item["id"] == 1
    assert item["entidad"]["nombre"] == "Ministerio de Hábitat"
    assert item["entidad"]["rol"] == "firmante"
    assert "Convenio" in item["entidad"]["evidencia"]

    # Entidad sin normas asociadas
    res_vacia = search_by_entity(db, nombre="Juan Pérez")
    assert res_vacia["returned_count"] == 0

    # Entidad inexistente
    res_inex = search_by_entity(db, nombre="Entidad Inexistente XYZ")
    assert res_inex["returned_count"] == 0
