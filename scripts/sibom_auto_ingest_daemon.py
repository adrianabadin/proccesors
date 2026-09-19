#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Daemon de auto-ingesta continua para SIBOM.

Monitorea periódicamente el disco (sibom/) y cuando detecta nuevas normas
descargadas por cualquier scraper (Track 1, 2, 3), las ingesta de forma incremental
en sibom.db de manera 100% transparente y no bloqueante.
"""

import argparse
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.sibom_ingest_markdown import ingestar_municipio, DB_PATH
from scripts.sibom_municipios import listar_municipios_descargados


_ultimo_disco = {}

def ciclo_ingesta(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("SELECT codigo_localidad, COUNT(*) FROM normas GROUP BY codigo_localidad")
    db_counts = dict(cur.fetchall())

    descargados = listar_municipios_descargados()
    nuevos_totales = 0

    for m in descargados:
        cid = m["id"]
        nombre = m["nombre"]
        total_disco = m["ordenanzas"] + m["decretos"]
        total_db = db_counts.get(cid, 0)

        # Si ya verificamos este total de disco y no hubo novedades, saltar
        if _ultimo_disco.get(cid) == total_disco and total_db > 0:
            continue

        if total_disco > total_db or cid not in db_counts:
            diff = total_disco - total_db
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Detectadas {diff} nuevas normas en disco para [{cid}] {nombre} (disco: {total_disco}, db: {total_db}). Ingestando...", flush=True)
            try:
                ins = ingestar_municipio(conn, cid)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] OK [{cid}] {nombre}: {ins} normas incorporadas a sibom.db\n", flush=True)
                nuevos_totales += ins
                db_counts[cid] = total_db + ins
                _ultimo_disco[cid] = total_disco
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error en auto-ingesta de [{cid}] {nombre}: {e}", flush=True)
                try:
                    conn.rollback()
                except Exception:
                    pass

    return nuevos_totales


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--intervalo", type=int, default=60, help="Intervalo de sondeo en segundos (default: 60)")
    ap.add_argument("--una-vez", action="store_true", help="Ejecuta una sola pasada y sale")
    args = ap.parse_args()

    print("=" * 70, flush=True)
    print("DAEMON CONTINUO DE AUTO-INGESTA SIBOM", flush=True)
    print(f"Base de datos : {DB_PATH}", flush=True)
    print(f"Intervalo     : {args.intervalo} segundos", flush=True)
    print("=" * 70, flush=True)

    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout = 60000")

    try:
        if args.una_vez:
            n = ciclo_ingesta(conn)
            print(f"Pasada única completada. Nuevas normas ingestadas: {n}")
            return

        while True:
            ciclo_ingesta(conn)
            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        print("\nDaemon detenido por el usuario.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
