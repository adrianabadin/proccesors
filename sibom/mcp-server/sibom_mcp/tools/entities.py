"""Herramienta para buscar normas que mencionen una entidad específica."""
from typing import Any
from ..db import Database
from ..municipios import resolver_municipio


def search_by_entity(
    db: Database,
    nombre: str,
    tipo: str | None = None,
    municipio: str | int | None = None,
    limit: int = 20
) -> dict[str, Any]:
    """Busca normas asociadas a una entidad (persona, empresa u organismo) con evidencia."""
    # 1. Buscar entidades que coincidan por nombre o slug en index_db
    where_ent = ["(nombre LIKE ? OR slug LIKE ?)"]
    term = f"%{nombre.strip().lower()}%"
    params_ent: list[Any] = [term, term]

    if tipo is not None:
        where_ent.append("tipo = ?")
        params_ent.append(tipo.strip().lower())

    sql_ent = f"SELECT id, nombre, slug, tipo FROM entidades WHERE {' AND '.join(where_ent)}"
    ent_rows = db.query_index(sql_ent, params_ent)

    if not ent_rows:
        return {
            "items": [],
            "returned_count": 0,
            "entity": nombre,
            "tipo": tipo,
            "message": f"No se encontraron entidades coincidentes con '{nombre}'."
        }

    ent_ids = [e["id"] for e in ent_rows]
    ent_map = {e["id"]: e for e in ent_rows}

    # 2. Buscar menciones en norma_entidades
    placeholders = ",".join("?" * len(ent_ids))
    sql_menciones = f"""
        SELECT norma_id, entidad_id, rol, contexto
        FROM norma_entidades
        WHERE entidad_id IN ({placeholders})
    """
    menciones = db.query_index(sql_menciones, ent_ids)
    if not menciones:
        return {
            "items": [],
            "returned_count": 0,
            "entity": nombre,
            "tipo": tipo,
            "message": "Entidad encontrada en el catálogo pero sin normas asociadas registradas."
        }

    norma_ids = list({m["norma_id"] for m in menciones})
    mencion_map = {m["norma_id"]: m for m in menciones}

    # 3. Filtrar y obtener datos de normas desde base principal
    norma_placeholders = ",".join("?" * len(norma_ids))
    where_norma = [f"id IN ({norma_placeholders})"]
    params_norma: list[Any] = list(norma_ids)

    mun_info = None
    if municipio is not None:
        mun_info = resolver_municipio(municipio)
        where_norma.append("codigo_localidad = ?")
        params_norma.append(mun_info["id"])

    sql_normas = f"""
        SELECT id, tipo, numero, anio, codigo_localidad, localidad, titulo, summary, estado
        FROM normas
        WHERE {' AND '.join(where_norma)}
        ORDER BY anio DESC, numero DESC
        LIMIT ?
    """
    params_norma.append(limit)
    norma_rows = db.query(sql_normas, params_norma)

    items = []
    for n in norma_rows:
        m = mencion_map.get(n["id"])
        ent_info = ent_map.get(m["entidad_id"]) if m else {}
        items.append({
            "id": n["id"],
            "tipo": n["tipo"],
            "numero": n["numero"],
            "anio": n["anio"],
            "codigo_localidad": n["codigo_localidad"],
            "localidad": n["localidad"],
            "titulo": n["titulo"],
            "resumen": n["summary"],
            "estado": n["estado"],
            "entidad": {
                "nombre": ent_info.get("nombre"),
                "tipo": ent_info.get("tipo"),
                "rol": m.get("rol") if m else None,
                "evidencia": m.get("contexto") if m else None
            }
        })

    return {
        "items": items,
        "returned_count": len(items),
        "entity": nombre,
        "tipo": tipo,
        "municipio": mun_info
    }
