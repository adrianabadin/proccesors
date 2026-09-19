#!/usr/bin/env python3
"""
descarga_seccion7_region10.py
-----------------------------
Descarga priorizada y especializada de los distritos correspondientes a:
  - 7ma Sección Electoral de la Pcia. de Buenos Aires
  - Región Sanitaria X de la Pcia. de Buenos Aires

Distritos procesados:
  - #015 Bolívar (7ma Sección) - Reanuda las 17.109 restantes
  - #016 Bragado (Región X) - Reanuda las 12.395 restantes
  - #032 Chivilcoy (Región X)
  - #045 General Alvear (7ma Sección)
  - #074 Lobos (Región X)
  - #082 Mercedes (Región X)
  - #106 Roque Pérez (7ma Sección y Región X)
  - #120 Suipacha (Región X)
  - #122 Tapalqué (7ma Sección)

(Nota: Saladillo #108, 25 de Mayo #130 y Alberti #003 ya están 100% completados.
 Azul #008, Olavarría #091 y Navarro #088 no publican en SIBOM).
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

LOG_FILE = STATE_DIR / "seccion7_region10.log"
COMPLETADOS_LOG = STATE_DIR / "municipios_completados.log"

DISTRITOS_PRIORITARIOS = [
    {"id": 15, "nombre": "Bolívar", "region": "7ma Sección"},
    {"id": 16, "nombre": "Bragado", "region": "Región X"},
    {"id": 32, "nombre": "Chivilcoy", "region": "Región X"},
    {"id": 45, "nombre": "General Alvear", "region": "7ma Sección"},
    {"id": 74, "nombre": "Lobos", "region": "Región X"},
    {"id": 82, "nombre": "Mercedes", "region": "Región X"},
    {"id": 106, "nombre": "Roque Pérez", "region": "7ma Sección / Región X"},
    {"id": 120, "nombre": "Suipacha", "region": "Región X"},
    {"id": 122, "nombre": "Tapalqué", "region": "7ma Sección"},
]


def log(msg: str = ""):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}" if msg else ""
    print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def format_duration(seconds: float) -> str:
    return str(timedelta(seconds=int(seconds)))


def main():
    log("=" * 80)
    log("INICIANDO DESCARGA PRIORIZADA: 7MA SECCIÓN ELECTORAL Y REGIÓN SANITARIA X")
    log("=" * 80)
    log(f"Distritos a procesar: {len(DISTRITOS_PRIORITARIOS)}")
    for d in DISTRITOS_PRIORITARIOS:
        log(f"  - #{d['id']:03d} {d['nombre']:<20} ({d['region']})")
    log("-" * 80)

    for idx, d in enumerate(DISTRITOS_PRIORITARIOS, start=1):
        cid = d["id"]
        nombre = d["nombre"]
        region = d["region"]

        # Verificar si ya está completa o vacía
        ciudades_actual = load_json(CIUDADES_JSON, [])
        c_info = next((x for x in ciudades_actual if x.get("id") == cid), {})
        estado = c_info.get("estado", "pendiente")
        if estado in ("completa", "vacia"):
            log(f"Omitiendo #{cid:03d} {nombre} (estado actual: {estado})")
            continue

        log()
        log(f">>> [{idx}/{len(DISTRITOS_PRIORITARIOS)}] INICIANDO #{cid:03d} {nombre} ({region})")
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

            # Registrar en log permanente
            with open(COMPLETADOS_LOG, "a", encoding="utf-8") as f_comp:
                f_comp.write(
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                    f"Municipio #{cid:03d} {nombre} | "
                    f"{res.get('boletines', 0)} bol | "
                    f"{res.get('contenidos', 0)} normas | "
                    f"{res.get('hechos', 0)} hechos | "
                    f"duracion: {format_duration(dur)}\n"
                )

        except Exception as exc:
            log(f"! ERROR en #{cid:03d} {nombre}: {exc}")
            marcar_estado_ciudad(cid, "error")

    log("=" * 80)
    log("FIN DEL PROCESO: 7MA SECCIÓN ELECTORAL Y REGIÓN SANITARIA X COMPLETADAS")
    log("=" * 80)


if __name__ == "__main__":
    main()
