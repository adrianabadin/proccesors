#!/usr/bin/env python3
"""
vigilante_disparador_r423.py
----------------------------
Vigila en segundo plano la finalización de cualquiera de los dos tracks nuevos:
  - Track 1: descarga_seccion7_region10.py
  - Track 3: descarga_vecinos_region10.py

Apenas UNO de ellos concluye su lote de municipios, este vigilante dispara
automáticamente el proceso de descarga encadenada:
  Región Sanitaria IV -> Región Sanitaria II -> Región Sanitaria III
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sibom_scraper import STATE_DIR

LOG_TRACK1 = STATE_DIR / "seccion7_region10.log"
LOG_TRACK3 = STATE_DIR / "vecinos_region10.log"
LOG_VIGILANTE = STATE_DIR / "disparador_r423.log"
TARGET_SCRIPT = ROOT / "scripts" / "descarga_regiones_4_2_3.py"


def log(msg: str = ""):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}" if msg else ""
    print(line, flush=True)
    try:
        LOG_VIGILANTE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_VIGILANTE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def track1_finalizo() -> bool:
    if not LOG_TRACK1.exists():
        return False
    try:
        with open(LOG_TRACK1, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            return "FIN DEL PROCESO: 7MA SECCIÓN ELECTORAL Y REGIÓN SANITARIA X COMPLETADAS" in content
    except Exception:
        return False


def track3_finalizo() -> bool:
    if not LOG_TRACK3.exists():
        return False
    try:
        with open(LOG_TRACK3, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            return "FIN DEL PROCESO: PARTIDOS VECINOS DE REGIÓN SANITARIA X COMPLETADOS" in content
    except Exception:
        return False


def main():
    log("=" * 80)
    log("VIGILANTE INICIADO: ESPERANDO FINALIZACIÓN DE TRACK 1 O TRACK 3")
    log("=" * 80)
    log("Objetivo: En cuanto uno de los 2 procesos termine, se disparará:")
    log("  -> Región Sanitaria IV -> Región Sanitaria II -> Región Sanitaria III")

    while True:
        t1_done = track1_finalizo()
        t3_done = track3_finalizo()

        if t1_done or t3_done:
            causa = "Track 1 (7ma Sección y Región X)" if t1_done else "Track 3 (Alrededores Región X)"
            log()
            log("!" * 80)
            log(f"¡FINALIZACIÓN DETECTADA EN: {causa}!")
            log(f"DISPARANDO EJECUCIÓN: {TARGET_SCRIPT.name}")
            log("!" * 80)

            # Ejecutar el script objetivo de forma síncrona / continua
            try:
                subprocess.run(
                    [sys.executable, "-u", str(TARGET_SCRIPT)],
                    check=True,
                    cwd=str(ROOT),
                )
                log("Descarga encadenada de Regiones IV, II y III completada exitosamente.")
            except Exception as exc:
                log(f"Error durante la ejecución encadenada: {exc}")
            break

        time.sleep(15)


if __name__ == "__main__":
    main()
