"""Herramientas de detalle de normas y anexos para SIBOM."""
import os
from pathlib import Path
from typing import Any
from ..db import Database
from ..config import settings


def get_norma(db: Database, norma_id: int) -> dict[str, Any]:
    """Obtiene el detalle completo de una norma por ID."""
    rows = db.query("SELECT * FROM normas WHERE id = ?", (norma_id,))
    if not rows:
        raise ValueError(f"No se encontró norma con ID: {norma_id}")

    n = rows[0]

    # Artículos
    articulos = db.query(
        "SELECT id, numero_articulo, orden, texto, resumen, estado FROM articulos WHERE norma_id = ? ORDER BY orden",
        (norma_id,)
    )

    # Referencias
    referencias = db.query("""
        SELECT 
            id,
            tipo_relacion,
            norma_destino_id,
            destino_tipo,
            destino_numero,
            destino_anio,
            destino_referencia,
            articulos_afectados,
            texto_cita,
            notas
        FROM referencias_normativas
        WHERE norma_origen_id = ?
        ORDER BY id
    """, (norma_id,))

    # Anexos
    anexos = db.query("SELECT id, nombre, archivo_pdf, url FROM anexos WHERE norma_id = ? ORDER BY id", (norma_id,))

    # Categorías asociadas desde el índice derivado
    cat_names = []
    try:
        cats = db.query_index("""
            SELECT c.nombre, c.slug, nc.relevancia
            FROM norma_categorias nc
            JOIN categorias c ON c.id = nc.categoria_id
            WHERE nc.norma_id = ?
            ORDER BY nc.relevancia DESC
        """, (norma_id,))
        cat_names = [c["nombre"] for c in cats]
    except Exception:
        pass

    return {
        "id": n["id"],
        "tipo": n["tipo"],
        "numero": n["numero"],
        "anio": n["anio"],
        "numero_sibom": n.get("numero_sibom"),
        "fecha": n.get("fecha"),
        "boletin": n.get("boletin"),
        "version": n["version"],
        "codigo_localidad": n["codigo_localidad"],
        "localidad": n["localidad"],
        "titulo": n["titulo"],
        "seccion_visto": n.get("seccion_visto"),
        "seccion_considerando": n.get("seccion_considerando"),
        "texto_completo": n["texto_completo"],
        "estado": n["estado"],
        "notas_vigencia": n.get("notas_vigencia"),
        "summary": n.get("summary"),
        "summary_trata": n.get("summary_trata"),
        "summary_resuelve": n.get("summary_resuelve"),
        "summary_depende": n.get("summary_depende"),
        "url": n["url"],
        "archivo_md": n["archivo_md"],
        "articulos": articulos,
        "referencias": referencias,
        "anexos": anexos,
        "categorias": cat_names
    }


def get_anexo(
    db: Database,
    anexo_id: int | None = None,
    norma_id: int | None = None,
    anexo_numero: str | None = None,
    anexos_dir: str | Path | None = None
) -> dict[str, Any]:
    """Obtiene metadatos y texto extraído de un anexo de forma segura."""
    if anexo_id is not None:
        rows = db.query("SELECT * FROM anexos WHERE id = ?", (anexo_id,))
    elif norma_id is not None and anexo_numero is not None:
        rows = db.query(
            "SELECT * FROM anexos WHERE norma_id = ? AND (nombre LIKE ? OR archivo_pdf LIKE ?)",
            (norma_id, f"%{anexo_numero}%", f"%{anexo_numero}%")
        )
    elif norma_id is not None:
        rows = db.query("SELECT * FROM anexos WHERE norma_id = ? LIMIT 1", (norma_id,))
    else:
        raise ValueError("Debe especificarse anexo_id o norma_id")

    if not rows:
        raise ValueError("No se encontró el anexo solicitado")

    anexo = rows[0]
    base_dir = Path(anexos_dir or settings.anexos_dir).resolve()

    texto_extraido = None
    texto_disponible = False
    archivo_local = None

    if anexo.get("archivo_pdf"):
        # Validación estricta anti path-traversal
        pdf_path = (base_dir / anexo["archivo_pdf"]).resolve()
        try:
            pdf_path.relative_to(base_dir)
            if pdf_path.exists() and pdf_path.is_file():
                archivo_local = str(pdf_path)
                # Intentar extracción si pypdf está disponible
                try:
                    import pypdf
                    reader = pypdf.PdfReader(str(pdf_path))
                    pages_text = [p.extract_text() or "" for p in reader.pages[:10]]
                    extracted = "\n".join(pages_text).strip()
                    if extracted:
                        texto_extraido = extracted
                        texto_disponible = True
                except Exception:
                    pass
        except ValueError:
            # Intento de path traversal fuera del directorio base
            pass

    return {
        "id": anexo["id"],
        "norma_id": anexo["norma_id"],
        "nombre": anexo["nombre"],
        "archivo_pdf": anexo.get("archivo_pdf"),
        "archivo_local": archivo_local,
        "url": anexo["url"],
        "texto_extraido": texto_extraido,
        "texto_disponible": texto_disponible,
        "status": "ok" if texto_disponible else "text_unavailable"
    }
