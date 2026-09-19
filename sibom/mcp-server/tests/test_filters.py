"""Pruebas de resolución de municipios y filtros reutilizables."""
import pytest
from sibom_mcp.municipios import resolver_municipio, listar_municipios_disponibles
from sibom_mcp.db import Database


def test_resolver_municipios_conocidos():
    """Verifica resolución unívoca de municipios conocidos."""
    # Por ID numérico
    m108 = resolver_municipio(108)
    assert m108["id"] == 108
    assert m108["slug"] == "saladillo"

    # Por string numérico
    m130 = resolver_municipio("130")
    assert m130["id"] == 130
    assert m130["slug"] == "veinticinco-de-mayo"

    # Por slug
    m_alsina = resolver_municipio("adolfo-alsina")
    assert m_alsina["id"] == 1

    # Por nombre con acentos o mayúsculas
    m_salliquelo = resolver_municipio("Salliqueló")
    assert m_salliquelo["id"] == 109

    # Sin acentos
    m_salliquelo2 = resolver_municipio("salliquelo")
    assert m_salliquelo2["id"] == 109


def test_resolver_municipio_invalido():
    """Verifica rechazo explícito ante municipios inexistentes o ambiguos."""
    with pytest.raises(ValueError):
        resolver_municipio("municipio_inexistente_xyz_999")

    with pytest.raises(ValueError):
        resolver_municipio("")


def test_filtros_municipales_no_mezclan_registros(test_env):
    """Verifica que las consultas con filtro municipal aíslen estrictamente los registros."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    # Consulta para Saladillo (108)
    saladillo_normas = db.query(
        "SELECT id, codigo_localidad, titulo FROM normas WHERE codigo_localidad = ?",
        (108,)
    )
    for n in saladillo_normas:
        assert n["codigo_localidad"] == 108
    saladillo_ids = {n["id"] for n in saladillo_normas}

    # Consulta para Veinticinco de Mayo (130)
    vdemayo_normas = db.query(
        "SELECT id, codigo_localidad, titulo FROM normas WHERE codigo_localidad = ?",
        (130,)
    )
    for n in vdemayo_normas:
        assert n["codigo_localidad"] == 130
    vdemayo_ids = {n["id"] for n in vdemayo_normas}

    # Ninguna intersección
    assert saladillo_ids.isdisjoint(vdemayo_ids)
    assert len(saladillo_normas) >= 3
    assert len(vdemayo_normas) >= 1


def test_filtro_tipo_norma(test_env):
    """Verifica que el filtro de tipo (ordenanza vs decreto) discrimine adecuadamente."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    ordenanzas = db.query("SELECT id, tipo FROM normas WHERE tipo = 'ordenanza'")
    decretos = db.query("SELECT id, tipo FROM normas WHERE tipo = 'decreto'")

    assert len(ordenanzas) >= 4
    assert len(decretos) >= 1
    assert all(o["tipo"] == "ordenanza" for o in ordenanzas)
    assert all(d["tipo"] == "decreto" for d in decretos)
