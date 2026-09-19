"""Herramienta de estadísticas y métricas del corpus SIBOM."""
from typing import Any
from ..db import Database
from ..municipios import resolver_municipio


def get_stats(db: Database, municipio: str | int | None = None) -> dict[str, Any]:
    """Calcula estadísticas generales o filtradas por municipio sobre SIBOM."""
    where_sql = ""
    params: list[Any] = []
    mun_info = None

    if municipio is not None:
        mun_info = resolver_municipio(municipio)
        where_sql = "WHERE codigo_localidad = ?"
        params = [mun_info["id"]]

    # 1. Totales por tipo
    tipo_rows = db.query(
        f"SELECT tipo, count(*) as cnt FROM normas {where_sql} GROUP BY tipo",
        params
    )
    totales_por_tipo = {r["tipo"]: r["cnt"] for r in tipo_rows}
    total_normas = sum(totales_por_tipo.values())

    # 2. Cobertura de embeddings
    emb_rows = db.query(
        f"""
        SELECT 
            count(embedding_summary) as con_resumen_vec,
            count(embedding_texto) as con_texto_vec,
            count(summary) as con_summary_llm
        FROM normas {where_sql}
        """,
        params
    )
    emb_stats = emb_rows[0] if emb_rows else {"con_resumen_vec": 0, "con_texto_vec": 0, "con_summary_llm": 0}

    # 3. Distribución por municipio (si no se filtró por uno)
    municipios_dist = []
    if municipio is None:
        mun_rows = db.query(
            "SELECT codigo_localidad, localidad, count(*) as cnt FROM normas GROUP BY codigo_localidad, localidad ORDER BY cnt DESC"
        )
        municipios_dist = [{
            "codigo": r["codigo_localidad"],
            "localidad": r["localidad"],
            "total": r["cnt"]
        } for r in mun_rows]

    # 4. Distribución por año (top 20)
    where_anio = f"{where_sql} AND anio IS NOT NULL" if where_sql else "WHERE anio IS NOT NULL"
    anio_rows = db.query(
        f"""
        SELECT anio, count(*) as cnt 
        FROM normas {where_anio}
        GROUP BY anio 
        ORDER BY anio DESC 
        LIMIT 20
        """,
        params
    )
    dist_por_anio = [{"anio": r["anio"], "total": r["cnt"]} for r in anio_rows]

    # Conteo de años nulos
    null_anio_rows = db.query(
        f"SELECT count(*) as cnt FROM normas {where_sql} {'AND' if where_sql else 'WHERE'} anio IS NULL",
        params
    )
    anios_desconocidos = null_anio_rows[0]["cnt"] if null_anio_rows else 0

    # 5. Métricas del índice derivado (categorías y artículos vectorizados)
    categorias_total = 0
    articulos_vectorizados = 0
    try:
        cat_count_rows = db.query_index("SELECT count(*) as cnt FROM categorias")
        categorias_total = cat_count_rows[0]["cnt"] if cat_count_rows else 0

        art_count_rows = db.query_index("SELECT count(*) as cnt FROM articulo_embeddings")
        articulos_vectorizados = art_count_rows[0]["cnt"] if art_count_rows else 0
    except Exception:
        pass

    return {
        "total_normas": total_normas,
        "ordenanzas": totales_por_tipo.get("ordenanza", 0),
        "decretos": totales_por_tipo.get("decreto", 0),
        "cobertura_embeddings": {
            "embedding_summary": emb_stats["con_resumen_vec"],
            "embedding_texto": emb_stats["con_texto_vec"],
            "summary_llm": emb_stats["con_summary_llm"]
        },
        "anios_desconocidos": anios_desconocidos,
        "distribucion_por_municipio": municipios_dist,
        "distribucion_por_anio": dist_por_anio,
        "indice_derivado": {
            "total_categorias": categorias_total,
            "articulos_vectorizados": articulos_vectorizados
        },
        "municipio_filtro": mun_info
    }
