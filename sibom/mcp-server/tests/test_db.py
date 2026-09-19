"""Pruebas de la capa de base de datos SQLite y solo lectura."""
import sqlite3
import pytest
from sibom_mcp.db import Database, get_readonly_connection


def test_db_readonly_enforcement(test_env):
    """Verifica que cualquier intento de escritura sea rechazado tajantemente."""
    db_path = test_env["db_path"]
    conn = get_readonly_connection(db_path)

    # Intentar INSERT debe fallar
    with pytest.raises(sqlite3.OperationalError) as exc_info:
        conn.execute("INSERT INTO normas (id, tipo, contenido_id, version, titulo, texto_completo, url, archivo_md) VALUES (99, 'ordenanza', 99, 'completa', 't', 't', 'u', 'a')")
    assert "readonly" in str(exc_info.value).lower() or "attempt to write" in str(exc_info.value).lower()

    # Intentar UPDATE debe fallar
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("UPDATE normas SET estado = 'derogada_total' WHERE id = 1")

    # Intentar DELETE debe fallar
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM normas WHERE id = 1")

    conn.close()


def test_db_non_existent_file():
    """Verifica que una base de datos inexistente devuelva un error claro."""
    with pytest.raises(FileNotFoundError) as exc_info:
        get_readonly_connection("C:/ruta/falsa/inexistente_12345.db")
    assert "no existe" in str(exc_info.value).lower()


def test_db_query_returns_dicts(test_env):
    """Verifica que las consultas SELECT retornen diccionarios con las columnas correctas."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])
    rows = db.query("SELECT id, titulo, codigo_localidad, estado FROM normas WHERE id = ?", (1,))
    assert len(rows) == 1
    row = rows[0]
    assert isinstance(row, dict)
    assert row["id"] == 1
    assert "Hábitat" in row["titulo"]
    assert row["codigo_localidad"] == 108
    assert row["estado"] == "vigente"


def test_index_db_query(test_env):
    """Verifica consulta de solo lectura sobre el índice derivado."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])
    cats = db.query_index("SELECT id, nombre, slug FROM categorias ORDER BY id")
    assert len(cats) >= 3
    assert cats[0]["slug"] == "urbanismo-suelo"
