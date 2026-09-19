#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Procesa secuencialmente las normas pendientes o con error."""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import sqlite3
from scripts.sibom_enrich_glm import call_glm, parse_articulos, guardar_resultado, DB_PATH

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, titulo, texto_completo FROM normas WHERE procesado_llm = -1")
    rows = cur.fetchall()
    total = len(rows)
    print(f"Procesando secuencialmente las {total} normas restantes...")

    for i, (id_, tit, txt) in enumerate(rows, 1):
        try:
            arts = parse_articulos(txt)
            if len(txt) > 6000:
                txt_clip = txt[:4000] + "\n\n[...artículos intermedios...]\n\n" + txt[-2000:]
            else:
                txt_clip = txt
            res = call_glm(txt_clip, tit)
            res["articulos"] = arts
            guardar_resultado(conn, id_, res)
            trata = (res.get("summary") or {}).get("trata") or ""
            print(f"[{i}/{total}] ok id={id_}: {trata[:60]}")
        except Exception as e:
            print(f"[{i}/{total}] error id={id_}: {e}")

    conn.close()
    print("Finalizado.")

if __name__ == "__main__":
    main()
