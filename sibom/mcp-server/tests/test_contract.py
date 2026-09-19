"""Test de contrato y paridad de herramientas para SIBOM MCP."""
import pytest
from pydantic import ValidationError

# Los 17 nombres exactos definidos en el contrato del plan
EXPECTED_TOOLS = [
    "sibom_search_normas",
    "sibom_search_by_category",
    "sibom_search_by_year_range",
    "sibom_get_norma",
    "sibom_get_anexo",
    "sibom_search_by_entity",
    "sibom_get_references",
    "sibom_list_categories",
    "sibom_get_stats",
    "sibom_similar_normas",
    "sibom_summarize_texto",
    "sibom_health_check",
    "sibom_semantic_search",
    "sibom_semantic_search_articulos",
    "sibom_full_semantic_search",
    "sibom_compilar_tematica",
    "sibom_comparar_intermunicipal",
]


def test_expected_tool_count():
    """Acreditar que el contrato contempla exactamente 17 herramientas."""
    assert len(EXPECTED_TOOLS) == 17
    assert len(set(EXPECTED_TOOLS)) == 17


def test_tool_schemas_importable():
    """Verifica que todos los esquemas Pydantic para las 17 herramientas existan."""
    from sibom_mcp import schemas

    # Validar que los 17 esquemas de entrada están definidos
    assert hasattr(schemas, "SearchNormasInput")
    assert hasattr(schemas, "SearchByCategoryInput")
    assert hasattr(schemas, "SearchByYearRangeInput")
    assert hasattr(schemas, "GetNormaInput")
    assert hasattr(schemas, "GetAnexoInput")
    assert hasattr(schemas, "SearchByEntityInput")
    assert hasattr(schemas, "GetReferencesInput")
    assert hasattr(schemas, "ListCategoriesInput")
    assert hasattr(schemas, "GetStatsInput")
    assert hasattr(schemas, "SimilarNormasInput")
    assert hasattr(schemas, "SummarizeTextoInput")
    assert hasattr(schemas, "HealthCheckInput")
    assert hasattr(schemas, "SemanticSearchInput")
    assert hasattr(schemas, "SemanticSearchArticulosInput")
    assert hasattr(schemas, "FullSemanticSearchInput")
    assert hasattr(schemas, "CompilarTematicaInput")
    assert hasattr(schemas, "CompararIntermunicipalInput")


def test_schema_validations():
    """Valida reglas de negocio en los esquemas de entrada."""
    from sibom_mcp import schemas

    # 1. Búsqueda textual: query no vacía
    with pytest.raises(ValidationError):
        schemas.SearchNormasInput(query="")

    valid_search = schemas.SearchNormasInput(query="presupuesto")
    assert valid_search.tipo == "ordenanza"
    assert valid_search.limit == 20

    # 2. Rango de años: desde <= hasta
    with pytest.raises(ValidationError):
        schemas.SearchByYearRangeInput(desde=2024, hasta=2010)

    valid_range = schemas.SearchByYearRangeInput(desde=2010, hasta=2024)
    assert valid_range.desde == 2010
    assert valid_range.hasta == 2024

    # 3. ID positivo
    with pytest.raises(ValidationError):
        schemas.GetNormaInput(id=0)

    with pytest.raises(ValidationError):
        schemas.GetNormaInput(id=-5)

    valid_get = schemas.GetNormaInput(id=108)
    assert valid_get.id == 108

    # 4. Límites acotados 1..100
    with pytest.raises(ValidationError):
        schemas.SearchNormasInput(query="test", limit=0)
    with pytest.raises(ValidationError):
        schemas.SearchNormasInput(query="test", limit=101)

    # 5. Profundidad de referencias 1..5
    with pytest.raises(ValidationError):
        schemas.GetReferencesInput(norma_id=1, profundidad=0)
    with pytest.raises(ValidationError):
        schemas.GetReferencesInput(norma_id=1, profundidad=6)

    # 6. Compilación temática
    with pytest.raises(ValidationError):
        schemas.CompilarTematicaInput(tema="")

    valid_comp = schemas.CompilarTematicaInput(tema="habitat")
    assert valid_comp.limit == 20
    assert valid_comp.tipo == "ordenanza"

    # 7. Comparación intermunicipal: destino Saladillo (108) por defecto
    valid_comp_inter = schemas.CompararIntermunicipalInput(tema="salud")
    assert valid_comp_inter.municipio_destino in (108, "108", "saladillo")
