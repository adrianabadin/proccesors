"""Herramientas de búsqueda semántica sobre normas y artículos individuales."""
from typing import Any
import numpy as np
from ..db import Database
from ..municipios import resolver_municipio
from ..embeddings import get_embedding_model, parse_blob_to_vector
from ..cache import query_cache
from ..vectors import compute_top_k, reciprocal_rank_fusion


def _get_query_vector(query: str, model_name: str | None = None, mock: bool = False) -> np.ndarray:
    """Obtiene el vector normalizado de la consulta, utilizando caché."""
    model_key = "mock" if mock else (model_name or "default")
    cached = query_cache.get(query, model_key)
    if cached is not None:
        return cached

    model = get_embedding_model(model_name, mock=mock)
    vec = model.encode(query, normalize_embeddings=True)
    query_cache.set(query, model_key, vec)
    return vec


def semantic_search(
    db: Database,
    query: str,
    municipio: str | int | None = None,
    tipo: str = "ordenanza",
    solo_vigentes: bool = False,
    limit: int = 10,
    umbral: float = 0.4,
    mock: bool = False
) -> dict[str, Any]:
    """Búsqueda semántica sobre normas completas usando embeddings pre-calculados."""
    query_vec = _get_query_vector(query, mock=mock)

    # Construir filtros SQL antes del escaneo vectorial
    where_clauses = ["embedding_summary IS NOT NULL"]
    params: list[Any] = []

    mun_info = None
    if municipio is not None:
        mun_info = resolver_municipio(municipio)
        where_clauses.append("codigo_localidad = ?")
        params.append(mun_info["id"])

    if tipo in ("ordenanza", "decreto"):
        where_clauses.append("tipo = ?")
        params.append(tipo)

    if solo_vigentes:
        where_clauses.append("estado IN ('vigente', 'modificada')")

    where_sql = " AND ".join(where_clauses)
    sql = f"""
        SELECT id, tipo, numero, anio, codigo_localidad, localidad, titulo, summary, estado, embedding_summary
        FROM normas
        WHERE {where_sql}
    """
    rows = db.query(sql, params)

    if not rows:
        return {
            "items": [],
            "returned_count": 0,
            "query": query,
            "umbral": umbral,
            "municipio": mun_info,
            "search_method": "semantic_normas"
        }

    valid_ids = []
    vector_list = []
    row_map = {}

    for r in rows:
        vec = parse_blob_to_vector(r["embedding_summary"])
        if vec is not None:
            valid_ids.append(r["id"])
            vector_list.append(vec)
            row_map[r["id"]] = r

    if not vector_list:
        return {
            "items": [],
            "returned_count": 0,
            "query": query,
            "umbral": umbral,
            "municipio": mun_info,
            "search_method": "semantic_normas"
        }

    matrix = np.vstack(vector_list)
    top_matches = compute_top_k(query_vec, matrix, valid_ids, limit=limit, umbral=umbral)

    items = []
    for norma_id, score in top_matches:
        r = row_map[norma_id]
        items.append({
            "id": r["id"],
            "tipo": r["tipo"],
            "numero": r["numero"],
            "anio": r["anio"],
            "codigo_localidad": r["codigo_localidad"],
            "localidad": r["localidad"],
            "titulo": r["titulo"],
            "resumen": r["summary"],
            "estado": r["estado"],
            "score": round(score, 4)
        })

    return {
        "items": items,
        "returned_count": len(items),
        "query": query,
        "umbral": umbral,
        "municipio": mun_info,
        "search_method": "semantic_normas"
    }


def semantic_search_articulos(
    db: Database,
    query: str,
    municipio: str | int | None = None,
    solo_vigentes: bool = False,
    limit: int = 10,
    umbral: float = 0.4,
    mock: bool = False
) -> dict[str, Any]:
    """Búsqueda semántica a nivel de artículo individual en el índice derivado."""
    query_vec = _get_query_vector(query, mock=mock)

    where_clauses = ["1=1"]
    params: list[Any] = []

    mun_info = None
    if municipio is not None:
        mun_info = resolver_municipio(municipio)
        where_clauses.append("ae.codigo_localidad = ?")
        params.append(mun_info["id"])

    where_sql = " AND ".join(where_clauses)
    sql_index = f"""
        SELECT ae.articulo_id, ae.norma_id, ae.codigo_localidad, ae.embedding
        FROM articulo_embeddings ae
        WHERE {where_sql}
    """
    rows = db.query_index(sql_index, params)

    if not rows:
        return {
            "items": [],
            "returned_count": 0,
            "query": query,
            "umbral": umbral,
            "municipio": mun_info,
            "search_method": "semantic_articulos"
        }

    valid_ids = []
    vector_list = []
    art_meta = {}

    for r in rows:
        vec = parse_blob_to_vector(r["embedding"])
        if vec is not None:
            valid_ids.append(r["articulo_id"])
            vector_list.append(vec)
            art_meta[r["articulo_id"]] = {
                "norma_id": r["norma_id"],
                "codigo_localidad": r["codigo_localidad"]
            }

    if not vector_list:
        return {
            "items": [],
            "returned_count": 0,
            "query": query,
            "umbral": umbral,
            "municipio": mun_info,
            "search_method": "semantic_articulos"
        }

    matrix = np.vstack(vector_list)
    top_matches = compute_top_k(query_vec, matrix, valid_ids, limit=limit * 2, umbral=umbral)

    if not top_matches:
        return {
            "items": [],
            "returned_count": 0,
            "query": query,
            "umbral": umbral,
            "municipio": mun_info,
            "search_method": "semantic_articulos"
        }

    # Cargar textos y detalles de artículos desde base fuente
    art_ids = [m[0] for m in top_matches]
    placeholders = ",".join("?" * len(art_ids))
    art_rows = db.query(f"""
        SELECT a.id, a.norma_id, a.numero_articulo, a.texto, a.estado as articulo_estado,
               n.numero as norma_numero, n.anio as norma_anio, n.titulo as norma_titulo, n.estado as norma_estado,
               n.localidad, n.codigo_localidad
        FROM articulos a
        JOIN normas n ON a.norma_id = n.id
        WHERE a.id IN ({placeholders})
    """, art_ids)

    art_row_map = {r["id"]: r for r in art_rows}
    items = []

    for art_id, score in top_matches:
        if art_id not in art_row_map:
            continue
        ar = art_row_map[art_id]

        if solo_vigentes and ar["norma_estado"] not in ("vigente", "modificada"):
            continue

        items.append({
            "articulo_id": ar["id"],
            "norma_id": ar["norma_id"],
            "numero_articulo": ar["numero_articulo"],
            "texto": ar["texto"],
            "score": round(score, 4),
            "norma": {
                "numero": ar["norma_numero"],
                "anio": ar["norma_anio"],
                "titulo": ar["norma_titulo"],
                "estado": ar["norma_estado"],
                "localidad": ar["localidad"]
            }
        })
        if len(items) >= limit:
            break

    return {
        "items": items,
        "returned_count": len(items),
        "query": query,
        "umbral": umbral,
        "municipio": mun_info,
        "search_method": "semantic_articulos"
    }


def full_semantic_search(
    db: Database,
    query: str,
    municipio: str | int | None = None,
    solo_vigentes: bool = False,
    limit: int = 10,
    umbral: float = 0.4,
    mock: bool = False
) -> dict[str, Any]:
    """Búsqueda semántica combinada de normas y artículos individuales."""
    res_normas = semantic_search(
        db=db,
        query=query,
        municipio=municipio,
        tipo="todos",
        solo_vigentes=solo_vigentes,
        limit=limit * 2,
        umbral=umbral,
        mock=mock
    )
    res_articulos = semantic_search_articulos(
        db=db,
        query=query,
        municipio=municipio,
        solo_vigentes=solo_vigentes,
        limit=limit * 2,
        umbral=umbral,
        mock=mock
    )

    combined = []
    for item in res_normas["items"]:
        combined.append({
            "identity_type": "norma",
            "id": item["id"],
            "norma_id": item["id"],
            "titulo": item["titulo"],
            "resumen": item["resumen"],
            "numero": item["numero"],
            "anio": item["anio"],
            "localidad": item["localidad"],
            "score": item["score"],
            "estado": item["estado"]
        })

    for item in res_articulos["items"]:
        combined.append({
            "identity_type": "articulo",
            "id": item["articulo_id"],
            "articulo_id": item["articulo_id"],
            "norma_id": item["norma_id"],
            "numero_articulo": item["numero_articulo"],
            "texto": item["texto"],
            "norma": item["norma"],
            "score": item["score"],
            "estado": item["norma"]["estado"]
        })

    # Ordenar combinados por score descendente
    combined.sort(key=lambda x: x["score"], reverse=True)
    top_items = combined[:limit]

    return {
        "items": top_items,
        "returned_count": len(top_items),
        "total_normas_found": len(res_normas["items"]),
        "total_articulos_found": len(res_articulos["items"]),
        "query": query,
        "umbral": umbral,
        "search_method": "full_semantic_hybrid"
    }
