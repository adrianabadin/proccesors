"""Herramienta de búsqueda de normas semánticamente similares."""
from typing import Any
import numpy as np
from ..db import Database
from ..municipios import resolver_municipio
from ..embeddings import parse_blob_to_vector
from ..vectors import compute_top_k


def similar_normas(
    db: Database,
    norma_id: int,
    municipio: str | int | None = None,
    limit: int = 10,
    umbral: float = 0.5
) -> dict[str, Any]:
    """Encuentra normas semánticamente similares excluyendo la norma consultada."""
    # 1. Obtener vector de referencia
    ref_rows = db.query(
        "SELECT id, titulo, embedding_summary, embedding_texto FROM normas WHERE id = ?",
        (norma_id,)
    )
    if not ref_rows:
        raise ValueError(f"No se encontró la norma de referencia con ID: {norma_id}")

    ref = ref_rows[0]
    ref_blob = ref["embedding_summary"] or ref["embedding_texto"]
    if not ref_blob:
        return {
            "items": [],
            "returned_count": 0,
            "norma_id": norma_id,
            "warning": "La norma de referencia no cuenta con vector de embeddings registrado."
        }

    ref_vec = parse_blob_to_vector(ref_blob)
    if ref_vec is None:
        return {
            "items": [],
            "returned_count": 0,
            "norma_id": norma_id,
            "warning": "El vector de embeddings de la norma de referencia es inválido o incompatible."
        }

    # 2. Obtener vectores candidatos (excluyendo norma_id)
    where_clauses = ["id != ?", "embedding_summary IS NOT NULL"]
    params: list[Any] = [norma_id]

    mun_info = None
    if municipio is not None:
        mun_info = resolver_municipio(municipio)
        where_clauses.append("codigo_localidad = ?")
        params.append(mun_info["id"])

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
            "norma_id": norma_id,
            "umbral": umbral,
            "municipio": mun_info
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
            "norma_id": norma_id,
            "umbral": umbral,
            "municipio": mun_info
        }

    matrix = np.vstack(vector_list)
    top_matches = compute_top_k(ref_vec, matrix, valid_ids, limit=limit, umbral=umbral)

    items = []
    for match_id, score in top_matches:
        r = row_map[match_id]
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
        "norma_id": norma_id,
        "norma_referencia_titulo": ref["titulo"],
        "umbral": umbral,
        "municipio": mun_info
    }
