"""Herramienta para compilación temática y generación de dossiers normativos."""
from typing import Any
from ..db import Database
from ..municipios import resolver_municipio
from .search import search_normas


def compilar_tematica(
    db: Database,
    tema: str,
    municipios: list[str | int] | None = None,
    desde: int | None = None,
    hasta: int | None = None,
    tipo: str = "ordenanza",
    solo_vigentes: bool = False,
    cursor: int = 0,
    limit: int = 20
) -> dict[str, Any]:
    """Compila un dossier normativo temático estructurado y en Markdown."""
    # 1. Resolver filtros municipales
    codigos_municipios = []
    mun_infos = []
    if municipios:
        for m in municipios:
            info = resolver_municipio(m)
            codigos_municipios.append(info["id"])
            mun_infos.append(info)

    # 2. Recuperar candidatos mediante búsqueda textual FTS5
    # Buscamos con un margen más amplio para deduplicar y paginar limpiamente
    search_limit = 100
    fts_res = search_normas(
        db=db,
        query=tema,
        municipio=codigos_municipios[0] if len(codigos_municipios) == 1 else None,
        tipo=tipo,
        solo_vigentes=solo_vigentes,
        limit=search_limit
    )

    candidatos = fts_res["items"]

    # Si hay múltiples municipios, filtrar adicionalmente en memoria
    if len(codigos_municipios) > 1:
        candidatos = [c for c in candidatos if c["codigo_localidad"] in codigos_municipios]

    # Filtro por rango de años si fue especificado
    if desde is not None:
        candidatos = [c for c in candidatos if c["anio"] is None or c["anio"] >= desde]
    if hasta is not None:
        candidatos = [c for c in candidatos if c["anio"] is None or c["anio"] <= hasta]

    total_candidates = len(candidatos)
    paginated_items = candidatos[cursor : cursor + limit]
    has_more = (cursor + limit) < total_candidates
    next_cursor = (cursor + limit) if has_more else None

    # 3. Cargar artículos, relaciones y anexos para cada norma seleccionada
    dossier_normas = []
    for c in paginated_items:
        norma_id = c["id"]
        
        # Cargar artículos
        articulos = db.query(
            "SELECT id, numero_articulo, orden, texto, estado FROM articulos WHERE norma_id = ? ORDER BY orden",
            (norma_id,)
        )

        # Cargar referencias normativas
        referencias = db.query("""
            SELECT tipo_relacion, destino_referencia, destino_numero, destino_anio, articulos_afectados, texto_cita
            FROM referencias_normativas
            WHERE norma_origen_id = ?
        """, (norma_id,))

        # Cargar anexos
        anexos = db.query("SELECT id, nombre, url FROM anexos WHERE norma_id = ?", (norma_id,))

        dossier_normas.append({
            "id": norma_id,
            "tipo": c["tipo"],
            "numero": c["numero"],
            "anio": c["anio"],
            "localidad": c["localidad"],
            "titulo": c["titulo"],
            "resumen": c["resumen"],
            "estado": c["estado"],
            "score": c["score"],
            "articulos": articulos,
            "referencias": referencias,
            "anexos": anexos
        })

    # 4. Construir versión Markdown legible
    md_lines = [
        f"# Dossier Temático Normativo: {tema.title()}",
        f"**Tipo de norma:** {tipo} | **Candidatos recuperados:** {total_candidates} (Mostrando {len(paginated_items)})",
        "---",
        "## Inventario de Normas Relevantes\n"
    ]

    for n in dossier_normas:
        num_str = f"N° {n['numero']}/{n['anio']}" if n['numero'] and n['anio'] else f"ID {n['id']}"
        md_lines.append(f"### [{n['localidad']}] {n['tipo'].capitalize()} {num_str}: {n['titulo']}")
        md_lines.append(f"- **Estado:** `{n['estado']}` | **Score relevancia:** {n['score']}")
        if n['resumen']:
            md_lines.append(f"- **Resumen:** {n['resumen']}")
        
        if n['articulos']:
            md_lines.append("\n**Articulado relevante:**")
            for a in n['articulos'][:5]:  # Mostrar los primeros 5 artículos
                md_lines.append(f"  - **Art. {a['numero_articulo']}:** {a['texto'][:250]}...")

        if n['referencias']:
            md_lines.append("\n**Relaciones y Citas:**")
            for r in n['referencias']:
                dest = r['destino_referencia'] or f"N° {r['destino_numero']}/{r['destino_anio']}"
                md_lines.append(f"  - *{r['tipo_relacion']}* a {dest}: {r['texto_cita'] or ''}")

        if n['anexos']:
            md_lines.append("\n**Anexos:**")
            for ax in n['anexos']:
                md_lines.append(f"  - [{ax['nombre']}]({ax['url']})")

        md_lines.append("\n---\n")

    md_lines.append(
        "\n> **Aviso Legal:** Esta compilación es una agrupación técnica con fines de estudio e investigación. "
        "No constituye un texto consolidado oficial ni certifica vigencia jurídica definitiva."
    )

    return {
        "tema": tema,
        "total_candidates": total_candidates,
        "returned_count": len(dossier_normas),
        "has_more": has_more,
        "next_cursor": next_cursor,
        "normas": dossier_normas,
        "dossier_markdown": "\n".join(md_lines),
        "cobertura": {
            "municipios_incluidos": mun_infos or "Todos",
            "periodo": f"{desde or 'Inicio'}-{hasta or 'Presente'}",
            "tipo": tipo
        }
    }
