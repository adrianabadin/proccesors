"""Herramientas de búsqueda textual y estructurada para SIBOM."""
import re
from typing import Any
from ..db import Database
from ..municipios import resolver_municipio


def escape_fts5_query(query: str) -> str:
    """Escapa de forma segura consultas para SQLite FTS5.
    
    Separa las palabras o frases y las envuelve en comillas dobles
    para evitar errores de sintaxis con operadores FTS5 (AND, OR, NOT, *, ^, etc.).
    """
    clean = re.sub(r'["\*\^:\(\)]', " ", query).strip()
    words = [w for w in clean.split() if w.strip()]
    if not words:
        return '""'
    # Envolver cada token en comillas dobles y unir con OR para permitir ranking BM25 flexible
    escaped_tokens = [f'"{w}"' for w in words]
    return " OR ".join(escaped_tokens)


def search_normas(
    db: Database,
    query: str,
    municipio: str | int | None = None,
    tipo: str = "ordenanza",
    solo_vigentes: bool = False,
    limit: int = 20,
    cursor: int = 0
) -> dict[str, Any]:
    """Búsqueda full-text de normas usando FTS5 y ranking BM25."""
    fts_query = escape_fts5_query(query)
    
    where_clauses = ["normas_fts MATCH ?"]
    params: list[Any] = [fts_query]

    # Filtro municipal
    mun_info = None
    if municipio is not None:
        mun_info = resolver_municipio(municipio)
        where_clauses.append("n.codigo_localidad = ?")
        params.append(mun_info["id"])

    # Filtro de tipo
    if tipo in ("ordenanza", "decreto"):
        where_clauses.append("n.tipo = ?")
        params.append(tipo)

    # Filtro de vigencia
    if solo_vigentes:
        where_clauses.append("n.estado IN ('vigente', 'modificada')")

    where_sql = " AND ".join(where_clauses)
    
    # Consulta con conteo total aproximado y paginación
    sql = f"""
        SELECT 
            n.id,
            n.tipo,
            n.numero,
            n.anio,
            n.codigo_localidad,
            n.localidad,
            n.titulo,
            n.summary,
            n.estado,
            bm25(normas_fts) as score,
            snippet(normas_fts, 2, '<<', '>>', '...', 25) as headline
        FROM normas_fts
        JOIN normas n ON normas_fts.rowid = n.id
        WHERE {where_sql}
        ORDER BY score ASC
        LIMIT ? OFFSET ?
    """
    params.extend([limit + 1, cursor])

    rows = db.query(sql, params)
    has_more = len(rows) > limit
    items = rows[:limit]

    # Formatear items
    formatted = []
    for r in items:
        # BM25 en SQLite devuelve valores negativos (menor es mejor match)
        # Normalizamos score para presentación
        raw_bm25 = float(r["score"]) if r["score"] is not None else 0.0
        norm_score = max(0.0, 1.0 / (1.0 + abs(raw_bm25)))

        formatted.append({
            "id": r["id"],
            "tipo": r["tipo"],
            "numero": r["numero"],
            "anio": r["anio"],
            "codigo_localidad": r["codigo_localidad"],
            "localidad": r["localidad"],
            "titulo": r["titulo"],
            "resumen": r["summary"],
            "estado": r["estado"],
            "score": round(norm_score, 4),
            "headline": r["headline"],
        })

    return {
        "items": formatted,
        "returned_count": len(formatted),
        "has_more": has_more,
        "next_cursor": cursor + len(formatted) if has_more else None,
        "query": query,
        "search_method": "fts5_bm25",
        "municipio": mun_info,
    }


def search_by_category(
    db: Database,
    slug: str,
    municipio: str | int | None = None,
    anio: int | None = None,
    limit: int = 20,
    cursor: int = 0
) -> dict[str, Any]:
    """Búsqueda de normas por categoría taxonómica."""
    # 1. Obtener ID de categoría desde el índice derivado
    cat_rows = db.query_index("SELECT id, nombre, slug FROM categorias WHERE slug = ?", (slug,))
    if not cat_rows:
        return {
            "items": [],
            "returned_count": 0,
            "has_more": False,
            "error": f"Categoría '{slug}' no encontrada en la taxonomía.",
            "category": None
        }
    cat = cat_rows[0]
    cat_id = cat["id"]

    # 2. Obtener norma_ids asignados
    assign_rows = db.query_index(
        "SELECT norma_id, relevancia FROM norma_categorias WHERE categoria_id = ? ORDER BY relevancia DESC",
        (cat_id,)
    )
    if not assign_rows:
        return {
            "items": [],
            "returned_count": 0,
            "has_more": False,
            "category": cat,
        }

    norma_relevance = {r["norma_id"]: r["relevancia"] for r in assign_rows}
    norma_ids = list(norma_relevance.keys())

    # 3. Filtrar en normas
    placeholders = ",".join("?" * len(norma_ids))
    where_clauses = [f"n.id IN ({placeholders})"]
    params: list[Any] = list(norma_ids)

    mun_info = None
    if municipio is not None:
        mun_info = resolver_municipio(municipio)
        where_clauses.append("n.codigo_localidad = ?")
        params.append(mun_info["id"])

    if anio is not None:
        where_clauses.append("n.anio = ?")
        params.append(anio)

    where_sql = " AND ".join(where_clauses)
    sql = f"""
        SELECT id, tipo, numero, anio, codigo_localidad, localidad, titulo, summary, estado
        FROM normas n
        WHERE {where_sql}
        ORDER BY anio DESC, numero DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit + 1, cursor])
    rows = db.query(sql, params)

    has_more = len(rows) > limit
    items = rows[:limit]

    formatted = [{
        "id": r["id"],
        "tipo": r["tipo"],
        "numero": r["numero"],
        "anio": r["anio"],
        "codigo_localidad": r["codigo_localidad"],
        "localidad": r["localidad"],
        "titulo": r["titulo"],
        "resumen": r["summary"],
        "estado": r["estado"],
        "relevancia": norma_relevance.get(r["id"], 1.0),
        "categorias": [cat["nombre"]]
    } for r in items]

    return {
        "items": formatted,
        "returned_count": len(formatted),
        "has_more": has_more,
        "next_cursor": cursor + len(formatted) if has_more else None,
        "category": cat,
        "municipio": mun_info,
    }


def search_by_year_range(
    db: Database,
    desde: int,
    hasta: int,
    municipio: str | int | None = None,
    tipo: str = "ordenanza",
    limit: int = 20,
    cursor: int = 0
) -> dict[str, Any]:
    """Búsqueda de normas en un rango de años inclusivo."""
    where_clauses = ["n.anio BETWEEN ? AND ?"]
    params: list[Any] = [desde, hasta]

    mun_info = None
    if municipio is not None:
        mun_info = resolver_municipio(municipio)
        where_clauses.append("n.codigo_localidad = ?")
        params.append(mun_info["id"])

    if tipo in ("ordenanza", "decreto"):
        where_clauses.append("n.tipo = ?")
        params.append(tipo)

    where_sql = " AND ".join(where_clauses)
    sql = f"""
        SELECT id, tipo, numero, anio, codigo_localidad, localidad, titulo, summary, estado
        FROM normas n
        WHERE {where_sql}
        ORDER BY anio DESC, numero DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit + 1, cursor])

    rows = db.query(sql, params)
    has_more = len(rows) > limit
    items = rows[:limit]

    formatted = [{
        "id": r["id"],
        "tipo": r["tipo"],
        "numero": r["numero"],
        "anio": r["anio"],
        "codigo_localidad": r["codigo_localidad"],
        "localidad": r["localidad"],
        "titulo": r["titulo"],
        "resumen": r["summary"],
        "estado": r["estado"]
    } for r in items]

    return {
        "items": formatted,
        "returned_count": len(formatted),
        "has_more": has_more,
        "next_cursor": cursor + len(formatted) if has_more else None,
        "year_range": f"{desde}-{hasta}",
        "municipio": mun_info
    }
