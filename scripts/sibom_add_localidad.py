#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Migración para agregar columnas de localidad y código a normas en sibom.db."""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "sibom" / "sibom.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(normas)")
    cols = [c[1] for c in cur.fetchall()]

    if "codigo_localidad" not in cols:
        print("Agregando columna 'codigo_localidad'...")
        cur.execute("ALTER TABLE normas ADD COLUMN codigo_localidad INTEGER DEFAULT 108")
    else:
        print("Columna 'codigo_localidad' ya existe.")

    if "localidad" not in cols:
        print("Agregando columna 'localidad'...")
        cur.execute("ALTER TABLE normas ADD COLUMN localidad TEXT DEFAULT 'Saladillo'")
    else:
        print("Columna 'localidad' ya existe.")

    print("Actualizando registros existentes...")
    cur.execute("UPDATE normas SET codigo_localidad = 108 WHERE codigo_localidad IS NULL")
    cur.execute("UPDATE normas SET localidad = 'Saladillo' WHERE localidad IS NULL")

    print("Creando índices...")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_normas_localidad ON normas(codigo_localidad, tipo)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_normas_localidad_num ON normas(codigo_localidad, tipo, numero, anio)")

    conn.commit()

    cur.execute("SELECT codigo_localidad, localidad, COUNT(*) FROM normas GROUP BY codigo_localidad, localidad")
    distribucion = cur.fetchall()
    print("Distribución verificada:", distribucion)

    conn.close()

if __name__ == "__main__":
    migrate()
