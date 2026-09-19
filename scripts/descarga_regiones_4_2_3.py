#!/usr/bin/env python3
"""
descarga_regiones_4_2_3.py
--------------------------
Descarga secuencial y priorizada de los distritos correspondientes a:
  1. Región Sanitaria IV (PBA Norte)
  2. Región Sanitaria II (PBA Noroeste)
  3. Región Sanitaria III (PBA Centro-Noroeste)

Omitiendo automáticamente municipios ya completados o sin publicaciones en SIBOM.
Se activa automáticamente cuando finalice Track 1 o Track 3.
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

LOG_FILE = STATE_DIR / "regiones_4_2_3.log"
COMPLETADOS_LOG = STATE_DIR / "municipios_completados.log"

DISTRITOS_R4_R2_R3 = [
    # --- REGIÓN SANITARIA IV ---
    {"id": 23, "nombre": "Carmen de Areco", "region": "Región Sanitaria IV"},
    {"id": 25, "nombre": "Colón", "region": "Región Sanitaria IV"},
    {"id": 95, "nombre": "Pergamino", "region": "Región Sanitaria IV"},
    {"id": 102, "nombre": "Ramallo", "region": "Región Sanitaria IV"},
    {"id": 105, "nombre": "Rojas", "region": "Región Sanitaria IV"},
    {"id": 110, "nombre": "Salto", "region": "Región Sanitaria IV"},
    {"id": 111, "nombre": "San Andrés de Giles", "region": "Región Sanitaria IV"},

    # --- REGIÓN SANITARIA II ---
    {"id": 22, "nombre": "Carlos Tejedor", "region": "Región Sanitaria II"},
    {"id": 33, "nombre": "Daireaux", "region": "Región Sanitaria II"},
    {"id": 59, "nombre": "General Villegas", "region": "Región Sanitaria II"},
    {"id": 61, "nombre": "Hipólito Yrigoyen", "region": "Región Sanitaria II"},
    {"id": 90, "nombre": "Nueve de Julio", "region": "Región Sanitaria II"},
    {"id": 94, "nombre": "Pellegrini", "region": "Región Sanitaria II"},
    {"id": 104, "nombre": "Rivadavia", "region": "Región Sanitaria II"},
    {"id": 126, "nombre": "Trenque Lauquen", "region": "Región Sanitaria II"},
    {"id": 129, "nombre": "Tres Lomas", "region": "Región Sanitaria II"},

    # --- REGIÓN SANITARIA III ---
    {"id": 30, "nombre": "Chacabuco", "region": "Región Sanitaria III"},
    {"id": 43, "nombre": "Florentino Ameghino", "region": "Región Sanitaria III"},
    {"id": 46, "nombre": "General Arenales", "region": "Región Sanitaria III"},
    {"id": 58, "nombre": "General Viamonte", "region": "Región Sanitaria III"},
    {"id": 72, "nombre": "Lincoln", "region": "Región Sanitaria III"},
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
    """Verifica si otro proceso está escribiendo activamente en la carpeta del municipio."""
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
    log("INICIANDO DESCARGA ENCADENADA: REGIÓN SANITARIA IV -> II -> III")
    log("=" * 80)
    log(f"Distritos en cartera: {len(DISTRITOS_R4_R2_R3)}")
    for d in DISTRITOS_R4_R2_R3:
        log(f"  - #{d['id']:03d} {d['nombre']:<24} ({d['region']})")
    log("-" * 80)

    for idx, d in enumerate(DISTRITOS_R4_R2_R3, start=1):
        cid = d["id"]
        nombre = d["nombre"]
        region = d["region"]

        # Comprobar estado actualizado
        ciudades_actual = load_json(CIUDADES_JSON, [])
        c_info = next((x for x in ciudades_actual if x.get("id") == cid), {})
        slug = c_info.get("slug", "")
        estado = c_info.get("estado", "pendiente")

        if estado in ("completa", "vacia"):
            log(f"Omitiendo #{cid:03d} {nombre} (estado actual: {estado})")
            continue

        if ciudad_en_uso_por_otro(cid, slug):
            log(f"AVISO: #{cid:03d} {nombre} registra actividad de otro proceso reciente. Saltando al siguiente...")
            continue

        log()
        log(f">>> [{idx}/{len(DISTRITOS_R4_R2_R3)}] INICIANDO #{cid:03d} {nombre} ({region})")
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

            # Registrar en log permanente compartido
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
    log("FIN DEL PROCESO: REGIONES SANITARIAS IV, II Y III COMPLETADAS")
    log("=" * 80)


if __name__ == "__main__":
    main()
