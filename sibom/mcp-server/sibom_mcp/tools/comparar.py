"""Herramienta para comparación de antecedentes normativos intermunicipales."""
from typing import Any
import numpy as np
from ..db import Database
from ..municipios import resolver_municipio
from ..embeddings import parse_blob_to_vector
from ..vectors import compute_top_k
from .search import search_normas


def comparar_intermunicipal(
    db: Database,
    tema: str,
    municipio_destino: str | int = 108,
    municipios_referencia: list[str | int] | None = None,
    periodo_desde: int | None = None,
    limit_candidatos: int = 20,
    mock: bool = False
) -> dict[str, Any]:
    """Compara antecedentes normativos entre municipios de referencia y un municipio destino."""
    # 1. Resolver municipio destino
    dest_info = resolver_municipio(municipio_destino)
    dest_id = dest_info["id"]

    # 2. Resolver municipios de referencia
    all_mun_rows = db.query("SELECT DISTINCT codigo_localidad, localidad FROM normas")
    available_mun_ids = [r["codigo_localidad"] for r in all_mun_rows if r["codigo_localidad"] != dest_id]

    ref_ids = []
    ref_infos = []
    if municipios_referencia:
        for m in municipios_referencia:
            info = resolver_municipio(m)
            if info["id"] != dest_id:
                ref_ids.append(info["id"])
                ref_infos.append(info)
    else:
        ref_ids = available_mun_ids
        for mid in ref_ids:
            try:
                ref_infos.append(resolver_municipio(mid))
            except Exception:
                pass

    if not ref_ids:
        return {
            "tema": tema,
            "municipio_destino": dest_info,
            "municipios_referencia": [],
            "candidatos_analizados": 0,
            "comparaciones": [],
            "status": "evidencia_insuficiente",
            "mensaje": "No se encontraron municipios de referencia para comparar."
        }

    # 3. Buscar candidatos externos en municipios de referencia
    candidatos_externos = []
    for r_id in ref_ids:
        res = search_normas(db=db, query=tema, municipio=r_id, tipo="todos", limit=limit_candidatos)
        for item in res["items"]:
            if periodo_desde is not None and item["anio"] is not None and item["anio"] < periodo_desde:
                continue
            candidatos_externos.append(item)
            if len(candidatos_externos) >= limit_candidatos:
                break
        if len(candidatos_externos) >= limit_candidatos:
            break

    if not candidatos_externos:
        return {
            "tema": tema,
            "municipio_destino": dest_info,
            "municipios_referencia": ref_infos,
            "candidatos_analizados": 0,
            "comparaciones": [],
            "status": "evidencia_insuficiente",
            "mensaje": f"No se hallaron antecedentes sobre '{tema}' en los municipios de referencia consultados."
        }

    # 4. Obtener corpus y vectores del municipio destino para matching
    dest_normas = db.query(
        "SELECT id, numero, anio, titulo, summary, embedding_summary, estado FROM normas WHERE codigo_localidad = ?",
        (dest_id,)
    )

    dest_vectors = []
    dest_ids = []
    dest_map = {}
    for dn in dest_normas:
        dest_map[dn["id"]] = dn
        v = parse_blob_to_vector(dn["embedding_summary"])
        if v is not None:
            dest_vectors.append(v)
            dest_ids.append(dn["id"])

    dest_matrix = np.vstack(dest_vectors) if dest_vectors else None

    # 5. Contrastar cada candidato externo contra el destino (Vectorial + FTS)
    analisis_comparativo = []

    for ext in candidatos_externos:
        candidato_id = ext["id"]
        candidato_titulo = ext["titulo"]
        candidato_resumen = ext["resumen"] or ""

        # Obtener vector del candidato si existe
        ext_row = db.query("SELECT embedding_summary FROM normas WHERE id = ?", (candidato_id,))
        ext_blob = ext_row[0]["embedding_summary"] if ext_row else None
        ext_vec = parse_blob_to_vector(ext_blob)

        # A) Búsqueda por similitud vectorial en destino
        vector_match = None
        vector_score = 0.0
        if ext_vec is not None and dest_matrix is not None and len(dest_ids) > 0:
            top_dest = compute_top_k(ext_vec, dest_matrix, dest_ids, limit=1, umbral=0.0)
            if top_dest:
                match_id, score = top_dest[0]
                vector_score = round(score, 4)
                vector_match = dest_map.get(match_id)

        # B) Búsqueda léxica (FTS) en destino por palabras clave del título
        fts_match = None
        clean_terms = " ".join([w for w in candidato_titulo.split() if len(w) > 4][:4])
        if clean_terms:
            fts_res = search_normas(db=db, query=clean_terms, municipio=dest_id, tipo="todos", limit=1)
            if fts_res["items"]:
                fts_match = fts_res["items"][0]

        # Determinar estado de equivalencia
        estado_resultado = "posible_brecha"
        mejor_antecedente = None
        confianza = 0.0

        if vector_score >= 0.75 and vector_match:
            estado_resultado = "equivalente_encontrado"
            mejor_antecedente = {
                "id": vector_match["id"],
                "numero": vector_match["numero"],
                "anio": vector_match["anio"],
                "titulo": vector_match["titulo"],
                "estado": vector_match["estado"],
                "score": vector_score,
                "canal": "vectorial"
            }
            confianza = vector_score
        elif fts_match and fts_match["score"] > 0.6:
            estado_resultado = "equivalente_encontrado"
            mejor_antecedente = {
                "id": fts_match["id"],
                "numero": fts_match["numero"],
                "anio": fts_match["anio"],
                "titulo": fts_match["titulo"],
                "estado": fts_match["estado"],
                "score": fts_match["score"],
                "canal": "fts_bm25"
            }
            confianza = fts_match["score"]
        elif vector_match and vector_score >= 0.50:
            estado_resultado = "equivalente_encontrado"
            mejor_antecedente = {
                "id": vector_match["id"],
                "numero": vector_match["numero"],
                "anio": vector_match["anio"],
                "titulo": vector_match["titulo"],
                "estado": vector_match["estado"],
                "score": vector_score,
                "canal": "vectorial_moderado"
            }
            confianza = vector_score
        else:
            estado_resultado = "posible_brecha"
            if vector_match:
                mejor_antecedente = {
                    "id": vector_match["id"],
                    "numero": vector_match["numero"],
                    "anio": vector_match["anio"],
                    "titulo": vector_match["titulo"],
                    "score": vector_score,
                    "canal": "vectorial_bajo"
                }

        analisis_comparativo.append({
            "candidato_referencia": {
                "id": ext["id"],
                "localidad": ext["localidad"],
                "tipo": ext["tipo"],
                "numero": ext["numero"],
                "anio": ext["anio"],
                "titulo": ext["titulo"],
                "resumen": ext["resumen"]
            },
            "estado_resultado": estado_resultado,
            "confianza": confianza,
            "antecedente_destino": mejor_antecedente,
            "diferencias_observables": (
                f"El municipio de referencia ({ext['localidad']}) cuenta con regulación específica. "
                + (f"En {dest_info['nombre']} se detectó antecedente similar ({mejor_antecedente['titulo']})."
                   if estado_resultado == "equivalente_encontrado"
                   else f"No se encontró normativa análoga directa en el corpus indexado de {dest_info['nombre']}.")
            ),
            "aspectos_adaptacion": (
                "Verificar marco de ordenamiento territorial, fuentes de financiamiento local y adecuación orgánica."
            )
        })

    return {
        "tema": tema,
        "municipio_destino": dest_info,
        "municipios_referencia": ref_infos,
        "candidatos_analizados": len(analisis_comparativo),
        "comparaciones": analisis_comparativo,
        "cobertura": {
            "normas_destino_evaluadas": len(dest_normas),
            "vectores_destino_disponibles": len(dest_ids)
        },
        "aviso_metodologico": (
            "La detección de posibles brechas o equivalencias es un análisis automatizado de precedentes. "
            "No certifica inexistencia normativa formal ni validez jurídica de aplicabilidad directa."
        )
    }
