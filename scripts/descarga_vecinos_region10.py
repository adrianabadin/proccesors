#!/usr/bin/env python3
"""
descarga_vecinos_region10.py
-----------------------------
Descarga especializada y concurrente de los partidos limítrofes / alrededores
de cada uno de los municipios de la Región Sanitaria X de la Pcia. de Buenos Aires,
excluyendo los que ya están en proceso o completados en Track 1 (7ma Sección / Región X)
o completados previamente.

Distritos limítrofes cubiertos (con publicaciones en SIBOM):
  - #030 Chacabuco (limita con Alberti, Bragado, Chivilcoy, Suipacha)
  - #058 General Viamonte (limita con Bragado)
  - #090 Nueve de Julio (limita con Bragado, 25 de Mayo)
  - #069 Las Flores (limita con Saladillo, Roque Pérez)
  - #047 General Belgrano (limita con Roque Pérez)
  - #111 San Andrés de Giles (limita con Mercedes, Suipacha)
  - #076 Luján (limita con Mercedes)
  - #023 Carmen de Areco (limita con Suipacha)

Vecinos vacíos en SIBOM (omitidos automáticamente):
  - #019 Cañuelas, #050 Gral. Las Heras, #065 Junín, #081 Marcos Paz, #084 Monte.
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
    SIBOM_DIR,
    load_json,
    marcar_estado_ciudad,
    pipeline_ciudad,
)

LOG_FILE = STATE_DIR / "vecinos_region10.log"
COMPLETADOS_LOG = STATE_DIR / "municipios_completados.log"

DISTRITOS_VECINOS = [
    {
        "id": 30,
        "nombre": "Chacabuco",
        "limita_con": "Alberti, Bragado, Chivilcoy, Suipacha",
    },
    {
        "id": 58,
        "nombre": "General Viamonte",
        "limita_con": "Bragado",
    },
    {
        "id": 90,
        "nombre": "Nueve de Julio",
        "limita_con": "Bragado, 25 de Mayo",
    },
    {
        "id": 69,
        "nombre": "Las Flores",
        "limita_con": "Saladillo, Roque Pérez",
    },
    {
        "id": 47,
        "nombre": "General Belgrano",
        "limita_con": "Roque Pérez",
    },
    {
        "id": 111,
        "nombre": "San Andrés de Giles",
        "limita_con": "Mercedes, Suipacha",
    },
    {
        "id": 76,
        "nombre": "Luján",
        "limita_con": "Mercedes",
    },
    {
        "id": 23,
        "nombre": "Carmen de Areco",
        "limita_con": "Suipacha",
    },
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


def ciudad_en_uso_por_otro(cid: int, slug: str) -> bool:
    """Verifica si otro proceso está escribiendo en el directorio del municipio activamente."""
    dir_name = f"{cid:03d}-{slug}"
    p_cont = SIBOM_DIR / dir_name / "contenidos.json"
    if p_cont.exists():
        try:
            mtime = p_cont.stat().st_mtime
            if (time.time() - mtime) < 30.0:
                return True
        except Exception:
            pass
    return False


def main():
    log("=" * 80)
    log("INICIANDO DESCARGA: PARTIDOS VECINOS / ALREDEDORES DE REGIÓN SANITARIA X")
    log("=" * 80)
    log(f"Distritos vecinos a procesar: {len(DISTRITOS_VECINOS)}")
    for d in DISTRITOS_VECINOS:
        log(f"  - #{d['id']:03d} {d['nombre']:<22} (Limita con: {d['limita_con']})")
    log("-" * 80)

    for idx, d in enumerate(DISTRITOS_VECINOS, start=1):
        cid = d["id"]
        nombre = d["nombre"]
        limita = d["limita_con"]

        # Verificar estado fresco en ciudades.json
        ciudades_actual = load_json(CIUDADES_JSON, [])
        c_info = next((x for x in ciudades_actual if x.get("id") == cid), {})
        slug = c_info.get("slug", "")
        estado = c_info.get("estado", "pendiente")

        if estado in ("completa", "vacia"):
            log(f"Omitiendo #{cid:03d} {nombre} (estado actual: {estado})")
            continue

        if ciudad_en_uso_por_otro(cid, slug):
            log(f"AVISO: #{cid:03d} {nombre} registra actividad de otro proceso reciente. Saltando...")
            continue

        log()
        log(f">>> [{idx}/{len(DISTRITOS_VECINOS)}] INICIANDO #{cid:03d} {nombre} (Alrededores Región X - Vecino de {limita})")
        t_inicio = time.time()

        try:
            res = pipeline_ciudad(cid=cid, solo_indexar=False)
            marcar_estado_ciudad(cid, "completa")
            dur = time.time() - t_inicio

            log(
                f"OK #{cid:03d} {nombre}: "
                f"{res.get('boletines', 0)} boletines, "
                f"{res.get('contenidos', 0)} normas "
                f"({res.get('hechos', 0)} hechos, {res.get('errores', 0)} err). "
                f"Duración: {format_duration(dur)}"
            )

            # Registrar en log permanente compartido
            with open(COMPLETADOS_LOG, "a", encoding="utf-8") as f_comp:
                f_comp.write(
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                    f"Municipio #{cid:03d} {nombre} (Vecino Región X) | "
                    f"{res.get('boletines', 0)} bol | "
                    f"{res.get('contenidos', 0)} normas | "
                    f"{res.get('hechos', 0)} hechos | "
                    f"duracion: {format_duration(dur)}\n"
                )

        except Exception as exc:
            log(f"! ERROR en #{cid:03d} {nombre}: {exc}")
            marcar_estado_ciudad(cid, "error")

    log("=" * 80)
    log("FIN DEL PROCESO: PARTIDOS VECINOS DE REGIÓN SANITARIA X COMPLETADOS")
    log("=" * 80)


if __name__ == "__main__":
    main()
