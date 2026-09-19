"""Pruebas para compilación temática y generación de dossiers."""
from sibom_mcp.db import Database
from sibom_mcp.tools.compilar import compilar_tematica


def test_compilar_tematica_habitat(test_env):
    """Verifica compilación temática de hábitat sobre múltiples municipios."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    dossier = compilar_tematica(db, tema="habitat", limit=10)
    assert dossier["tema"] == "habitat"
    assert dossier["returned_count"] >= 2
    assert dossier["total_candidates"] >= 2

    # Verificar que las normas tengan sus artículos y relaciones
    normas = dossier["normas"]
    norma1 = next((n for n in normas if n["id"] == 1), None)
    assert norma1 is not None
    assert len(norma1["articulos"]) >= 2
    assert len(norma1["anexos"]) >= 1

    # Verificar generación de Markdown con aviso legal
    md = dossier["dossier_markdown"]
    assert "# Dossier Temático Normativo: Habitat" in md
    assert "Aviso Legal" in md
    assert "texto consolidado oficial" in md


def test_compilar_tematica_paginacion(test_env):
    """Verifica paginación estable con cursor y has_more."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    # Página 1
    p1 = compilar_tematica(db, tema="habitat", cursor=0, limit=1)
    assert p1["returned_count"] == 1
    assert p1["has_more"] is True
    assert p1["next_cursor"] == 1

    # Página 2
    p2 = compilar_tematica(db, tema="habitat", cursor=1, limit=1)
    assert p2["returned_count"] == 1
    # Los IDs de página 1 y página 2 no deben solaparse
    assert p1["normas"][0]["id"] != p2["normas"][0]["id"]


def test_compilar_tematica_filtro_municipio(test_env):
    """Verifica compilación acotada a municipios específicos."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    # Solo Saladillo (108)
    dossier_sal = compilar_tematica(db, tema="habitat", municipios=[108])
    for n in dossier_sal["normas"]:
        assert n["localidad"] == "Saladillo"
