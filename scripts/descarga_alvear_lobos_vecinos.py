#!/usr/bin/env python3
"""
descarga_alvear_lobos_vecinos.py
---------------------------------
Descarga concurrente y priorizada de los distritos restantes de la 7ma Sección Electoral,
Región Sanitaria X y municipios vecinos limítrofes que aún no han sido descargados:
  - #045 General Alvear  (7ma Sección Electoral)
  - #074 Lobos           (Región Sanitaria X)
  - #069 Las Flores      (Vecino Región X / Saladillo / Roque Pérez)
  - #047 General Belgrano (Vecino Región X / Roque Pérez)
  - #076 Luján           (Vecino Región X / Mercedes)

Totalmente compatible e independiente de los procesos activos (Lote General y Regiones 4-2-3).
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

LOG_FILE = STATE_DIR / "alvear_lobos_vecinos.log"
COMPLETADOS_LOG = STATE_DIR / "municipios_completados.log"

DISTRITOS = [
    {"id": 45, "nombre": "General Alvear", "tipo": "7ma Sección Electoral"},
    {"id": 74, "nombre": "Lobos", "tipo": "Región Sanitaria X"},
    {"id": 69, "nombre": "Las Flores", "tipo": "Vecino Región X (Saladillo / Roque Pérez)"},
    {"id": 47, "nombre": "General Belgrano", "tipo": "Vecino Región X (Roque Pérez)"},
    {"id": 76, "nombre": "Luján", "tipo": "Vecino Región X (Mercedes)"},
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
    log("INICIANDO DESCARGA: 7MA SECCIÓN, REGIÓN X Y VECINOS RESTANTES")
    log("=" * 80)
    log(f"Distritos a procesar: {len(DISTRITOS)}")
    for d in DISTRITOS:
        log(f"  - #{d['id']:03d} {d['nombre']:<20} ({d['tipo']})")
    log("-" * 80)

    for idx, d in enumerate(DISTRITOS, start=1):
        cid = d["id"]
        nombre = d["nombre"]
        tipo = d["tipo"]

        # Verificar si ya está completa o vacía
        ciudades_actual = load_json(CIUDADES_JSON, [])
        c_info = next((x for x in ciudades_actual if x.get("id") == cid), {})
        estado = c_info.get("estado", "pendiente")
        if estado in ("completa", "vacia"):
            log(f"Omitiendo #{cid:03d} {nombre} (estado actual: {estado})")
            continue

        log()
        log(f">>> [{idx}/{len(DISTRITOS)}] INICIANDO #{cid:03d} {nombre} ({tipo})")
        t_inicio = time.time()

        try:
            res = pipeline_ciudad(cid=cid, solo_indexar=False)
            marcar_estado_ciudad(cid, "completa")
            dur = time.time() - t_inicio

            log(
                f"OK #{cid:03d} {nombre} ({tipo}): "
                f"{res.get('boletines', 0)} boletines, "
                f"{res.get('contenidos', 0)} normas "
                f"({res.get('hechos', 0)} hechos, {res.get('errores', 0)} err). "
                f"Duración: {format_duration(dur)}"
            )

            # Registrar en log permanente
            with open(COMPLETADOS_LOG, "a", encoding="utf-8") as f_comp:
                f_comp.write(
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                    f"Municipio #{cid:03d} {nombre} ({tipo}) | "
                    f"{res.get('boletines', 0)} bol | "
                    f"{res.get('contenidos', 0)} normas | "
                    f"{res.get('hechos', 0)} hechos | "
                    f"duracion: {format_duration(dur)}\n"
                )

        except Exception as exc:
            log(f"! ERROR en #{cid:03d} {nombre}: {exc}")
            marcar_estado_ciudad(cid, "error")

    log("=" * 80)
    log("FIN DEL PROCESO: DISTRITOS RESTANTES COMPLETADOS")
    log("=" * 80)


if __name__ == "__main__":
    main()
