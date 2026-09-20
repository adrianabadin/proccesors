#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enriquecedor de ordenanzas con GLM Flash (Zhipu AI / BigModel).

Extrae:
1. Desglose determinístico de artículos (número, orden, texto, resumen inicial).
2. Summary estructurado vía LLM (trata, resuelve, depende).
3. Relaciones de vigencia vía LLM (derogaciones totales, parciales, modificaciones, citas).

Soporta glm-4.7-flash con fallback automático a glm-4-flash ante congestión (HTTP 429 / código 1305).
Configuración en .env: BIGMODEL_API_KEY
"""

import argparse
import concurrent.futures
import json
import os
import re
import sqlite3
import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

SIBOM_DIR = ROOT / "sibom"
DB_PATH = SIBOM_DIR / "sibom.db"

API_KEY = os.getenv("BIGMODEL_API_KEY")
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_MODEL = os.getenv("GLM_MODEL", "glm-4-flash")

def get_system_prompt(municipio: str = "Saladillo") -> str:
    return f"""Eres un analista legal experto en derecho municipal argentino. Tu función es analizar ordenanzas y decretos de {municipio} (Buenos Aires) y extraer información jurídica estructurada en formato JSON estricto.

## Reglas:
1. Respondé ÚNICAMENTE con un objeto JSON válido. Sin markdown ni texto explicativo.
2. Si no hay relaciones normativas, devolvé una lista vacía [].
3. Sé riguroso: solo extraé relaciones que surjan del texto.
4. Tipos de relación permitidos:
   - deroga_total: anula completamente otra norma
   - deroga_parcial: anula artículos específicos de otra norma
   - modifica: cambia la redacción de artículos de otra norma
   - sustituye: reemplaza un artículo o régimen previo por uno nuevo
   - prorroga: extiende el plazo de vigencia de una norma
   - convalida: ratifica un decreto o convenio previo
   - adhiere: adhiere a una ley provincial o nacional
   - reglamenta: reglamenta una ordenanza o ley
   - cita: menciona otra norma como antecedente

## Estructura JSON requerida:
{{
  "summary": {{
    "trata": "string breve (objeto o materia principal)",
    "resuelve": "string breve (disposición o decisión concreta)",
    "depende": "string breve (expedientes, leyes u ordenanzas antecedentes de las que depende)"
  }},
  "relaciones": [
    {{
      "tipo": "deroga_total | deroga_parcial | modifica | sustituye | prorroga | convalida | adhiere | reglamenta | cita",
      "destino_tipo": "ordenanza | decreto | ley_provincial | decreto_provincial | ley_nacional | otro",
      "destino_numero": null o integer,
      "destino_anio": null o integer,
      "destino_referencia": "string (ej: 'Ordenanza 62/07', 'Ley 11.723', 'Expte 145/2023')",
      "articulos_afectados": "string | null (ej: 'Arts. 1 y 3')",
      "texto_cita": "string breve donde se dispone la relación"
    }}
  ]
}}"""

SYSTEM_PROMPT = get_system_prompt("Saladillo")


def parse_articulos(texto: str) -> list[dict]:
    """Desglosa el texto de la norma en artículos de forma determinística."""
    if not texto:
        return []

    patron = re.compile(
        r"(?im)^(?:\s*(?:#+|\*+|-+)\s*)?(?:art[ií]culo|art\.?)\s+([0-9]+[a-z0-9\s]*(?:bis|ter|quater|quinto)?)\s*[:º°\.\-\)\*]*\s*(.*)$"
    )
    matches = list(patron.finditer(texto))
    if not matches:
        # Si no tiene desglose explícito de artículos, guardamos 1 artículo general
        resumen_previo = texto[:180].replace("\n", " ").strip()
        return [{
            "numero": "1",
            "orden": 1,
            "texto": texto.strip(),
            "resumen": resumen_previo
        }]

    articulos = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
        num_art = m.group(1).strip().rstrip(".-:")
        cuerpo = texto[start:end].strip()

        # Primeras líneas para resumen rápido
        lineas = [l.strip() for l in cuerpo.split("\n") if l.strip()]
        resumen = lineas[0] if lineas else ""
        if len(lineas) > 1 and len(resumen) < 40:
            resumen += " " + lineas[1]

        articulos.append({
            "numero": num_art,
            "orden": i + 1,
            "texto": cuerpo,
            "resumen": resumen[:250].strip()
        })
    return articulos


def clean_json_response(raw_text: str) -> dict:
    """Limpia bloques de código markdown o caracteres extraños para parsear JSON, con auto-reparación si fue truncado."""
    txt = raw_text.strip()
    if "```" in txt:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", txt)
        if match:
            txt = match.group(1).strip()

    txt = re.sub(r"<think>[\s\S]*?</think>", "", txt).strip()

    start = txt.find("{")
    if start != -1:
        txt = txt[start:]

    # Normalizar comas faltantes entre atributos JSON
    txt = re.sub(r'([0-9"truefalsenull\]\}])\s*\n\s*("[a-zA-Z0-9_]+"\s*:)', r'\1,\n\2', txt)

    end = txt.rfind("}")
    if end != -1:
        txt_candidate = txt[: end + 1]
        try:
            return json.loads(txt_candidate, strict=False)
        except Exception:
            pass

    # Auto-reparación para JSON truncado por límite de tokens
    for i in range(len(txt), max(1, len(txt) - 500), -5):
        c = txt[:i].rstrip(", \n\r\t")
        for suffix in ["}", "]}", "]}}", '"}\n}', '"}\n]}']:
            try:
                return json.loads(c + suffix, strict=False)
            except Exception:
                continue

    return json.loads(txt, strict=False)


def call_glm(texto_norma: str, titulo: str, municipio: str = "Saladillo", model: str = DEFAULT_MODEL, retries: int = 2) -> dict:
    """Llama a la API de BigModel GLM Flash con manejo de reintentos y fallback."""
    if not API_KEY:
        raise ValueError("No se encontró BIGMODEL_API_KEY en .env")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    # Optimizar contexto: Visto/Considerando (inicio) + cláusulas derogatorias (final)
    if len(texto_norma) > 8000:
        texto_input = texto_norma[:5000] + "\n\n[...artículos intermedios omitidos...]\n\n" + texto_norma[-2500:]
    else:
        texto_input = texto_norma

    sys_prompt = get_system_prompt(municipio)
    prompt_user = f"Analizá la siguiente norma de {municipio}:\n\nTítulo: {titulo}\n\nTexto:\n{texto_input}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt_user},
        ],
        "temperature": 0.1,
        "max_tokens": 3072,
    }

    last_err = None
    current_model = model

    for attempt in range(1, retries + 1):
        payload["model"] = current_model
        if current_model.startswith("glm-4-flash") and "thinking" in payload:
            del payload["thinking"]

        try:
            r = requests.post(BASE_URL, headers=headers, json=payload, timeout=(10, 50))
            if r.status_code == 200:
                data = r.json()
                msg = data["choices"][0]["message"]
                content = msg.get("content") or ""
                if not content and "reasoning_content" in msg:
                    content = msg["reasoning_content"]
                return clean_json_response(content)
            elif r.status_code == 429:
                err_data = {}
                try:
                    err_data = r.json().get("error", {})
                except Exception:
                    pass
                if current_model != "glm-4-flash":
                    current_model = "glm-4-flash"
                    time.sleep(1.0)
                    continue
                last_err = f"HTTP 429 (Rate limit): {err_data.get('message', 'congestión')}"
                time.sleep(3.0 * attempt)
            else:
                last_err = f"HTTP {r.status_code}: {r.text[:200]}"
                time.sleep(2.0 * attempt)
        except requests.exceptions.Timeout:
            last_err = f"Timeout de lectura (>75s) en {current_model}"
            if current_model != "glm-4-flash":
                current_model = "glm-4-flash"
            time.sleep(2.0 * attempt)
        except requests.exceptions.RequestException as e:
            last_err = f"Error de red/DNS en {current_model}: {e}"
            time.sleep(4.0 * attempt)
        except Exception as e:
            last_err = str(e)
            time.sleep(2.0 * attempt)

    raise RuntimeError(f"Fallo tras {retries} reintentos ({current_model}): {last_err}")


def procesar_norma(norma_id: int, titulo: str, texto: str, municipio: str = "Saladillo", model: str = DEFAULT_MODEL) -> tuple[int, dict | None, str | None]:
    """Procesa una norma individual: extrae artículos determinísticos y llama a GLM."""
    try:
        # 1. Desglose determinístico de artículos
        articulos = parse_articulos(texto)

        # 2. Análisis semántico con LLM (summary y relaciones de vigencia)
        res_llm = call_glm(texto, titulo, municipio=municipio, model=model)
        res_llm["articulos"] = articulos

        return norma_id, res_llm, None
    except Exception as exc:
        return norma_id, None, str(exc)


def guardar_resultado(conn: sqlite3.Connection, norma_id: int, res: dict):
    """Persiste en SQLite la extracción de forma atómica con reintentos en caso de lock."""
    summary_data = res.get("summary", {})
    trata = summary_data.get("trata")
    resuelve = summary_data.get("resuelve")
    depende = summary_data.get("depende")

    partes_resumen = []
    if trata:
        partes_resumen.append(f"Trata sobre: {trata}")
    if resuelve:
        partes_resumen.append(f"Resuelve: {resuelve}")
    if depende:
        partes_resumen.append(f"Depende de: {depende}")
    summary_texto = " | ".join(partes_resumen) if partes_resumen else None

    articulos = res.get("articulos", [])
    relaciones = res.get("relaciones", [])

    for attempt in range(1, 20):
        try:
            cur = conn.cursor()
            # 1. Actualizar norma
            cur.execute("""
                UPDATE normas
                SET summary_trata = ?,
                    summary_resuelve = ?,
                    summary_depende = ?,
                    summary = ?,
                    procesado_llm = 1,
                    fecha_procesado_llm = datetime('now', 'localtime')
                WHERE id = ?
            """, (trata, resuelve, depende, summary_texto, norma_id))

            # 2. Insertar artículos
            if articulos:
                cur.execute("DELETE FROM articulos WHERE norma_id = ?", (norma_id,))
                for idx, art in enumerate(articulos, 1):
                    num_art = str(art.get("numero") or idx)
                    texto_art = art.get("texto") or ""
                    resumen_art = art.get("resumen")
                    cur.execute("""
                        INSERT OR REPLACE INTO articulos (norma_id, numero_articulo, orden, texto, resumen, estado)
                        VALUES (?, ?, ?, ?, ?, 'vigente')
                    """, (norma_id, num_art, idx, texto_art, resumen_art))

            # 3. Insertar relaciones normativas
            if relaciones:
                cur.execute("DELETE FROM referencias_normativas WHERE norma_origen_id = ?", (norma_id,))
                for rel in relaciones:
                    tipo_rel = rel.get("tipo") or "cita"
                    dest_tipo = rel.get("destino_tipo") or "otro"
                    dest_num = rel.get("destino_numero")
                    dest_anio = rel.get("destino_anio")
                    dest_ref = rel.get("destino_referencia")
                    art_afect = rel.get("articulos_afectados")
                    texto_cita = rel.get("texto_cita")

                    tipo_rel_valido = tipo_rel if tipo_rel in (
                        "deroga_total", "deroga_parcial", "modifica", "sustituye",
                        "prorroga", "convalida", "adhiere", "reglamenta", "cita"
                    ) else "cita"

                    cur.execute("""
                        INSERT INTO referencias_normativas (
                            norma_origen_id, destino_tipo, destino_numero, destino_anio,
                            destino_referencia, tipo_relacion, articulos_afectados, texto_cita
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (norma_id, dest_tipo, dest_num, dest_anio, dest_ref, tipo_rel_valido, art_afect, texto_cita))

            conn.commit()
            return
        except sqlite3.OperationalError as exc:
            if ("locked" in str(exc).lower() or "busy" in str(exc).lower()) and attempt < 20:
                time.sleep(0.5 * attempt)
            else:
                raise



from scripts.sibom_municipios import (
    resolver_municipio,
    get_municipio_rutas,
    listar_municipios_descargados,
    DB_PATH,
)


def cmd_status(municipio_filtro=None):
    conn = sqlite3.connect(DB_PATH, timeout=60)
    cur = conn.cursor()

    mun_info = resolver_municipio(municipio_filtro) if municipio_filtro else None

    print("=" * 65)
    if mun_info:
        print(f"ESTADO DE PROCESAMIENTO GLM - [{mun_info['id']}] {mun_info['nombre'].upper()}")
    else:
        print("ESTADO DE PROCESAMIENTO GLM EN SIBOM.DB (CONSOLIDADO)")
    print("=" * 65)

    where_sql = " WHERE codigo_localidad = ?" if mun_info else ""
    params = (mun_info["id"],) if mun_info else ()

    cur.execute(f"SELECT COUNT(*) FROM normas{where_sql}", params)
    total = cur.fetchone()[0]

    cur.execute(f"SELECT procesado_llm, COUNT(*) FROM normas{where_sql} GROUP BY procesado_llm", params)
    estados_map = {
        0: "pendiente",
        1: "enriquecido_glm",
        2: "extractada_directa",
        -1: "error"
    }
    counts = {estados_map.get(r[0], str(r[0])): r[1] for r in cur.fetchall()}

    # Desglose por municipio si no hay filtro
    if not mun_info:
        cur.execute("""
            SELECT codigo_localidad, localidad,
                   SUM(CASE WHEN tipo = 'ordenanza' THEN 1 ELSE 0 END) as ordenanzas,
                   SUM(CASE WHEN tipo = 'decreto' THEN 1 ELSE 0 END) as decretos,
                   SUM(CASE WHEN procesado_llm = 1 THEN 1 ELSE 0 END) as enriquecidas,
                   SUM(CASE WHEN procesado_llm = 0 THEN 1 ELSE 0 END) as pendientes,
                   COUNT(*) as total
            FROM normas
            GROUP BY codigo_localidad, localidad
        """)
        print("Desglose por Municipio:")
        for cid, loc, ords, decs, enr, pend, tot in cur.fetchall():
            print(f"  * [{cid}] {loc:<22}: {tot} normas ({ords} ords, {decs} decs) | {enr} enriquecidas, {pend} pendientes")
        print("-" * 65)

    cur.execute(f"""
        SELECT COUNT(*) FROM articulos a
        JOIN normas n ON n.id = a.norma_id
        {where_sql.replace('WHERE', 'WHERE n.')}
    """, params)
    total_arts = cur.fetchone()[0]

    cur.execute(f"""
        SELECT COUNT(*) FROM referencias_normativas r
        JOIN normas n ON n.id = r.norma_origen_id
        {where_sql.replace('WHERE', 'WHERE n.')}
    """, params)
    total_refs = cur.fetchone()[0]

    cur.execute(f"""
        SELECT r.tipo_relacion, COUNT(*) FROM referencias_normativas r
        JOIN normas n ON n.id = r.norma_origen_id
        {where_sql.replace('WHERE', 'WHERE n.')}
        GROUP BY r.tipo_relacion
    """, params)
    refs_by_tipo = dict(cur.fetchall())

    conn.close()

    print(f"Normas en ámbito:         {total}")
    print(f"Estados de procesamiento: {counts}")
    print(f"Artículos extraídos:      {total_arts}")
    print(f"Referencias/árbol:        {total_refs} {refs_by_tipo}")
    print("=" * 65)


def run_enrichment(tipo_filtro: str | None = None, municipio_filtro=None, limit: int | None = None, workers: int = 5, model: str = DEFAULT_MODEL):
    conn = sqlite3.connect(DB_PATH, timeout=60)
    cur = conn.cursor()

    mun_info = resolver_municipio(municipio_filtro) if municipio_filtro else None

    query = "SELECT id, titulo, texto_completo, localidad FROM normas WHERE procesado_llm = 0"
    params = []
    if mun_info:
        query += " AND codigo_localidad = ?"
        params.append(mun_info["id"])
    if tipo_filtro:
        query += " AND tipo = ?"
        params.append(tipo_filtro)
    query += " ORDER BY anio DESC, numero DESC"
    if limit:
        query += f" LIMIT {limit}"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    total = len(rows)
    mun_lbl = f"[{mun_info['id']}] {mun_info['nombre']}" if mun_info else "TODOS"
    if total == 0:
        print(f"No hay normas pendientes para {mun_lbl} con el filtro ({tipo_filtro or 'todos'}).")
        return

    print(f"Iniciando enriquecimiento GLM ({model}) para {mun_lbl}: {total} normas pendientes a procesar con {workers} workers...")

    exitos = 0
    fallos = 0
    start_time = time.time()

    write_conn = sqlite3.connect(DB_PATH, timeout=60)
    write_conn.execute("PRAGMA busy_timeout = 60000")

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(procesar_norma, row[0], row[1], row[2], row[3] or "Saladillo", model): row[0]
            for row in rows
        }

        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            norma_id, resultado, error = future.result()
            if resultado:
                guardar_resultado(write_conn, norma_id, resultado)
                exitos += 1
                n_arts = len(resultado.get("articulos", []))
                n_refs = len(resultado.get("relaciones", []))
                print(f"[{i}/{total}] ok id={norma_id} ({n_arts} arts, {n_refs} relaciones)", flush=True)
            else:
                fallos += 1
                for attempt in range(1, 10):
                    try:
                        wcur = write_conn.cursor()
                        wcur.execute(
                            "UPDATE normas SET procesado_llm = -1, notas_vigencia = ? WHERE id = ?",
                            (f"ERROR GLM: {error}", norma_id)
                        )
                        write_conn.commit()
                        break
                    except sqlite3.OperationalError:
                        time.sleep(0.5 * attempt)
                safe_err = str(error).encode("ascii", errors="replace").decode("ascii")
                print(f"[{i}/{total}] ERROR id={norma_id}: {safe_err}", flush=True)

    write_conn.close()

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"LOTE FINALIZADO en {elapsed:.1f}s ({exitos} exitosos, {fallos} errores)")
    print("=" * 60)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--status", action="store_true", help="Muestra estadísticas actuales")
    ap.add_argument("--municipio", type=str, default=None, help="ID, slug o nombre del municipio (ej: 130, 108, veinticinco-de-mayo)")
    ap.add_argument("--ordenanzas", action="store_true", help="Procesa solo las ordenanzas pendientes")
    ap.add_argument("--decretos-completos", action="store_true", help="Procesa solo los decretos completos pendientes")
    ap.add_argument("--limit", type=int, default=None, help="Límite de normas a procesar")
    ap.add_argument("--workers", type=int, default=5, help="Workers concurrentes (default: 5)")
    ap.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Modelo GLM a usar")
    ap.add_argument("--reset-errores", action="store_true", help="Resetea errores (-1) a pendientes (0)")
    args = ap.parse_args()

    if args.status:
        cmd_status(municipio_filtro=args.municipio)
        return

    if args.reset_errores:
        conn = sqlite3.connect(DB_PATH, timeout=60)
        q = "UPDATE normas SET procesado_llm = 0 WHERE procesado_llm = -1"
        params = []
        if args.municipio:
            info = resolver_municipio(args.municipio)
            q += " AND codigo_localidad = ?"
            params.append(info["id"])
        conn.execute(q, params)
        conn.commit()
        conn.close()
        print("Errores reseteados a pendiente (0).")
        return

    if args.ordenanzas:
        run_enrichment(tipo_filtro="ordenanza", municipio_filtro=args.municipio, limit=args.limit, workers=args.workers, model=args.model)
    elif args.decretos_completos:
        run_enrichment(tipo_filtro="decreto", municipio_filtro=args.municipio, limit=args.limit, workers=args.workers, model=args.model)
    else:
        run_enrichment(tipo_filtro=None, municipio_filtro=args.municipio, limit=args.limit, workers=args.workers, model=args.model)


if __name__ == "__main__":
    main()
