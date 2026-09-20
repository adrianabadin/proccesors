#!/usr/bin/env python3
"""
descarga_region3_adelanto.py
----------------------------
Descarga adelantada y en paralelo de los distritos restantes de la Región Sanitaria III:
  - #043 Florentino Ameghino
  - #046 General Arenales
  - #072 Lincoln
(Chacabuco #030 y General Viamonte #058 ya completados al 100%).

Permite que la Región III avance simultáneamente con la Región II (que corre en task-2363).
Al terminar cada uno, queda marcado como 'completa' y se registra en municipios_completados.log.
"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sibom_scraper import (
    CIUDADES_JSON,
    STATE_DIR,
    load_json,
    marcar_estado_ciudad,
    pipeline_ciudad,
)

LOG_FILE = STATE_DIR / "region3_adelanto.log"
COMPLETADOS_LOG = STATE_DIR / "municipios_completados.log"

DISTRITOS = [
    {"id": 43, "nombre": "Florentino Ameghino", "region": "Región Sanitaria III"},
    {"id": 46, "nombre": "General Arenales", "region": "Región Sanitaria III"},
    {"id": 72, "nombre": "Lincoln", "region": "Región Sanitaria III"},
]


def log(msg: str = ""):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}" if msg else ""
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def format_duration(seconds: float) -> str:
    return str(timedelta(seconds=int(seconds)))


def main():
    log("=" * 80)
    log("INICIANDO DESCARGA ADELANTADA: REGIÓN SANITARIA III")
    log("=" * 80)
    log(f"Distritos a procesar: {len(DISTRITOS)}")
    for d in DISTRITOS:
        log(f"  - #{d['id']:03d} {d['nombre']:<25} ({d['region']})")
    log("-" * 80)

    for idx, d in enumerate(DISTRITOS, start=1):
        cid = d["id"]
        nombre = d["nombre"]
        region = d["region"]

        ciudades_actual = load_json(CIUDADES_JSON, [])
        c_info = next((x for x in ciudades_actual if x.get("id") == cid), {})
        estado = c_info.get("estado", "pendiente")
        if estado in ("completa", "vacia"):
            log(f"Omitiendo #{cid:03d} {nombre} (estado actual: {estado})")
            continue

        log()
        log(f">>> [{idx}/{len(DISTRITOS)}] INICIANDO #{cid:03d} {nombre} ({region})")
        t_inicio = time.time()

        try:
            res = pipeline_ciudad(cid=cid, solo_indexar=False)
            marcar_estado_ciudad(cid, "completa")
            dur = time.time() - t_inicio

            log(
                f"OK #{cid:03d} {nombre} ({region}): "
                f"{res.get('boletines', 0)} boletines, "
                f"{res.get('contenidos', 0)} normas "
                f"({res.get('hechos', 0)} hechos, {res.get('errores', 0)} err). "
                f"Duración: {format_duration(dur)}"
            )

            with open(COMPLETADOS_LOG, "a", encoding="utf-8") as f_comp:
                f_comp.write(
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                    f"Municipio #{cid:03d} {nombre} ({region}) | "
                    f"{res.get('boletines', 0)} bol | "
                    f"{res.get('contenidos', 0)} normas | "
                    f"{res.get('hechos', 0)} hechos | "
                    f"duracion: {format_duration(dur)}\n"
                )

        except Exception as exc:
            log(f"! ERROR en #{cid:03d} {nombre}: {exc}")
            marcar_estado_ciudad(cid, "error")

    log("=" * 80)
    log("FIN DEL PROCESO: REGIÓN SANITARIA III COMPLETADA")
    log("=" * 80)


if __name__ == "__main__":
    main()
