#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ingesta masiva de archivos Markdown y Anexos en SQLite (sibom.db).

Soporta múltiples municipios (ej: --municipio 108 Saladillo, --municipio 130 Veinticinco de Mayo).
1. Parsea YAML front-matter y cuerpo de cada archivo .md.
2. Extrae secciones VISTO y CONSIDERANDO.
3. Para decretos extractados, prellena summary oficial y marca procesado_llm = 2.
4. Para normas completas, marca procesado_llm = 0 (pendientes para GLM Flash).
5. Asocia anexos de contenidos.json a su norma correspondiente.
6. Permite ingesta incremental o con reemplazo selectivo por municipio.
"""

import argparse
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.sibom_municipios import (
    resolver_municipio,
    get_municipio_rutas,
    listar_municipios_descargados,
    DB_PATH,
)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Separa el bloque YAML front-matter del cuerpo Markdown."""
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    yaml_raw = parts[1].strip()
    body = parts[2].strip()

    metadata = {}
    for line in yaml_raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()

            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            elif val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                val = [item.strip().strip("'\"") for item in inner.split(",") if item.strip()] if inner else []
            elif val.lower() == "true":
                val = True
            elif val.lower() == "false":
                val = False
            elif val.isdigit():
                val = int(val)

            metadata[key] = val

    return metadata, body


def extract_visto_considerando(body: str) -> tuple[str | None, str | None]:
    """Extrae secciones VISTO y CONSIDERANDO con regex."""
    visto = None
    considerando = None

    m_visto = re.search(r"(?is)\bVISTO\b\s+(.*?)(?=\bCONSIDERANDO\b|\bPOR\s+(?:ELLO|TODO\s+ELLO)\b|\bART[IÍ]CULO\b|$)", body)
    if m_visto:
        visto = m_visto.group(1).strip()

    m_cons = re.search(r"(?is)\bCONSIDERANDO\b\s+(.*?)(?=\bPOR\s+(?:ELLO|TODO\s+ELLO)\b|\bART[IÍ]CULO\b|$)", body)
    if m_cons:
        considerando = m_cons.group(1).strip()

    return visto, considerando


def extract_extracto(texto: str) -> str | None:
    """Para decretos extractados, toma la frase resolutiva o temática."""
    lines = [l.strip() for l in texto.splitlines() if l.strip()]
    content_lines = []
    for l in lines:
        if l.startswith("#") or l.startswith("*") or l.startswith("---"):
            continue
        if "publicado en versión extractada" in l.lower() or "publicado en version extractada" in l.lower():
            continue
        content_lines.append(l)
    return " ".join(content_lines) if content_lines else None


def ingestar_municipio(conn: sqlite3.Connection, valor_municipio, reemplazar: bool = False):
    """Ingesta todos los archivos markdown y anexos de un municipio en SQLite."""
    cur = conn.cursor()
    info = resolver_municipio(valor_municipio)
    cid = info["id"]
    nombre_mun = info["nombre"]
    rutas = get_municipio_rutas(cid)

    ord_dir = rutas["ordenanzas"]
    dec_dir = rutas["decretos"]
    anx_dir = rutas["anexos"]
    cont_json = rutas["contenidos_json"]

    if not ord_dir.exists() and not dec_dir.exists():
        print(f"Error: no se encontraron carpetas de ordenanzas ni decretos para {nombre_mun} en {rutas['raiz']}")
        return 0

    print("=" * 60)
    print(f"INGESTANDO MUNICIPIO: [{cid}] {nombre_mun} ({info['slug']})")
    print("=" * 60)
    print(f"Directorio: {rutas['raiz']}")

    # Cargar contenidos.json si existe
    contenidos_map = {}
    if cont_json.exists():
        try:
            c_list = json.loads(cont_json.read_text(encoding="utf-8"))
            for c in c_list:
                if c.get("cid"):
                    contenidos_map[c["cid"]] = c
        except Exception as e:
            print(f"Aviso al leer {cont_json}: {e}")

    # Lista de archivos markdown
    archivos = sorted(list(ord_dir.glob("*.md")) + list(dec_dir.glob("*.md")))
    total_archivos = len(archivos)
    print(f"Archivos markdown encontrados: {total_archivos}")

    if total_archivos == 0:
        print("No hay archivos para procesar.")
        return 0

    if reemplazar:
        print(f"Eliminando registros previos de {nombre_mun} (cód. {cid})...")
        cur.execute("DELETE FROM anexos WHERE norma_id IN (SELECT id FROM normas WHERE codigo_localidad = ?)", (cid,))
        cur.execute("DELETE FROM articulos WHERE norma_id IN (SELECT id FROM normas WHERE codigo_localidad = ?)", (cid,))
        cur.execute("DELETE FROM referencias_normativas WHERE norma_origen_id IN (SELECT id FROM normas WHERE codigo_localidad = ?)", (cid,))
        cur.execute("DELETE FROM normas WHERE codigo_localidad = ?", (cid,))
        conn.commit()

    # Cargar contenido_ids ya existentes para no duplicar si no es reemplazo
    cur.execute("SELECT contenido_id FROM normas WHERE codigo_localidad = ?", (cid,))
    existentes = set(r[0] for r in cur.fetchall())

    normas_batch = []
    anexos_batch = []

    count_extractadas = 0
    count_completas = 0
    count_ordenanzas = 0
    count_decretos = 0
    omitidos = 0

    start_time = time.time()

    for idx, path in enumerate(archivos, 1):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            text = path.read_text(encoding="latin-1", errors="replace")

        fm, body = parse_frontmatter(text)

        contenido_id = fm.get("contenido_id")
        if not contenido_id:
            m_cid = re.search(r"contents/(\d+)", fm.get("url", ""))
            if m_cid:
                contenido_id = int(m_cid.group(1))

        if not contenido_id:
            continue

        if contenido_id in existentes:
            omitidos += 1
            continue

        tipo = str(fm.get("tipo", "decreto")).lower()
        if tipo == "ordenanza":
            count_ordenanzas += 1
        else:
            tipo = "decreto"
            count_decretos += 1

        numero = fm.get("numero")
        if numero is not None and str(numero).strip():
            parts = str(numero).split()
            try:
                numero = int(parts[0].rstrip(".-/")) if parts else None
            except (ValueError, IndexError):
                numero = None
        else:
            numero = None

        anio = fm.get("anio")
        if anio is not None and str(anio).strip():
            parts = str(anio).split()
            try:
                anio = int(parts[0].rstrip(".-/")) if parts else None
            except (ValueError, IndexError):
                anio = None
        else:
            anio = None

        numero_sibom = str(fm.get("numero_sibom", "")) if fm.get("numero_sibom") else None
        fecha = str(fm.get("fecha", "")) if fm.get("fecha") else None

        boletin = fm.get("boletin")
        if boletin is not None and str(boletin).strip():
            try:
                boletin = int(str(boletin).split()[0].rstrip(".-/"))
            except (ValueError, IndexError):
                boletin = None
        else:
            boletin = None

        boletin_id = fm.get("boletin_id")
        if boletin_id is not None and str(boletin_id).strip():
            try:
                boletin_id = int(str(boletin_id).split()[0].rstrip(".-/"))
            except (ValueError, IndexError):
                boletin_id = None
        else:
            boletin_id = None

        version = str(fm.get("version", "completa")).lower()
        if version not in ("completa", "extractada"):
            version = "completa"

        url = fm.get("url") or f"https://sibom.slyt.gba.gob.ar/contents/{contenido_id}"
        tambien_en = fm.get("tambien_en") or []
        tambien_en_str = json.dumps(tambien_en) if tambien_en else None

        try:
            rel_path = str(path.relative_to(ROOT)).replace("\\", "/")
        except ValueError:
            rel_path = str(path).replace("\\", "/")

        m_title = re.search(r"^#\s+(.*?)$", body, re.MULTILINE)
        titulo = m_title.group(1).strip() if m_title else (f"{tipo.capitalize()} Nº {numero}/{anio}" if numero and anio else path.stem)

        visto, considerando = extract_visto_considerando(body)

        summary = None
        summary_trata = None
        summary_resuelve = None
        summary_depende = None
        procesado_llm = 0

        if version == "extractada":
            count_extractadas += 1
            procesado_llm = 2
            extracto_txt = extract_extracto(body)
            if extracto_txt:
                summary_trata = extracto_txt
                summary_resuelve = extracto_txt
                summary = f"Publicado en versión extractada: {extracto_txt}"
            else:
                summary = "Publicado en versión extractada (sin texto adicional en boletín)."
        else:
            count_completas += 1
            procesado_llm = 0

        norma_tuple = (
            tipo,
            numero,
            anio,
            numero_sibom,
            fecha,
            boletin,
            boletin_id,
            contenido_id,
            version,
            titulo,
            visto,
            considerando,
            text,
            "vigente",
            None,
            summary,
            summary_trata,
            summary_resuelve,
            summary_depende,
            None,
            None,
            tambien_en_str,
            url,
            rel_path,
            nombre_mun,
            cid,
            procesado_llm,
            None,
        )
        normas_batch.append((norma_tuple, contenido_id, fm.get("anexos") or []))

        # Insertar por lotes de 1.000
        if len(normas_batch) >= 1000 or idx == total_archivos:
            if normas_batch:
                insert_tuples = [item[0] for item in normas_batch]
                cur.executemany("""
                    INSERT INTO normas (
                        tipo, numero, anio, numero_sibom, fecha, boletin, boletin_id, contenido_id,
                        version, titulo, seccion_visto, seccion_considerando, texto_completo,
                        estado, notas_vigencia, summary, summary_trata, summary_resuelve,
                        summary_depende, embedding_summary, embedding_texto, tambien_en, url,
                        archivo_md, localidad, codigo_localidad, procesado_llm, fecha_procesado_llm
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, insert_tuples)

                # Mapear anexos
                cids_batch = [item[1] for item in normas_batch if item[1] is not None]
                placeholders = ",".join("?" * len(cids_batch))
                cur.execute(f"SELECT id, contenido_id FROM normas WHERE contenido_id IN ({placeholders})", cids_batch)
                cid_to_norma_id = dict(cur.fetchall())

                for item in normas_batch:
                    c_id = item[1]
                    norma_id = cid_to_norma_id.get(c_id)
                    if not norma_id:
                        continue

                    c_meta = contenidos_map.get(c_id, {})
                    anexos_meta = c_meta.get("anexos") or []

                    if anexos_meta:
                        for a in anexos_meta:
                            anexos_batch.append((
                                norma_id,
                                a.get("titulo") or "Anexo",
                                a.get("anexo_id"),
                                a.get("nombre_archivo"),
                                a.get("url"),
                                "pendiente",
                            ))

                if anexos_batch:
                    cur.executemany("""
                        INSERT INTO anexos (
                            norma_id, titulo, anexo_sibom_id, archivo_pdf, url_descarga, estado_extraccion
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, anexos_batch)
                    anexos_batch.clear()

                conn.commit()
                normas_batch.clear()

    elapsed = time.time() - start_time
    insertadas = total_archivos - omitidos
    print(f"Ingesta de {nombre_mun} finalizada en {elapsed:.1f}s:")
    print(f"  - Nuevas normas insertadas: {insertadas} ({count_ordenanzas} ordenanzas, {count_decretos} decretos)")
    print(f"  - Omitidas (ya existentes): {omitidos}")
    print(f"  - Decretos extractados    : {count_extractadas}")
    print(f"  - Normas completas        : {count_completas}")
    return insertadas


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--municipio", type=str, default=None, help="ID, slug o nombre del municipio (ej: 130, 108, veinticinco-de-mayo)")
    ap.add_argument("--todos", action="store_true", help="Ingesta todos los municipios descargados en disco")
    ap.add_argument("--reemplazar", action="store_true", help="Reemplaza los registros previos del municipio en vez de solo agregar nuevos")
    ap.add_argument("--listar", action="store_true", help="Lista los municipios descargados disponibles")
    args = ap.parse_args()

    if args.listar:
        print("Municipios descargados encontrados en disco:")
        for m in listar_municipios_descargados():
            print(f"  - [{m['id']}] {m['nombre']} ({m['slug']}): {m['ordenanzas']} ordenanzas, {m['decretos']} decretos -> {m['ruta']}")
        return

    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")

    if args.todos:
        for m in listar_municipios_descargados():
            ingestar_municipio(conn, m["id"], reemplazar=args.reemplazar)
    elif args.municipio:
        ingestar_municipio(conn, args.municipio, reemplazar=args.reemplazar)
    else:
        print("Uso: python scripts/sibom_ingest_markdown.py --municipio <id o slug> [--reemplazar]")
        print("     python scripts/sibom_ingest_markdown.py --todos")
        print("     python scripts/sibom_ingest_markdown.py --listar")

    conn.close()


if __name__ == "__main__":
    main()
