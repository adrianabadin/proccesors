"""Pruebas para el indexador derivado y manifiestos de generación."""
import sqlite3
from pathlib import Path
from sibom_mcp.indexer import build_index


def test_build_index_mock(test_env, tmp_path: Path):
    """Verifica construcción del índice de artículos con modelo mock determinista."""
    output_db = tmp_path / "fresh_index.db"

    res = build_index(
        db_path=test_env["db_path"],
        output_path=output_db,
        model_name="mock",
        batch_size=2,
        resume=False,
        mock=True
    )

    assert res["new_indexed"] >= 4
    assert res["total_articles"] >= 4
    assert "generation_id" in res

    # Verificar datos en fresh_index.db
    conn = sqlite3.connect(str(output_db))
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM articulo_embeddings")
    count = cur.fetchone()[0]
    assert count >= 4

    cur.execute("SELECT generation_id, model_name, active FROM manifests WHERE active = 1")
    manifest = cur.fetchone()
    assert manifest is not None
    assert manifest[1] == "mock"
    assert manifest[2] == 1
    conn.close()


def test_build_index_resume(test_env, tmp_path: Path):
    """Verifica que resume=True no reprocese artículos existentes."""
    output_db = tmp_path / "resume_index.db"

    # Primera corrida
    res1 = build_index(
        db_path=test_env["db_path"],
        output_path=output_db,
        model_name="mock",
        batch_size=2,
        resume=False,
        mock=True
    )
    assert res1["new_indexed"] >= 4

    # Segunda corrida con resume=True
    res2 = build_index(
        db_path=test_env["db_path"],
        output_path=output_db,
        model_name="mock",
        batch_size=2,
        resume=True,
        mock=True
    )
    assert res2["new_indexed"] == 0
