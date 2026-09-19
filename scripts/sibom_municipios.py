#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Módulo de resolución de municipios y rutas para el sistema SIBOM."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIBOM_DIR = ROOT / "sibom"
DB_PATH = SIBOM_DIR / "sibom.db"
STATE_DIR = SIBOM_DIR / "_estado"
CIUDADES_JSON = STATE_DIR / "ciudades.json"

MUNICIPIOS_FIJOS = {
    108: {"id": 108, "nombre": "Saladillo", "slug": "saladillo"},
    130: {"id": 130, "nombre": "Veinticinco de Mayo", "slug": "veinticinco-de-mayo"},
    109: {"id": 109, "nombre": "Salliqueló", "slug": "salliquelo"},
}


def resolver_municipio(valor) -> dict:
    """Resuelve un valor (ID, slug o nombre) al diccionario del municipio."""
    if valor is None or str(valor).strip() in ("108", "saladillo", "Saladillo"):
        return MUNICIPIOS_FIJOS[108]

    val_str = str(valor).strip().lower()

    # Si es número directo
    if val_str.isdigit():
        cid = int(val_str)
        if cid in MUNICIPIOS_FIJOS:
            return MUNICIPIOS_FIJOS[cid]

    # Cargar ciudades.json si existe
    ciudades = []
    if CIUDADES_JSON.exists():
        try:
            ciudades = json.loads(CIUDADES_JSON.read_text(encoding="utf-8"))
        except Exception:
            ciudades = []

    if val_str.isdigit():
        cid = int(val_str)
        for c in ciudades:
            if c.get("id") == cid:
                return {
                    "id": cid,
                    "nombre": c.get("nombre") or f"Municipio {cid}",
                    "slug": c.get("slug") or f"municipio-{cid}",
                }

    # Búsqueda textual por slug o nombre
    for c in ciudades:
        slug = (c.get("slug") or "").lower()
        nombre = (c.get("nombre") or "").lower()
        if slug == val_str or nombre == val_str:
            return {"id": c["id"], "nombre": c["nombre"], "slug": c["slug"]}

    # Búsqueda por substring
    for c in ciudades:
        slug = (c.get("slug") or "").lower()
        nombre = (c.get("nombre") or "").lower()
        if val_str in slug or val_str in nombre:
            return {"id": c["id"], "nombre": c["nombre"], "slug": c["slug"]}

    # Fallback si solo es un id numérico no encontrado en el json
    if val_str.isdigit():
        cid = int(val_str)
        return {"id": cid, "nombre": f"Municipio {cid}", "slug": f"municipio-{cid}"}

    raise ValueError(f"No se pudo resolver el municipio: '{valor}'")


def get_municipio_rutas(cid: int) -> dict:
    """Devuelve las rutas en disco para un municipio dado."""
    info = resolver_municipio(cid)
    ciudad_id = info["id"]

    if ciudad_id == 108:
        return {
            "info": info,
            "raiz": SIBOM_DIR,
            "ordenanzas": SIBOM_DIR / "ordenanzas",
            "decretos": SIBOM_DIR / "decretos",
            "anexos": SIBOM_DIR / "anexos",
            "contenidos_json": STATE_DIR / "contenidos.json",
        }

    # Buscar carpeta específica (ej: 130-veinticinco-de-mayo o 130-*)
    raiz = None
    for p in SIBOM_DIR.iterdir():
        if p.is_dir():
            m = re.match(r"^0*(\d+)-", p.name)
            if m and int(m.group(1)) == ciudad_id:
                raiz = p
                break

    if not raiz or not raiz.exists():
        slug = info.get("slug") or f"municipio-{ciudad_id}"
        raiz = SIBOM_DIR / f"{ciudad_id:03d}-{slug}"

    return {
        "info": info,
        "raiz": raiz,
        "ordenanzas": raiz / "ordenanzas",
        "decretos": raiz / "decretos",
        "anexos": raiz / "anexos",
        "contenidos_json": STATE_DIR / str(ciudad_id) / "contenidos.json",
    }


def listar_municipios_descargados() -> list[dict]:
    """Lista todos los municipios descargados en disco con su conteo de archivos."""
    resultado = []

    # 1. Saladillo (108 legacy)
    ord_108 = list((SIBOM_DIR / "ordenanzas").glob("*.md"))
    dec_108 = list((SIBOM_DIR / "decretos").glob("*.md"))
    if ord_108 or dec_108:
        resultado.append({
            "id": 108,
            "nombre": "Saladillo",
            "slug": "saladillo",
            "ordenanzas": len(ord_108),
            "decretos": len(dec_108),
            "ruta": str(SIBOM_DIR),
        })

    # 2. Otros municipios (v2)
    for p in sorted(SIBOM_DIR.iterdir()):
        if not p.is_dir():
            continue
        m = re.match(r"^0*(\d+)-(.+)$", p.name)
        if m:
            cid = int(m.group(1))
            if cid == 108:
                continue
            info = resolver_municipio(cid)
            o_count = len(list((p / "ordenanzas").glob("*.md")))
            d_count = len(list((p / "decretos").glob("*.md")))
            resultado.append({
                "id": cid,
                "nombre": info["nombre"],
                "slug": info["slug"],
                "ordenanzas": o_count,
                "decretos": d_count,
                "ruta": str(p),
            })

    return resultado


if __name__ == "__main__":
    print("Municipios descargados encontrados en disco:")
    for m in listar_municipios_descargados():
        print(f"  - [{m['id']}] {m['nombre']} ({m['slug']}): {m['ordenanzas']} ordenanzas, {m['decretos']} decretos -> {m['ruta']}")
