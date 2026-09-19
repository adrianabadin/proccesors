#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scraper SIBOM multi-municipio (v2) -> archivos Markdown.

v1 (legacy): sin --ciudad mantiene el comportamiento original de Saladillo 108
(rutas sibom/ + sibom/_estado/).
v2: con --ciudad N opera sobre sibom/{id:03d}-{slug}/ y estado en sibom/_estado/{N}/.

Subcomandos:
    index-cities [--desde 1 --hasta 135]   Inventario de municipios (omite 108)
    index-bulletins [--ciudad N]           Fase 1: indexa boletines
    index-contents  [--ciudad N]           Fase 2: indexa ordenanzas/decretos
    download --ciudad N                    Fase 3: pipeline completo de una ciudad
    download --rango A-B [--solo-indexar]  Fase 3 en lote (omite 108/inexistentes/vacias)
    download --boletin N [--ciudad N]      Descarga un boletin puntual
    download --municipio saladillo --desde 129   Actualizacion: solo boletines >= 129
    download --todo                        Legacy/v2: baja lo pendiente del estado activo
    download-anexos [--ciudad N]           Fase 4: baja PDFs de anexos
    status [--global]                      Progreso del estado activo o tabla por ciudad

--municipio acepta id o slug ('108', 'saladillo', 'salliquelo'). Saladillo (108)
siempre opera sobre el layout legacy v1.
Filtros --desde/--hasta actuan sobre el NUMERO de boletin y combinan con cualquier
modo; pensados para actualizaciones incrementales de base (solo lo nuevo).

Estado idempotente en JSON: reanuda donde quedo (guardado incremental cada 10 items).
"""

import argparse
import json
import os
import re
import sys
import time
import traceback
import unicodedata
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://sibom.slyt.gba.gob.ar"
CITY_ID = 108                       # Saladillo (legacy v1)
CITY_OMITIR = {108, 130}            # omitidas en modo lote (108 Saladillo, 130 25 de Mayo)

ROOT = Path(__file__).resolve().parents[1]
SIBOM_DIR = ROOT / "sibom"
STATE_DIR = SIBOM_DIR / "_estado"
CIUDADES_JSON = STATE_DIR / "ciudades.json"

DELAY = 0.4          # segundos entre requests (cortesia)
RETRIES = 5
BACKOFF = 3.0
TIMEOUT = 60

TIPO_PANEL = {"ordinance": "ordenanza", "decree_de": "decreto"}

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; archivo-normas-municipales/2.0)",
})


def log_error(msg: str, estado_dir: Path = STATE_DIR):
    estado_dir.mkdir(parents=True, exist_ok=True)
    with open(estado_dir / "errores.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | {msg}\n")


def get(url: str, ok_404: bool = False) -> requests.Response:
    last_exc = None
    for attempt in range(1, RETRIES + 1):
        try:
            r = session.get(url, timeout=TIMEOUT)
            if ok_404 and r.status_code == 404:
                time.sleep(DELAY)
                return r
            r.raise_for_status()
            time.sleep(DELAY)
            return r
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            wait = BACKOFF * attempt
            print(f"  ! reintento {attempt}/{RETRIES} en {wait}s: {url} ({exc})")
            time.sleep(wait)
    raise RuntimeError(f"Fallo definitivo GET {url}: {last_exc}")


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    content = json.dumps(data, ensure_ascii=False, indent=1)
    tmp.write_text(content, encoding="utf-8")
    for attempt in range(10):
        try:
            tmp.replace(path)
            return
        except OSError:
            time.sleep(0.15 * (attempt + 1))
    try:
        tmp.replace(path)
    except Exception:
        path.write_text(content, encoding="utf-8")
        if tmp.exists():
            try:
                tmp.unlink()
            except Exception:
                pass


def parse_date(s: str) -> str:
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", s or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""


def slugify(nombre: str) -> str:
    s = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s


# --------------------------------------------------------------- rutas/ciudades
def asegurar_ciudad(cid: int) -> dict:
    """Entrada de ciudades.json para cid; si falta, la crea con un fetch."""
    ciudades = load_json(CIUDADES_JSON, [])
    por_id = {c["id"]: c for c in ciudades}
    if cid in por_id:
        return por_id[cid]
    r = get(f"{BASE}/cities/{cid}", ok_404=True)
    h1 = BeautifulSoup(r.text, "html.parser").select_one("#frontend-container h1.title")
    if r.status_code == 404 or not h1:
        raise RuntimeError(f"Ciudad {cid} inexistente")
    nombre = re.sub(r"^Municipio de\s+", "", h1.get_text(strip=True))
    info = {"id": cid, "nombre": nombre, "slug": slugify(nombre),
            "paginas": None, "boletines_pagina1": None,
            "estado": "pendiente", "nota": ""}
    por_id[cid] = info
    save_json(CIUDADES_JSON, list(por_id.values()))
    return info


def resolver_municipio(valor):
    """'108' -> 108 | 'saladillo' -> 108 | slug/nombre -> id (via ciudades.json)."""
    if valor is None:
        return None
    if str(valor).isdigit():
        return int(valor)
    buscado = slugify(str(valor))
    ciudades = load_json(CIUDADES_JSON, [])
    for c in ciudades:
        if c.get("slug") == buscado or slugify(c.get("nombre") or "") == buscado:
            return c["id"]
    sys.exit(f"Municipio '{valor}' no encontrado en {CIUDADES_JSON} (correr index-cities)")


def resolver_rutas(ciudad_id):
    """Rutas legacy (Saladillo v1) si ciudad_id es None o 108; por-ciudad (v2) si no."""
    if ciudad_id == CITY_ID:
        ciudad_id = None  # Saladillo vive en el layout legacy v1
    if ciudad_id is None:
        return {
            "ciudad": None,
            "raiz": SIBOM_DIR,
            "ordenanzas": SIBOM_DIR / "ordenanzas",
            "decretos": SIBOM_DIR / "decretos",
            "anexos": SIBOM_DIR / "anexos",
            "estado": STATE_DIR,
            "boletines_json": STATE_DIR / "boletines.json",
            "contenidos_json": STATE_DIR / "contenidos.json",
        }
    info = asegurar_ciudad(ciudad_id)
    raiz = SIBOM_DIR / f"{ciudad_id:03d}-{info['slug']}"
    est = STATE_DIR / str(ciudad_id)
    return {
        "ciudad": info,
        "raiz": raiz,
        "ordenanzas": raiz / "ordenanzas",
        "decretos": raiz / "decretos",
        "anexos": raiz / "anexos",
        "estado": est,
        "boletines_json": est / "boletines.json",
        "contenidos_json": est / "contenidos.json",
    }


# --------------------------------------------------------------- index-cities
def cmd_index_cities(args):
    ciudades = load_json(CIUDADES_JSON, [])
    por_id = {c["id"]: c for c in ciudades}
    for cid in range(args.desde, args.hasta + 1):
        if cid in CITY_OMITIR and not args.incluir_108:
            prev = por_id.get(cid) or {
                "id": cid, "nombre": "Saladillo", "slug": "saladillo",
                "paginas": 17, "boletines_pagina1": 8,
                "estado": "pendiente", "nota": "",
            }
            prev["estado"] = "omitida"
            prev["nota"] = "en proceso por flujo v1 (PLAN-SIBOM.md)"
            por_id[cid] = prev
            print(f"{cid}: omitida (v1)")
            continue
        r = get(f"{BASE}/cities/{cid}", ok_404=True)
        if r.status_code == 404:
            por_id[cid] = {"id": cid, "nombre": None, "slug": None,
                           "paginas": 0, "boletines_pagina1": 0,
                           "estado": "inexistente", "nota": ""}
            print(f"{cid}: inexistente")
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        h1 = soup.select_one("#frontend-container h1.title")
        if not h1:
            por_id[cid] = {"id": cid, "nombre": None, "slug": None,
                           "paginas": 0, "boletines_pagina1": 0,
                           "estado": "inexistente", "nota": "sin titulo"}
            print(f"{cid}: inexistente (sin titulo)")
            continue
        nombre = re.sub(r"^Municipio de\s+", "", h1.get_text(strip=True))
        n_p1 = len(soup.select("div.bulletin"))
        pags = [
            int(m.group(1))
            for a in soup.select('ul.pagination a[href*="page="]')
            if (m := re.search(r"page=(\d+)", a.get("href", "")))
        ]
        paginas = max(pags) if pags else 1
        por_id[cid] = {
            "id": cid, "nombre": nombre, "slug": slugify(nombre),
            "paginas": paginas, "boletines_pagina1": n_p1,
            "estado": "vacia" if n_p1 == 0 else "pendiente",
            "nota": "",
        }
        print(f"{cid}: {nombre} ({paginas} pag.{', VACIA' if n_p1 == 0 else ''})")
    save_json(CIUDADES_JSON, list(por_id.values()))
    resumen = {}
    for c in por_id.values():
        resumen[c["estado"]] = resumen.get(c["estado"], 0) + 1
    print(f"Inventario -> {CIUDADES_JSON}  {resumen}")


# --------------------------------------------------------------- index-bulletins
def cmd_index_bulletins(args, R):
    cid = R["ciudad"]["id"] if R["ciudad"] else CITY_ID
    if R["boletines_json"].exists() and not getattr(args, "reindexar", False):
        prev = load_json(R["boletines_json"], [])
        if prev:
            print(f"Boletines ya indexados ({len(prev)} boletines) -> {R['boletines_json']}")
            return
    boletines = []
    page = 1
    while True:
        url = f"{BASE}/cities/{cid}" if page == 1 else f"{BASE}/cities/{cid}?page={page}"
        soup = BeautifulSoup(get(url).text, "html.parser")
        rows = soup.select("div.bulletin")
        if not rows:
            break
        for row in rows:
            title_el = row.select_one("p.bulletin-title")
            date_el = row.select_one("p.bulletin-date")
            form = row.select_one('form.button_to[action*="/bulletins/"]')
            if not (title_el and form):
                continue
            bid = int(re.search(r"/bulletins/(\d+)", form["action"]).group(1))
            num = re.search(r"(\d+)", title_el.get_text())
            boletines.append({
                "id": bid,
                "numero": int(num.group(1)) if num else None,
                "titulo": title_el.get_text(strip=True),
                "fecha": parse_date(date_el.get_text() if date_el else ""),
                "url": f"{BASE}/bulletins/{bid}",
            })
        if not soup.select_one('ul.pagination a[rel="next"]'):
            break
        page += 1
        print(f"  pagina {page - 1} ok ({len(boletines)} boletines)")
    boletines.sort(key=lambda b: b["numero"] or 0, reverse=True)
    save_json(R["boletines_json"], boletines)
    print(f"Indexados {len(boletines)} boletines -> {R['boletines_json']}")


# --------------------------------------------------------------- index-contents
def cmd_index_contents(args, R):
    boletines = load_json(R["boletines_json"], [])
    if not boletines:
        sys.exit("Ejecutar primero: index-bulletins")
    contenidos = load_json(R["contenidos_json"], [])
    por_cid = {c["cid"]: c for c in contenidos}

    if contenidos and not getattr(args, "reindexar", False):
        bids_en_contenidos = {c["bid"] for c in contenidos}
        boletines_pendientes = [b for b in boletines if b["id"] not in bids_en_contenidos]
        if not boletines_pendientes:
            print(f"Contenidos ya indexados ({len(contenidos)} contenidos) -> {R['contenidos_json']}")
            return
    else:
        boletines_pendientes = boletines

    total_nuevos = 0
    paneles_desconocidos = set()
    for b in boletines_pendientes:
        soup = BeautifulSoup(get(b["url"]).text, "html.parser")
        for panel in soup.select("div.panel-content"):
            panel_cls = next(
                (c for c in panel.get("class", [])
                 if c.startswith("panel-") and c != "panel-content"),
                None,
            )
            tipo = TIPO_PANEL.get((panel_cls or "").replace("panel-", ""))
            if not tipo:
                if panel.select("a.content-link"):
                    paneles_desconocidos.add(panel_cls)
                continue
            for link in panel.select("a.content-link"):
                m = re.search(r"/bulletins/(\d+)/contents/(\d+)", link["href"])
                if not m:
                    continue
                cid = int(m.group(2))
                if cid in por_cid:
                    continue
                box = link.select_one("div.white-box") or link
                parras = box.find_all("p")
                titulo_sibom = parras[0].get_text(strip=True) if parras else ""
                box_text = box.get_text(" ", strip=True).lower()
                extractada = "versión extractada" in box_text or "version extractada" in box_text
                date_el = box.select_one("p.city-and-date")
                fecha = parse_date(date_el.get_text() if date_el else "") or b["fecha"]
                por_cid[cid] = {
                    "cid": cid,
                    "bid": b["id"],
                    "boletin": b["numero"],
                    "tipo": tipo,
                    "titulo_sibom": titulo_sibom,
                    "extractada": extractada,
                    "fecha": fecha,
                    "url": f"{BASE}/bulletins/{b['id']}/contents/{cid}",
                    "estado": "pendiente",
                    "archivo": None,
                    "numero": None,
                    "anio": None,
                }
                total_nuevos += 1
        print(f"Boletin {b['numero']}: total indice {len(por_cid)}")
    save_json(R["contenidos_json"], list(por_cid.values()))
    for panel_cls in sorted(paneles_desconocidos):
        log_error(f"ADVERTENCIA panel desconocido '{panel_cls}' con contenido en {R['raiz'].name}")
        print(f"  ! ADVERTENCIA: panel '{panel_cls}' no mapeado (ver errores.log)")
    print(f"Indexados {total_nuevos} contenidos nuevos -> {R['contenidos_json']}")


# --------------------------------------------------------------- helpers .md
def limpiar(texto: str) -> str:
    texto = re.sub(r"\s+", " ", texto).strip()
    texto = re.sub(r"\s+,", ",", texto)         # "que ," -> "que,"
    texto = re.sub(r"\s*\.-\s*", ".- ", texto)  # preserva ".-" final de norma
    texto = re.sub(r"\s+([;:])\s*", r"\1 ", texto)
    texto = re.sub(r"\.(?!-)\s+", ". ", texto)
    return texto


def detectar_numero(tipo: str, titulo_sibom: str, cuerpo: str):
    """Devuelve (numero, anio) o (None, None)."""
    if tipo == "decreto":
        m = re.search(r"(\d+)\s*/\s*(\d{2,4})", titulo_sibom or "")
        if m:
            num = int(m.group(1))
            raw_yr = int(m.group(2))
            yr = 2000 + raw_yr if raw_yr < 100 else raw_yr
            return num, yr
    patron = re.compile(
        r"(?:ORDENANZA|DECRETO)\s+N[ºo°ª]?\s*0*(\d{1,5})\s*/\s*(\d{2,4})", re.IGNORECASE
    )
    matches = patron.findall(cuerpo or "")
    normalized = []
    for n, y in matches:
        ny = int(y)
        if ny < 100:
            ny = 2000 + ny if ny <= 50 else 1900 + ny
        if 1980 <= ny <= 2100:
            normalized.append((int(n), ny))
    if tipo == "ordenanza" and normalized:
        return normalized[-1]    # la formula de sancion va al final
    if normalized:
        return normalized[0]
    return None, None


def slug_numero(tipo: str, numero, anio, cid: int, titulo_sibom: str) -> str:
    if numero and anio:
        return f"{tipo}-{numero:04d}-{anio}"
    if titulo_sibom and not re.search(r"/\s*\d+$", titulo_sibom):
        m = re.search(r"(\d+)\s*$", titulo_sibom)
        if m:
            return f"{tipo}-sibom-{int(m.group(1)):04d}"
    return f"{tipo}-cid-{cid}"


def yaml_str(v) -> str:
    return f'"{v}"' if v is not None and v != "" else '""'


def escribir_md(c: dict, cuerpo_md: str, anexos: list, R: dict) -> Path:
    tipo = c["tipo"]
    slug = slug_numero(tipo, c["numero"], c["anio"], c["cid"], c["titulo_sibom"])
    dest_dir = R["ordenanzas"] if tipo == "ordenanza" else R["decretos"]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{slug}.md"
    etiqueta = "Ordenanza" if tipo == "ordenanza" else "Decreto"
    num_titulo = f"{etiqueta} Nº {c['numero']}/{c['anio']}" if c["numero"] else c["titulo_sibom"]
    anexos_yaml = "[" + ", ".join(a["nombre"] for a in anexos) + "]" if anexos else "[]"
    fm = (
        "---\n"
        f"tipo: {tipo}\n"
    )
    if R["ciudad"]:
        fm += f"municipio: {yaml_str(R['ciudad']['slug'])}\n"
        fm += f"municipio_id: {R['ciudad']['id']}\n"
    fm += (
        f"numero: {yaml_str(c['numero'])}\n"
        f"anio: {yaml_str(c['anio'])}\n"
        f"numero_sibom: {yaml_str(c.get('numero_sibom'))}\n"
        f"fecha: {yaml_str(c['fecha'])}\n"
        f"boletin: {yaml_str(c['boletin'])}\n"
        f"boletin_id: {c['bid']}\n"
        f"contenido_id: {c['cid']}\n"
        f"version: {'extractada' if c['extractada'] else 'completa'}\n"
        f"numero_detectado: {'true' if c['numero'] else 'false'}\n"
        f"anexos: {anexos_yaml}\n"
        f"tambien_en: []\n"
        f"url: {yaml_str(c['url'])}\n"
        f"descargado: {datetime.now().isoformat(timespec='seconds')}\n"
        "---\n\n"
        f"# {num_titulo}\n\n"
        f"*{c['titulo_sibom']}*\n\n"
        f"{cuerpo_md}\n"
    )
    dest.write_text(fm, encoding="utf-8")
    return dest


# --------------------------------------------------------------- download
def descargar_contenido(c: dict, R: dict):
    soup = BeautifulSoup(get(c["url"]).text, "html.parser")
    col9 = soup.select_one("#frontend-container .col-md-9")
    if not col9:
        raise RuntimeError("No se encontro contenedor de texto")
    h1 = col9.select_one("h1.title")
    h1_text = h1.get_text(strip=True) if h1 else ""
    if re.search(r"\d+\s*/\s*\d{2,4}", h1_text):
        # el h1 ya es el numero legal (ej: "Decreto Nº604/2026" o "Decreto Nº29/18"), no hay correlativo
        c["numero_sibom"] = None
    else:
        m_sibom = re.search(r"(\d+)\s*$", h1_text)
        c["numero_sibom"] = int(m_sibom.group(1)) if m_sibom else None

    parras = col9.find_all("p", recursive=False)
    if not parras:
        parras = col9.find_all("p")
    lineas = []
    for p in parras:
        if "city-and-date" in (p.get("class") or []):
            continue
        txt = limpiar(p.get_text(" ", strip=True))
        if txt and txt != c["titulo_sibom"]:
            lineas.append(txt)
    cuerpo = "\n\n".join(lineas)

    numero, anio = detectar_numero(c["tipo"], c["titulo_sibom"], cuerpo)
    c["numero"], c["anio"] = numero, anio

    anexos = []
    for annex in soup.select(".row.annex"):
        name_el = annex.select_one("p.annex-name")
        link = annex.select_one('a[href*="download_annex"]')
        if link:
            anexos.append({
                "nombre": name_el.get_text(strip=True) if name_el else "Anexo",
                "url": BASE + link["href"],
            })
    c["anexos"] = anexos

    cuerpo_md = cuerpo if cuerpo else "(sin texto en el boletin)"
    dest = escribir_md(c, cuerpo_md, anexos, R)
    c["archivo"] = str(dest.relative_to(SIBOM_DIR)).replace("\\", "/")
    c["estado"] = "hecho"


def descargar_pendientes(R: dict, boletin_filtro=None, desde=None, hasta=None):
    contenidos = load_json(R["contenidos_json"], [])
    if not contenidos:
        return 0, 0
    pend = [c for c in contenidos if c["estado"] == "pendiente"]
    if boletin_filtro is not None:
        pend = [c for c in pend if c["boletin"] == boletin_filtro]
        if not pend:
            print(f"No hay pendientes del boletin {boletin_filtro}")
            return 0, 0
    if desde is not None:
        pend = [c for c in pend if isinstance(c["boletin"], int) and c["boletin"] >= desde]
    if hasta is not None:
        pend = [c for c in pend if isinstance(c["boletin"], int) and c["boletin"] <= hasta]
    if not pend:
        print("Nada pendiente que cumpla el filtro.")
        return 0, 0
    por_cid = {c["cid"]: c for c in contenidos}
    fallos = 0
    for i, c in enumerate(pend, 1):
        try:
            descargar_contenido(c, R)
            print(f"[{i}/{len(pend)}] ok  {c['archivo']}")
        except Exception as exc:  # noqa: BLE001
            c["estado"] = "error"
            fallos += 1
            log_error(f"cid={c['cid']} {c['url']} :: {exc}", R["estado"])
            print(f"[{i}/{len(pend)}] ERROR cid={c['cid']}: {exc}")
        por_cid[c["cid"]] = c
        if i % 10 == 0 or i == len(pend):
            save_json(R["contenidos_json"], list(por_cid.values()))
    save_json(R["contenidos_json"], list(por_cid.values()))
    return len(pend) - fallos, fallos


def bajar_anexos(R: dict):
    contenidos = load_json(R["contenidos_json"], [])
    pend = [
        c for c in contenidos
        if c.get("estado") == "hecho" and c.get("anexos")
        and not all(a.get("archivo") for a in c["anexos"])
    ]
    ok = err = 0
    for i, c in enumerate(pend, 1):
        slug = slug_numero(c["tipo"], c["numero"], c["anio"], c["cid"], c["titulo_sibom"])
        R["anexos"].mkdir(parents=True, exist_ok=True)
        for a in c["anexos"]:
            if a.get("archivo"):
                continue
            nombre = f"{slug}-{re.sub(r'[^\w-]+', '-', a['nombre'].lower())}.pdf"
            dest = R["anexos"] / nombre
            try:
                r = get(a["url"])
                dest.write_bytes(r.content)
                a["archivo"] = str(dest.relative_to(SIBOM_DIR)).replace("\\", "/")
                ok += 1
                print(f"[{i}/{len(pend)}] ok  {a['archivo']}")
            except Exception as exc:  # noqa: BLE001
                err += 1
                log_error(f"anexo cid={c['cid']} {a['url']} :: {exc}", R["estado"])
                print(f"[{i}/{len(pend)}] ERROR anexo {a['nombre']}: {exc}")
    save_json(R["contenidos_json"], contenidos)
    return ok, err


def marcar_estado_ciudad(cid: int, estado: str):
    ciudades = load_json(CIUDADES_JSON, [])
    for c in ciudades:
        if c["id"] == cid:
            c["estado"] = estado
            break
    save_json(CIUDADES_JSON, ciudades)


def pipeline_ciudad(cid: int, solo_indexar: bool = False, desde=None, hasta=None) -> dict:
    """Pipeline completo (fases 1-4) para una ciudad v2. Devuelve resumen."""
    R = resolver_rutas(cid)
    cmd_index_bulletins(None, R)
    cmd_index_contents(None, R)
    res = {
        "id": cid,
        "slug": R["ciudad"]["slug"],
        "boletines": len(load_json(R["boletines_json"], [])),
        "contenidos": len(load_json(R["contenidos_json"], [])),
        "hechos": 0,
        "errores": 0,
    }
    if not solo_indexar:
        hechos, fallos = descargar_pendientes(R, desde=desde, hasta=hasta)
        bajar_anexos(R)
        res["hechos"], res["errores"] = hechos, fallos
    return res


# --------------------------------------------------------------- comandos desc.
def cmd_download(args, R: dict):
    if R["ciudad"] is None:
        # legacy (Saladillo v1): baja pendientes del estado activo con filtros opcionales
        hechos, fallos = descargar_pendientes(R, args.boletin, args.desde, args.hasta)
        print(f"Listo. {hechos}/{hechos + fallos} descargados, {fallos} errores.")
        return
    # modo ciudad v2: pipeline completo
    res = pipeline_ciudad(R["ciudad"]["id"], solo_indexar=args.solo_indexar,
                          desde=args.desde, hasta=args.hasta)
    # solo marcar 'completa' si la descarga fue sin recorte de rango
    if not (args.solo_indexar or args.desde or args.hasta):
        marcar_estado_ciudad(R["ciudad"]["id"], "completa")
    elif args.solo_indexar:
        marcar_estado_ciudad(R["ciudad"]["id"], "indexada")
    print(f"Ciudad {res['id']}-{res['slug']}: {res['boletines']} boletines, "
          f"{res['contenidos']} contenidos, {res['hechos']} descargados, "
          f"{res['errores']} errores.")


def cmd_download_rango(args):
    m = re.match(r"(\d+)\s*-\s*(\d+)", args.rango or "")
    if not m:
        sys.exit("--rango formato: A-B (ej: 1-135)")
    desde, hasta = int(m.group(1)), int(m.group(2))
    ciudades = load_json(CIUDADES_JSON, [])
    if not ciudades:
        sys.exit("Ejecutar primero: index-cities")
    por_id = {c["id"]: c for c in ciudades}
    omitir = set(args.omitir) if args.omitir else (CITY_OMITIR if not args.incluir_108 else set())
    resumen = []
    for cid in range(desde, hasta + 1):
        info = por_id.get(cid)
        if cid in omitir:
            print(f"--- {cid}: omitida")
            continue
        if not info or info["estado"] in ("inexistente", "vacia", "completa"):
            print(f"--- {cid}: salteada ({info['estado'] if info else 'no indexada'})")
            continue
        print(f"=== Ciudad {cid} {info['nombre']} ===")
        try:
            res = pipeline_ciudad(cid, solo_indexar=args.solo_indexar,
                                  desde=args.desde, hasta=args.hasta)
            marcar_estado_ciudad(cid, "indexada" if args.solo_indexar else "completa")
            resumen.append(res)
            print(f"=== {cid} ok: {res}")
        except Exception as exc:  # noqa: BLE001
            marcar_estado_ciudad(cid, "error")
            log_error(f"lote ciudad={cid} :: {exc}")
            print(f"=== {cid} ERROR: {exc} (continua con la siguiente)")
    print("\nRESUMEN LOTE:")
    for r in resumen:
        print(f"  {r['id']:>3} {r['slug']:<30} {r['contenidos']:>6} contenidos, "
              f"{r['hechos']:>6} hechos, {r['errores']} err")


# --------------------------------------------------------------- status
def cmd_status(args, R: dict):
    from collections import Counter
    if args.global_:
        ciudades = load_json(CIUDADES_JSON, [])
        print(f"{'id':>4} {'municipio':<30} {'estado':<12} {'boletines':>9} "
              f"{'contenidos':>10} {'hechos':>7} {'pend':>6} {'err':>4}")
        totales = Counter()
        for c in sorted(ciudades, key=lambda x: x["id"]):
            if not c.get("slug"):
                print(f"{c['id']:>4} {'-':<30} {c['estado']:<12}")
                totales[c["estado"]] += 1
                continue
            est_dir = STATE_DIR / str(c["id"])
            conts = load_json(est_dir / "contenidos.json", [])
            blts = load_json(est_dir / "boletines.json", [])
            k = Counter(x["estado"] for x in conts)
            print(f"{c['id']:>4} {c['slug']:<30} {c['estado']:<12} {len(blts):>9} "
                  f"{len(conts):>10} {k.get('hecho', 0):>7} {k.get('pendiente', 0):>6} "
                  f"{k.get('error', 0):>4}")
            totales[c["estado"]] += 1
            totales["hecho"] += k.get("hecho", 0)
            totales["pendiente"] += k.get("pendiente", 0)
            totales["error"] += k.get("error", 0)
        print(f"\nTotales: {dict(totales)}")
        return
    contenidos = load_json(R["contenidos_json"], [])
    boletines = load_json(R["boletines_json"], [])
    est = Counter(c["estado"] for c in contenidos)
    tip = Counter(c["tipo"] for c in contenidos)
    alcance = f"{R['ciudad']['id']}-{R['ciudad']['slug']}" if R["ciudad"] else "legacy (Saladillo v1)"
    print(f"Alcance             : {alcance}")
    print(f"Boletines indexados : {len(boletines)}")
    print(f"Contenidos indexados: {len(contenidos)}  {dict(tip)}")
    print(f"Estados             : {dict(est)}")
    if (R["estado"] / "errores.log").exists():
        print(f"Log de errores      : {R['estado'] / 'errores.log'}")


# --------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    # parser padre: --ciudad disponible en cada subcomando
    común = argparse.ArgumentParser(add_help=False)
    común.add_argument("--ciudad", type=int, default=None,
                       help="id de municipio (v2). Sin esto: legacy Saladillo 108")

    ic = sub.add_parser("index-cities", parents=[común])
    ic.add_argument("--desde", type=int, default=1)
    ic.add_argument("--hasta", type=int, default=135)
    ic.add_argument("--incluir-108", action="store_true")

    sub.add_parser("index-bulletins", parents=[común])
    sub.add_parser("index-contents", parents=[común])

    d = sub.add_parser("download", parents=[común])
    d.add_argument("--boletin", type=int, default=None, help="numero de boletin puntual")
    d.add_argument("--desde", type=int, default=None,
                   help="descarga solo boletines numero >= N (actualizacion de base)")
    d.add_argument("--hasta", type=int, default=None,
                   help="descarga solo boletines numero <= N")
    d.add_argument("--municipio", type=str, default=None,
                   help="id o slug del municipio (ej: 108, saladillo, salliquelo)")
    d.add_argument("--todo", action="store_true", help="baja todo lo pendiente del estado activo")
    d.add_argument("--rango", type=str, default=None, help="lote v2: A-B (ej: 1-135)")
    d.add_argument("--solo-indexar", action="store_true", help="lote/ciudad: solo indexar")
    d.add_argument("--omitir", type=int, nargs="*", default=None,
                   help="ids a omitir en lote (default: 108)")
    d.add_argument("--incluir-108", action="store_true")

    sub.add_parser("download-anexos", parents=[común])

    st = sub.add_parser("status", parents=[común])
    st.add_argument("--global", dest="global_", action="store_true")

    args = ap.parse_args()
    if getattr(args, "municipio", None):
        args.ciudad = resolver_municipio(args.municipio)
    R = resolver_rutas(args.ciudad)

    if args.cmd == "index-cities":
        cmd_index_cities(args)
    elif args.cmd == "index-bulletins":
        cmd_index_bulletins(args, R)
    elif args.cmd == "index-contents":
        cmd_index_contents(args, R)
    elif args.cmd == "download":
        if args.rango:
            cmd_download_rango(args)
        elif not (args.boletin is not None or args.todo or args.desde
                  or args.hasta or R["ciudad"]):
            sys.exit("Usar --boletin N, --desde N, --todo, --ciudad N o --rango A-B")
        else:
            cmd_download(args, R)
    elif args.cmd == "download-anexos":
        ok, err = bajar_anexos(R)
        print(f"Anexos: {ok} bajados, {err} errores.")
    elif args.cmd == "status":
        cmd_status(args, R)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrumpido. Reanudar con el mismo comando.")
        sys.exit(130)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
