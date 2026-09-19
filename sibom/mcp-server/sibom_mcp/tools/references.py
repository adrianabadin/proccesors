"""Herramienta de árbol de referencias normativas y vigencia."""
from typing import Any
from ..db import Database


def get_references(
    db: Database,
    norma_id: int,
    direccion: str = "ambas",
    profundidad: int = 1,
    limit: int = 50
) -> dict[str, Any]:
    """Obtiene el árbol de referencias normativas con control de ciclos y profundidad."""
    visited_normas: set[int] = {norma_id}
    collected_refs: list[dict[str, Any]] = []
    seen_ref_keys: set[tuple[Any, ...]] = set()

    current_queue: list[int] = [norma_id]
    current_depth = 1

    while current_queue and current_depth <= profundidad and len(collected_refs) < limit:
        next_queue: list[int] = []

        for curr_id in current_queue:
            if len(collected_refs) >= limit:
                break

            where_conditions = []
            params: list[Any] = []

            if direccion in ("ambas", "afecta_a"):
                where_conditions.append("norma_origen_id = ?")
                params.append(curr_id)

            if direccion in ("ambas", "afectada_por"):
                where_conditions.append("norma_destino_id = ?")
                params.append(curr_id)

            where_sql = " OR ".join(where_conditions)
            sql = f"""
                SELECT 
                    r.id,
                    r.norma_origen_id,
                    r.norma_destino_id,
                    r.destino_tipo,
                    r.destino_numero,
                    r.destino_anio,
                    r.destino_referencia,
                    r.tipo_relacion,
                    r.articulos_afectados,
                    r.texto_cita,
                    r.notas,
                    no.numero as origen_numero,
                    no.anio as origen_anio,
                    no.titulo as origen_titulo,
                    nd.numero as destino_num_real,
                    nd.anio as destino_anio_real,
                    nd.titulo as destino_titulo_real
                FROM referencias_normativas r
                JOIN normas no ON no.id = r.norma_origen_id
                LEFT JOIN normas nd ON nd.id = r.norma_destino_id
                WHERE {where_sql}
                ORDER BY r.id
            """
            rows = db.query(sql, params)

            for r in rows:
                if len(collected_refs) >= limit:
                    break

                # Determinar si es afecta_a o afectada_por respecto al nodo actual
                is_afecta = (r["norma_origen_id"] == curr_id)
                rel_dir = "afecta_a" if is_afecta else "afectada_por"

                # Clave única para evitar duplicados
                ref_key = (r["id"], rel_dir)
                if ref_key in seen_ref_keys:
                    continue
                seen_ref_keys.add(ref_key)

                target_id = r["norma_destino_id"] if is_afecta else r["norma_origen_id"]

                item = {
                    "id": r["id"],
                    "direccion": rel_dir,
                    "tipo_relacion": r["tipo_relacion"],
                    "norma_origen_id": r["norma_origen_id"],
                    "norma_destino_id": r["norma_destino_id"],
                    "origen": {
                        "id": r["norma_origen_id"],
                        "numero": r["origen_numero"],
                        "anio": r["origen_anio"],
                        "titulo": r["origen_titulo"]
                    },
                    "destino": {
                        "id": r["norma_destino_id"],
                        "numero": r["destino_num_real"] or r["destino_numero"],
                        "anio": r["destino_anio_real"] or r["destino_anio"],
                        "titulo": r["destino_titulo_real"],
                        "referencia_externa": r["destino_referencia"]
                    },
                    "articulos_afectados": r["articulos_afectados"],
                    "texto_cita": r["texto_cita"],
                    "notas": r["notas"],
                    "profundidad": current_depth
                }
                collected_refs.append(item)

                # Si el nodo destino es una norma interna no visitada, encolar para profundidad siguiente
                if target_id is not None and target_id not in visited_normas:
                    visited_normas.add(target_id)
                    next_queue.append(target_id)

        current_queue = next_queue
        current_depth += 1

    return {
        "norma_id": norma_id,
        "direccion": direccion,
        "profundidad_maxima": profundidad,
        "total_referencias": len(collected_refs),
        "referencias": collected_refs,
    }
