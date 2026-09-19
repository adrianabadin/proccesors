"""Pruebas de inicialización, registro y despacho de herramientas en FastMCP."""
import asyncio
import json
import pytest
from sibom_mcp.db import Database
from sibom_mcp.server import create_mcp_server
from tests.test_contract import EXPECTED_TOOLS


def test_server_discovers_all_17_tools(test_env):
    """Verifica que el servidor registre y exponga exactamente las 17 herramientas."""
    async def run():
        db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])
        server = create_mcp_server(db)
        tool_list = await server.list_tools()
        discovered_names = [t.name for t in tool_list]
        assert len(discovered_names) == 17
        for expected in EXPECTED_TOOLS:
            assert expected in discovered_names, f"Herramienta '{expected}' no fue descubierta en el servidor"

    asyncio.run(run())


def test_server_call_health_check(test_env):
    """Verifica invocación de sibom_health_check a través del servidor FastMCP."""
    async def run():
        db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])
        server = create_mcp_server(db)
        res = await server.call_tool("sibom_health_check", {})
        assert not res.is_error
        data = res.structured_content if res.structured_content else res.content[0].text
        if isinstance(data, str):
            data = json.loads(data)
        assert data["status"] in ("ok", "degraded")
        assert data["database"]["status"] == "connected"

    asyncio.run(run())


def test_server_call_search_and_get(test_env):
    """Verifica invocaciones de búsqueda y detalle a través del protocolo del servidor."""
    async def run():
        db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])
        server = create_mcp_server(db)

        # Invocación de búsqueda
        search_res = await server.call_tool("sibom_search_normas", {"query": "habitat", "limit": 5})
        assert not search_res.is_error
        s_data = search_res.structured_content or search_res.content[0].text
        if isinstance(s_data, str):
            s_data = json.loads(s_data)
        assert s_data["returned_count"] >= 1

        # Invocación de detalle de norma
        get_res = await server.call_tool("sibom_get_norma", {"id": 1})
        assert not get_res.is_error
        g_data = get_res.structured_content or get_res.content[0].text
        if isinstance(g_data, str):
            g_data = json.loads(g_data)
        assert g_data["id"] == 1
        assert "Hábitat" in g_data["titulo"]

    asyncio.run(run())


def test_server_call_compilar_y_comparar(test_env):
    """Verifica invocación de las nuevas herramientas compilar y comparar."""
    async def run():
        db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])
        server = create_mcp_server(db)

        # Compilar temática
        comp_res = await server.call_tool("sibom_compilar_tematica", {"tema": "habitat", "limit": 5})
        assert not comp_res.is_error
        c_data = comp_res.structured_content or comp_res.content[0].text
        if isinstance(c_data, str):
            c_data = json.loads(c_data)
        assert c_data["tema"] == "habitat"
        assert "dossier_markdown" in c_data

        # Comparar intermunicipal
        comp_inter = await server.call_tool("sibom_comparar_intermunicipal", {
            "tema": "vivienda",
            "municipio_destino": 108,
            "municipios_referencia": [130]
        })
        assert not comp_inter.is_error
        ci_data = comp_inter.structured_content or comp_inter.content[0].text
        if isinstance(ci_data, str):
            ci_data = json.loads(ci_data)
        assert ci_data["municipio_destino"]["id"] == 108

    asyncio.run(run())
