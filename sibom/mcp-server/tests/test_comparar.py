"""Pruebas para comparación normativa intermunicipal."""
from sibom_mcp.db import Database
from sibom_mcp.tools.comparar import comparar_intermunicipal


def test_comparar_intermunicipal_habitat_equivalente(test_env):
    """Verifica detección de ordenanza equivalente en municipio destino."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    # Comparar hábitat con Saladillo (108) como destino y Veinticinco de Mayo (130) como referencia
    res = comparar_intermunicipal(
        db=db,
        tema="vivienda",
        municipio_destino=108,
        municipios_referencia=[130]
    )

    assert res["municipio_destino"]["id"] == 108
    assert res["candidatos_analizados"] >= 1
    
    comp = res["comparaciones"][0]
    assert comp["candidato_referencia"]["localidad"] == "Veinticinco de Mayo"
    # Debe haber encontrado equivalente en Saladillo (Norma 1 o 2 sobre hábitat)
    assert comp["estado_resultado"] == "equivalente_encontrado"
    assert comp["antecedente_destino"] is not None
    assert comp["antecedente_destino"]["id"] in (1, 2)
    assert "aviso_metodologico" in res


def test_comparar_intermunicipal_sin_candidatos(test_env):
    """Verifica que ausencia de antecedentes devuelva 'evidencia_insuficiente' sin inventar."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    res = comparar_intermunicipal(
        db=db,
        tema="materia_totalmente_inexistente_999",
        municipio_destino=108
    )

    assert res["status"] == "evidencia_insuficiente"
    assert res["candidatos_analizados"] == 0
