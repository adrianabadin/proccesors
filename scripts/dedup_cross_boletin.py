#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pase de deduplicación cross-boletín para SIBOM Saladillo.

1. Agrupa los contenidos por archivo destino / par (tipo, numero, anio).
2. En casos de duplicados (norma publicada en >1 boletín o repetida):
   - Selecciona como primaria la del boletín más antiguo (y versión completa si coexisten).
   - Actualiza el front-matter del archivo .md con 'tambien_en: [boletín X, ...]'.
   - Actualiza 'contenidos.json'.
3. Genera el reporte sibom/_estado/duplicados-resueltos.csv.
"""

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIBOM_DIR = ROOT / "sibom"
STATE_DIR = SIBOM_DIR / "_estado"
CONTENIDOS_JSON = STATE_DIR / "contenidos.json"
REPORT_CSV = STATE_DIR / "duplicados-resueltos.csv"


def update_frontmatter_tambien_en(file_path: Path, prim: dict, adicionales_bols: list):
    if not file_path.exists():
        return
    content = file_path.read_text(encoding="utf-8")
    
    # Lista formateada para YAML
    bols_yaml = "[" + ", ".join(f'"{b}"' for b in adicionales_bols) + "]"
    
    # Reemplazar tambien_en: [...]
    if "tambien_en:" in content:
        new_content = re.sub(r"tambien_en:\s*\[.*?\]", f"tambien_en: {bols_yaml}", content)
    else:
        # Si no estuviera, insertar antes de url:
        new_content = content.replace("url:", f"tambien_en: {bols_yaml}\nurl:")
    
    # Asegurar que los metadatos principales coincidan con prim
    new_content = re.sub(r'boletin:\s*"[^"]*"', f'boletin: "{prim["boletin"]}"', new_content, count=1)
    new_content = re.sub(r'boletin_id:\s*\d+', f'boletin_id: {prim["bid"]}', new_content, count=1)
    new_content = re.sub(r'contenido_id:\s*\d+', f'contenido_id: {prim["cid"]}', new_content, count=1)
    new_content = re.sub(r'url:\s*"[^"]*"', f'url: "{prim["url"]}"', new_content, count=1)
    
    file_path.write_text(new_content, encoding="utf-8")


def main():
    if not CONTENIDOS_JSON.exists():
        print(f"No existe {CONTENIDOS_JSON}")
        return

    data = json.loads(CONTENIDOS_JSON.read_text(encoding="utf-8"))
    
    groups = defaultdict(list)
    for c in data:
        if c.get("archivo"):
            groups[c["archivo"]].append(c)

    dups = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"Total archivos compartidos por múltiples registros: {len(dups)}")
    
    csv_rows = []
    total_republicaciones = 0

    for rel_path, items in dups.items():
        # Criterio de orden: boletín más antiguo primero, versión completa antes que extractada, cid menor
        items.sort(key=lambda x: (
            int(x.get("boletin") or 0),
            1 if x.get("extractada") else 0,
            x.get("cid", 0)
        ))
        
        prim = items[0]
        others = items[1:]
        
        bol_adicionales = sorted(list({str(x["boletin"]) for x in others if str(x["boletin"]) != str(prim["boletin"])}))
        # Si todos son del mismo boletín, indicar el número de boletín repetido
        if not bol_adicionales:
            bol_adicionales = [str(x["boletin"]) for x in others]
            
        cids_adicionales = [str(x["cid"]) for x in others]
        total_republicaciones += len(others)

        file_path = SIBOM_DIR / rel_path
        update_frontmatter_tambien_en(file_path, prim, bol_adicionales)

        # Actualizar campos en el json
        prim["tambien_en"] = bol_adicionales
        for o in others:
            o["es_republicacion_de"] = prim["cid"]

        csv_rows.append({
            "archivo": rel_path,
            "tipo": prim["tipo"],
            "numero": prim.get("numero"),
            "anio": prim.get("anio"),
            "boletin_principal": prim["boletin"],
            "cid_principal": prim["cid"],
            "boletines_adicionales": ";".join(bol_adicionales),
            "cids_adicionales": ";".join(cids_adicionales),
        })

    # Guardar json actualizado
    CONTENIDOS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Escribir reporte CSV
    with open(REPORT_CSV, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "archivo", "tipo", "numero", "anio",
            "boletin_principal", "cid_principal",
            "boletines_adicionales", "cids_adicionales"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"Pase de deduplicación completado:")
    print(f"  - Casos resueltos: {len(csv_rows)}")
    print(f"  - Total republicaciones consolidadas: {total_republicaciones}")
    print(f"  - Reporte generado en: {REPORT_CSV}")


if __name__ == "__main__":
    main()
