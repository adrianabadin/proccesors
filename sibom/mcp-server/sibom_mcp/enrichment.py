"""Gestión de taxonomía, enriquecimiento y entidades tipadas."""
import json
from pathlib import Path
from typing import Any
from .config import PROJECT_ROOT
from .db import Database

TAXONOMY_JSON = PROJECT_ROOT / "config" / "taxonomy.json"


def seed_taxonomy_from_json(db: Database, taxonomy_path: str | Path | None = None) -> int:
    """Inserta o actualiza la taxonomía jerárquica en sibom-index.db."""
    path = Path(taxonomy_path or TAXONOMY_JSON).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Archivo de taxonomía no encontrado: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    categories = data.get("categories", [])

    conn = db.get_index_conn(readonly=False)
    cur = conn.cursor()

    inserted_count = 0
    for cat in categories:
        cur.execute("""
            INSERT INTO categorias (nombre, slug, descripcion, parent_id)
            VALUES (?, ?, ?, NULL)
            ON CONFLICT(slug) DO UPDATE SET
                nombre=excluded.nombre,
                descripcion=excluded.descripcion
        """, (cat["nombre"], cat["slug"], cat.get("descripcion")))
        inserted_count += 1
        parent_id = cur.lastrowid
        if not parent_id:
            cur.execute("SELECT id FROM categorias WHERE slug = ?", (cat["slug"],))
            parent_id = cur.fetchone()[0]

        for sub in cat.get("subcategories", []):
            cur.execute("""
                INSERT INTO categorias (nombre, slug, descripcion, parent_id)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(slug) DO UPDATE SET
                    nombre=excluded.nombre,
                    descripcion=excluded.descripcion,
                    parent_id=excluded.parent_id
            """, (sub["nombre"], sub["slug"], sub.get("descripcion"), parent_id))
            inserted_count += 1

    conn.commit()
    conn.close()
    return inserted_count


def get_all_categories_with_counts(db: Database, incluir_vacias: bool = False) -> list[dict[str, Any]]:
    """Obtiene todas las categorías y el conteo de normas asignadas."""
    sql = """
        SELECT 
            c.id,
            c.nombre,
            c.slug,
            c.descripcion,
            c.parent_id,
            p.nombre as parent_nombre,
            count(nc.norma_id) as normas_count
        FROM categorias c
        LEFT JOIN categorias p ON c.parent_id = p.id
        LEFT JOIN norma_categorias nc ON nc.categoria_id = c.id
        GROUP BY c.id, c.nombre, c.slug, c.descripcion, c.parent_id, p.nombre
        ORDER BY COALESCE(c.parent_id, c.id), c.id
    """
    rows = db.query_index(sql)
    if not incluir_vacias:
        rows = [r for r in rows if r["normas_count"] > 0]
    return rows
