"""Pruebas para generación de resúmenes y caché persistente."""
import os
import pytest
from sibom_mcp.db import Database
from sibom_mcp.config import settings
from sibom_mcp.tools.summarize import summarize_texto


def test_summarize_sin_proveedor_configurado(test_env, monkeypatch):
    """Verifica que sin API keys se informe claramente 'provider_not_configured'."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])
    monkeypatch.setattr(settings, "groq_api_key", None)
    monkeypatch.setattr(settings, "openai_api_key", None)

    res = summarize_texto(db, texto="Texto legal a resumir...", longitud=50)
    assert res["status"] == "provider_not_configured"
    assert "no configurado" in res["error"].lower()
    assert res["cached"] is False


def test_summarize_con_cache_y_estilos(test_env):
    """Verifica generación con mock, almacenamiento en caché e invalidación por estilo."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])
    texto = "Ordenanza de prueba sobre regulación de parcelas en Saladillo."

    # 1. Primera llamada: genera y no está en caché
    res1 = summarize_texto(
        db,
        texto=texto,
        longitud=30,
        estilo="formal",
        mock_response="Resumen formal generado por IA."
    )
    assert res1["status"] == "ok"
    assert res1["cached"] is False
    assert res1["resumen"] == "Resumen formal generado por IA."

    # 2. Segunda llamada con idénticos parámetros: debe venir de caché (cached=True)
    res2 = summarize_texto(
        db,
        texto=texto,
        longitud=30,
        estilo="formal",
        mock_response="Nuevo texto que no debería usarse"
    )
    assert res2["status"] == "ok"
    assert res2["cached"] is True
    assert res2["resumen"] == "Resumen formal generado por IA."

    # 3. Llamada cambiando estilo a bullet-points: clave de hash distinta, no usa caché anterior
    res3 = summarize_texto(
        db,
        texto=texto,
        longitud=30,
        estilo="bullet-points",
        mock_response="- Punto 1: Regula parcelas."
    )
    assert res3["status"] == "ok"
    assert res3["cached"] is False
    assert res3["resumen"] == "- Punto 1: Regula parcelas."
