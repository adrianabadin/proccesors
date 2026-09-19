#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Descarga masiva de municipios SIBOM (PBA).

Omite automáticamente:
  - 108: Saladillo (ya descargado en layout v1)
  - 130: 25 de Mayo (ya descargado completo: 6.979 normas)
  - Municipios ya completados (ej: 109 Salliqueló)
  - Municipios vacíos o inexistentes (según ciudades.json)

Uso:
  python scripts/descarga_masiva_sibom.py --listar             # Solo muestra la lista pendiente
  python scripts/descarga_masiva_sibom.py                      # Ejecuta descarga de todos los pendientes (1-135)
  python scripts/descarga_masiva_sibom.py --desde 1 --hasta 20 # Solo un rango de IDs
  python scripts/descarga_masiva_sibom.py --orden tamano-asc   # Prioriza municipios más chicos (menos páginas)
  python scripts/descarga_masiva_sibom.py --limite 5           # Descarga los próximos 5 municipios
  python scripts/descarga_masiva_sibom.py --solo-indexar       # Solo indexa boletines/contenidos sin texto
"""

import argparse
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path

# Asegurar import de sibom_scraper
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from sibom_scraper import (
        CIUDADES_JSON,
        STATE_DIR,
        load_json,
        log_error,
        marcar_estado_ciudad,
        pipeline_ciudad,
    )
except ImportError as err:
    sys.exit(f"Error importando sibom_scraper: {err}")

# Municipios intocables / ya completados que se omiten por defecto
DEFAULT_OMITIR = {108, 130}

LOG_FILE = STATE_DIR / "lote_descarga.log"


def log(msg: str = "", to_file: bool = True):
    """Imprime en pantalla y registra en lote_descarga.log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}" if msg else ""
    print(formatted, flush=True)
    if to_file:
        try:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")
        except Exception:
            pass


def format_duration(seconds: float) -> str:
    """Devuelve duración legible en HH:MM:SS."""
    return str(timedelta(seconds=int(seconds)))


def obtener_candidatos(
    ciudades: list,
    desde: int,
    hasta: int,
    omitir_ids: set,
    incluir_completas: bool = False,
    orden: str = "id",
) -> list:
    """Filtra y ordena los municipios elegibles para descarga."""
    candidatos = []
    for c in ciudades:
        cid = c["id"]
        if cid < desde or cid > hasta:
            continue
        if cid in omitir_ids:
            continue

        estado = c.get("estado", "pendiente")
        # Saltar municipios sin contenido
        if estado in ("inexistente", "vacia", "omitida"):
            continue
        if estado == "completa" and not incluir_completas:
            continue

        candidatos.append(c)

    # Ordenamiento
    if orden == "tamano-asc":
        # Menor a mayor cantidad de páginas (más rápidos primero)
        candidatos.sort(key=lambda x: (x.get("paginas") or 9999, x["id"]))
    elif orden == "tamano-desc":
        candidatos.sort(key=lambda x: (x.get("paginas") or 0, x["id"]), reverse=True)
    else:  # 'id'
        candidatos.sort(key=lambda x: x["id"])

    return candidatos


def cmd_listar(candidatos: list, total_ciudades: int, omitir_ids: set):
    """Muestra tabla de candidatos sin descargar nada."""
    print("=" * 80)
    print("PLAN DE DESCARGA MASIVA SIBOM (MUNICIPIOS CANDIDATOS)")
    print("=" * 80)
    print(f"Total en inventario provincial : {total_ciudades}")
    print(f"Municipios excluidos fijados   : {sorted(omitir_ids)} (108 Saladillo, 130 25 de Mayo)")
    print(f"Municipios a procesar          : {len(candidatos)}")

    total_paginas = sum(c.get("paginas") or 0 for c in candidatos)
    print(f"Total páginas estimadas        : {total_paginas}")
    print("-" * 80)
    print(f"{'ID':>4} | {'Municipio':<30} | {'Páginas':>7} | {'Estado Actual':<12}")
    print("-" * 80)
    for c in candidatos:
        pags = c.get("paginas") or "?"
        print(f"{c['id']:>4} | {c.get('nombre') or c.get('slug', ''):<30} | {pags:>7} | {c.get('estado', 'pendiente'):<12}")
    print("=" * 80)


def ejecutar_lote(args):
    ciudades = load_json(CIUDADES_JSON, [])
    if not ciudades:
        sys.exit(f"No se encontró inventario en {CIUDADES_JSON}. Ejecutar primero index-cities.")

    omitir_ids = set(DEFAULT_OMITIR)
    if args.omitir:
        omitir_ids.update(args.omitir)

    candidatos = obtener_candidatos(
        ciudades=ciudades,
        desde=args.desde,
        hasta=args.hasta,
        omitir_ids=omitir_ids,
        incluir_completas=args.incluir_completas,
        orden=args.orden,
    )

    if args.limite and args.limite > 0:
        candidatos = candidatos[: args.limite]

    if args.listar:
        cmd_listar(candidatos, len(ciudades), omitir_ids)
        return

    if not candidatos:
        log("No hay municipios pendientes en el rango especificado.")
        return

    log("=" * 80)
    log("INICIANDO DESCARGA MASIVA SIBOM")
    log(f"Rango de IDs             : {args.desde} - {args.hasta}")
    log(f"Municipios omitidos      : {sorted(omitir_ids)} (incluye Saladillo 108 y 25 de Mayo 130)")
    log(f"Municipios a procesar    : {len(candidatos)}")
    log(f"Modo                     : {'SOLO INDEXAR' if args.solo_indexar else 'DESCARGA COMPLETA (normas + anexos)'}")
    log(f"Orden                    : {args.orden}")
    log(f"Archivo de log           : {LOG_FILE}")
    log("=" * 80)

    t_inicio_total = time.time()
    resumen_exitos = []
    resumen_fallos = []

    PROGRESO_JSON = STATE_DIR / "progreso_resumen.json"
    COMPLETADOS_LOG = STATE_DIR / "municipios_completados.log"

    def actualizar_progreso_json(actual_info=None):
        data = {
            "ultima_actualizacion": datetime.now().isoformat(),
            "modo": "solo_indexar" if args.solo_indexar else "completa",
            "total_candidatos": len(candidatos),
            "completados_count": len(resumen_exitos),
            "fallos_count": len(resumen_fallos),
            "actual": actual_info,
            "ultimos_completados": [
                {
                    "id": r[0],
                    "nombre": r[1],
                    "boletines": r[2].get("boletines", 0),
                    "contenidos": r[2].get("contenidos", 0),
                    "hechos": r[2].get("hechos", 0),
                    "duracion": format_duration(r[3]),
                }
                for r in resumen_exitos[-10:]
            ],
        }
        try:
            PROGRESO_JSON.parent.mkdir(parents=True, exist_ok=True)
            with open(PROGRESO_JSON, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    for idx, c in enumerate(candidatos, start=1):
        cid = c["id"]
        nombre = c.get("nombre") or c.get("slug", f"ciudad-{cid}")
        pags = c.get("paginas") or "?"

        log()
        log(f">>> [{idx}/{len(candidatos)}] INICIANDO Municipio #{cid}: {nombre} ({pags} págs.)")
        t_inicio_ciudad = time.time()
        actualizar_progreso_json({"id": cid, "nombre": nombre, "indice": idx, "paginas": pags})

        try:
            res = pipeline_ciudad(
                cid=cid,
                solo_indexar=args.solo_indexar,
                desde=None,
                hasta=None,
            )
            nuevo_estado = "indexada" if args.solo_indexar else "completa"
            marcar_estado_ciudad(cid, nuevo_estado)

            dur_ciudad = time.time() - t_inicio_ciudad
            log(
                f"OK Municipio #{cid} ({nombre}): "
                f"{res.get('boletines', 0)} boletines, "
                f"{res.get('contenidos', 0)} normas "
                f"({res.get('hechos', 0)} descargadas, {res.get('errores', 0)} err). "
                f"Tiempo: {format_duration(dur_ciudad)}"
            )
            resumen_exitos.append((cid, nombre, res, dur_ciudad))

            # Registrar en log permanente de municipios completados
            with open(COMPLETADOS_LOG, "a", encoding="utf-8") as f_comp:
                f_comp.write(
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                    f"Municipio #{cid:03d} {nombre} | "
                    f"{res.get('boletines', 0)} bol | "
                    f"{res.get('contenidos', 0)} normas | "
                    f"{res.get('hechos', 0)} hechos | "
                    f"duracion: {format_duration(dur_ciudad)}\n"
                )
            # Ingesta automática a sibom.db si hubo descargas
            if not args.solo_indexar and res.get('hechos', 0) > 0:
                try:
                    import sqlite3
                    if str(ROOT) not in sys.path:
                        sys.path.insert(0, str(ROOT))
                    try:
                        from scripts.sibom_ingest_markdown import ingestar_municipio, DB_PATH
                    except ImportError:
                        from sibom_ingest_markdown import ingestar_municipio, DB_PATH
                    conn_ing = sqlite3.connect(DB_PATH, timeout=60)
                    conn_ing.execute("PRAGMA busy_timeout = 60000")
                    ins = ingestar_municipio(conn_ing, cid)
                    conn_ing.close()
                    log(f"-> Ingestadas automáticamente en sibom.db: {ins} normas para #{cid} ({nombre})")
                except Exception as e_ing:
                    log(f"! Error en ingesta automática de #{cid} a sibom.db: {e_ing}")

            actualizar_progreso_json(None)

        except KeyboardInterrupt:
            log("! Interrupción por el usuario (Ctrl+C). Guardando estado actual...")
            actualizar_progreso_json(None)
            break
        except Exception as exc:  # noqa: BLE001
            dur_ciudad = time.time() - t_inicio_ciudad
            log(f"! ERROR en Municipio #{cid} ({nombre}): {exc}")
            log_error(f"descarga_masiva ciudad={cid} ({nombre}) :: {exc}")
            marcar_estado_ciudad(cid, "error")
            resumen_fallos.append((cid, nombre, str(exc)))
            log(f"! Municipio #{cid} marcado como 'error'. Continuando con el siguiente...")
            actualizar_progreso_json(None)

        # Progreso general y ETA
        tiempo_transcurrido = time.time() - t_inicio_total
        promedio_por_ciudad = tiempo_transcurrido / idx
        restantes = len(candidatos) - idx
        eta_segundos = promedio_por_ciudad * restantes
        log(f"Progreso global: {idx}/{len(candidatos)} completados. ETA restante: ~{format_duration(eta_segundos)}")

    # Resumen final
    tiempo_total = time.time() - t_inicio_total
    log()
    log("=" * 80)
    log("RESUMEN DE DESCARGA MASIVA")
    log(f"Tiempo total transcurrido: {format_duration(tiempo_total)}")
    log(f"Municipios completados con éxito : {len(resumen_exitos)}")
    log(f"Municipios con error             : {len(resumen_fallos)}")

    if resumen_exitos:
        total_boletines = sum(r[2].get("boletines", 0) for r in resumen_exitos)
        total_contenidos = sum(r[2].get("contenidos", 0) for r in resumen_exitos)
        total_descargados = sum(r[2].get("hechos", 0) for r in resumen_exitos)
        log(f"Total boletines indexados        : {total_boletines}")
        log(f"Total normas procesadas          : {total_contenidos}")
        log(f"Total archivos descargados       : {total_descargados}")

    if resumen_fallos:
        log("\nMunicipios que registraron error (revisar sibom/_estado/errores.log):")
        for cid, nom, err in resumen_fallos:
            log(f"  - #{cid} {nom}: {err}")

    log("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--desde", type=int, default=1, help="ID inicial (default: 1)")
    parser.add_argument("--hasta", type=int, default=135, help="ID final (default: 135)")
    parser.add_argument(
        "--omitir",
        type=int,
        nargs="*",
        default=[],
        help="IDs adicionales a omitir (108 y 130 se omiten siempre automáticamente)",
    )
    parser.add_argument(
        "--incluir-completas",
        action="store_true",
        help="Fuerza re-descargar municipios que ya figuran en estado 'completa'",
    )
    parser.add_argument(
        "--solo-indexar",
        action="store_true",
        help="Solo indexa boletines y contenidos sin descargar archivos de texto ni anexos",
    )
    parser.add_argument(
        "--listar",
        action="store_true",
        help="Muestra la lista de municipios candidatos sin realizar descargas",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=None,
        help="Límite máximo de municipios a procesar en esta ejecución",
    )
    parser.add_argument(
        "--orden",
        choices=["id", "tamano-asc", "tamano-desc"],
        default="id",
        help="Orden de procesamiento: 'id' (ascendente), 'tamano-asc' (más chicos primero), 'tamano-desc'",
    )

    args = parser.parse_args()
    ejecutar_lote(args)


if __name__ == "__main__":
    main()
