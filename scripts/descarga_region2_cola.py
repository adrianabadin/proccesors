#!/usr/bin/env python3
"""
descarga_region2_cola.py
------------------------
Descarga en paralelo de la cola de la Región Sanitaria II (orden inverso):
  - #129 Tres Lomas
  - #126 Trenque Lauquen
  - #104 Rivadavia
  - #094 Pellegrini

Opera concurrentemente con task-2363 (que avanza desde #090 9 de Julio hacia adelante).
Ambos procesos se encuentran en el medio sin colisiones; si un distrito ya fue marcado
como 'completa', se saltea inmediatamente.
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

LOG_FILE = STATE_DIR / "region2_cola.log"
COMPLETADOS_LOG = STATE_DIR / "municipios_completados.log"

DISTRITOS = [
    {"id": 129, "nombre": "Tres Lomas", "region": "Región Sanitaria II"},
    {"id": 126, "nombre": "Trenque Lauquen", "region": "Región Sanitaria II"},
    {"id": 104, "nombre": "Rivadavia", "region": "Región Sanitaria II"},
    {"id": 94, "nombre": "Pellegrini", "region": "Región Sanitaria II"},
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
    log("INICIANDO DESCARGA EN PARALELO: REGIÓN SANITARIA II (COLA)")
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
    log("FIN DEL PROCESO: COLA DE REGIÓN SANITARIA II COMPLETADA")
    log("=" * 80)


if __name__ == "__main__":
    main()
