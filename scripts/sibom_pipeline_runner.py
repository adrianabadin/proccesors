#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Orquestador continuo de cola de procesamiento SIBOM.

Procesa municipios en cola secuencial (--cola 130 1 109 ...):
1. Si un municipio tiene ordenanzas pendientes, las enriquece con GLM Flash,
   reconcilia su vigencia y genera sus embeddings.
2. Si tiene decretos pendientes, los enriquece con GLM Flash, reconcilia
   el árbol de vigencia global del municipio y genera embeddings de resumen.
3. Al finalizar, avanza automáticamente al siguiente municipio de la cola.
Es completamente resiliente a reinicios: detecta automáticamente el estado
actual de cada municipio en sibom.db y retoma exactamente donde quedó.
"""

import argparse
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.sibom_municipios import resolver_municipio, DB_PATH
from scripts.sibom_enrich_glm import run_enrichment
from scripts.sibom_reconcile_vigencia import reconcile_vigencia
from scripts.sibom_generate_embeddings import generate_embeddings


def get_pendientes(conn: sqlite3.Connection, cid: int, tipo: str) -> int:
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM normas WHERE codigo_localidad = ? AND tipo = ? AND procesado_llm = 0",
        (cid, tipo),
    )
    return cur.fetchone()[0]


def post_procesar_municipio(cid: int):
    mun_info = resolver_municipio(cid)
    nombre = mun_info["nombre"]
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === POST-PROCESO PARA {nombre.upper()} [{cid}] ===", flush=True)

    # 1. Reconciliación de vigencia
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Reconciliando árbol de vigencia local...", flush=True)
    reconcile_vigencia(municipio_filtro=cid)

    # 2. Vectorización de resúmenes pendientes
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Vectorizando resúmenes pendientes...", flush=True)
    generate_embeddings(target="summary", municipio_filtro=cid)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Post-proceso de {nombre} completado con éxito.\n", flush=True)


def procesar_municipio_completo(cid: int, workers: int = 5, solo_tipo: str | None = None):
    mun_info = resolver_municipio(cid)
    nombre = mun_info["nombre"]
    print("\n" + "=" * 75, flush=True)
    print(f"INICIANDO PROCESAMIENTO: [{cid}] {nombre.upper()}", flush=True)
    print("=" * 75, flush=True)

    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    try:
        p_ords = get_pendientes(conn, cid, tipo="ordenanza")
        p_decs = get_pendientes(conn, cid, tipo="decreto")
    finally:
        conn.close()

    # 1. Ordenanzas (siempre primero para consolidar el marco regulatorio)
    if solo_tipo in (None, "ordenanza"):
        if p_ords > 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [1/2] Enriqueciendo {p_ords} ordenanzas pendientes de {nombre} con {workers} workers...", flush=True)
            run_enrichment(tipo_filtro="ordenanza", municipio_filtro=cid, workers=workers)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Reconciliando vigencia de ordenanzas de {nombre}...", flush=True)
            reconcile_vigencia(municipio_filtro=cid)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Vectorizando ordenanzas de {nombre}...", flush=True)
            generate_embeddings(target="all", municipio_filtro=cid)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [1/2] Ordenanzas de {nombre}: ya completadas (0 pendientes).", flush=True)

    # 2. Decretos completos
    if solo_tipo in (None, "decreto"):
        if p_decs > 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [2/2] Enriqueciendo {p_decs} decretos completos pendientes de {nombre} con {workers} workers...", flush=True)
            run_enrichment(tipo_filtro="decreto", municipio_filtro=cid, workers=workers)
            post_procesar_municipio(cid)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [2/2] Decretos completos de {nombre}: ya completados (0 pendientes).", flush=True)
            post_procesar_municipio(cid)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] ¡Municipio [{cid}] {nombre} FINALIZADO AL 100%!", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cola", nargs="+", default=["130", "1"], help="Lista de municipios a procesar en orden (ej: --cola 130 1 109)")
    ap.add_argument("--workers", type=int, default=5, help="Workers concurrentes para GLM Flash")
    ap.add_argument("--tipo", type=str, default=None, choices=["ordenanza", "decreto"], help="Filtrar por tipo específico si se desea")
    args = ap.parse_args()

    municipios_info = [resolver_municipio(m) for m in args.cola]

    print("=" * 75, flush=True)
    print("COLA CONTINUA DE PROCESAMIENTO SIBOM", flush=True)
    print(f"Municipios en cola ({len(municipios_info)}):", flush=True)
    for idx, m in enumerate(municipios_info, 1):
        print(f"  {idx}. [{m['id']}] {m['nombre']}", flush=True)
    print(f"Workers concurrentes: {args.workers}", flush=True)
    print("=" * 75, flush=True)

    for m in municipios_info:
        procesar_municipio_completo(m["id"], workers=args.workers, solo_tipo=args.tipo)

    print("\n" + "=" * 75, flush=True)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ¡TODA LA COLA DE MUNICIPIOS HA SIDO PROCESADA EXITOSAMENTE!", flush=True)
    print("=" * 75, flush=True)


if __name__ == "__main__":
    main()
