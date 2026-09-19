"""Resolución y normalización de municipios para SIBOM."""
import json
import re
import unicodedata
from pathlib import Path
from typing import Any
from .config import SIBOM_ROOT

CIUDADES_JSON = SIBOM_ROOT / "_estado" / "ciudades.json"

# Municipios frecuentes / verificados
MUNICIPIOS_CONOCIDOS: dict[int, dict[str, Any]] = {
    1: {"id": 1, "nombre": "Adolfo Alsina", "slug": "adolfo-alsina"},
    108: {"id": 108, "nombre": "Saladillo", "slug": "saladillo"},
    109: {"id": 109, "nombre": "Salliqueló", "slug": "salliquelo"},
    130: {"id": 130, "nombre": "Veinticinco de Mayo", "slug": "veinticinco-de-mayo"},
}


def _strip_accents(text: str) -> str:
    """Elimina acentos para comparación robusta."""
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def _load_ciudades() -> list[dict[str, Any]]:
    """Carga el catálogo de ciudades si existe."""
    if CIUDADES_JSON.exists():
        try:
            return json.loads(CIUDADES_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def resolver_municipio(valor: Any) -> dict[str, Any]:
    """Resuelve un valor (ID entero, string numérico, slug o nombre) a su dict canónico.
    
    Returns:
        dict: {"id": int, "nombre": str, "slug": str}
        
    Raises:
        ValueError: Si el valor no puede asociarse unívocamente a ningún municipio.
    """
    if valor is None:
        raise ValueError("El municipio no puede ser nulo")

    val_str = str(valor).strip()
    if not val_str:
        raise ValueError("El identificador de municipio no puede estar vacío")

    # 1. Si es numérico
    if val_str.isdigit():
        cid = int(val_str)
        if cid in MUNICIPIOS_CONOCIDOS:
            return MUNICIPIOS_CONOCIDOS[cid]

        ciudades = _load_ciudades()
        for c in ciudades:
            if c.get("id") == cid:
                return {
                    "id": cid,
                    "nombre": c.get("nombre") or f"Municipio {cid}",
                    "slug": c.get("slug") or f"municipio-{cid}",
                }
        return {"id": cid, "nombre": f"Municipio {cid}", "slug": f"municipio-{cid}"}

    # 2. Búsqueda por slug o nombre exacto (sin acentos, case insensitive)
    val_norm = _strip_accents(val_str.lower())
    for cid, m in MUNICIPIOS_CONOCIDOS.items():
        if _strip_accents(m["slug"].lower()) == val_norm or _strip_accents(m["nombre"].lower()) == val_norm:
            return m

    ciudades = _load_ciudades()
    for c in ciudades:
        slug = _strip_accents((c.get("slug") or "").lower())
        nombre = _strip_accents((c.get("nombre") or "").lower())
        if slug == val_norm or nombre == val_norm:
            return {"id": c["id"], "nombre": c["nombre"], "slug": c["slug"]}

    # 3. Búsqueda por substring parcial
    for cid, m in MUNICIPIOS_CONOCIDOS.items():
        if val_norm in _strip_accents(m["slug"].lower()) or val_norm in _strip_accents(m["nombre"].lower()):
            return m

    for c in ciudades:
        slug = _strip_accents((c.get("slug") or "").lower())
        nombre = _strip_accents((c.get("nombre") or "").lower())
        if val_norm in slug or val_norm in nombre:
            return {"id": c["id"], "nombre": c["nombre"], "slug": c["slug"]}

    raise ValueError(f"No se pudo resolver el municipio: '{valor}'")


def listar_municipios_disponibles() -> list[dict[str, Any]]:
    """Devuelve la lista de municipios conocidos con sus IDs y nombres."""
    return list(MUNICIPIOS_CONOCIDOS.values())
