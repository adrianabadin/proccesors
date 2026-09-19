# PLAN — Descarga SIBOM Saladillo → Markdown

> Plan autocontenido para cualquier agente. Incluye contexto, decisiones tomadas,
> estado actual, pasos restantes y criterios de validación. Ejecutar en orden.

## Objetivo

Descargar la totalidad de los boletines oficiales del Municipio de Saladillo
(distrito 108) desde el sistema provincial SIBOM y dejar cada ordenanza y cada
decreto como un archivo `.md` independiente con su texto completo, dentro de la
subcarpeta `sibom/` de este proyecto.

## Contexto (exploración ya realizada)

- **Fuente**: `https://sibom.slyt.gba.gob.ar` (Sistema de Boletines Oficiales
  Municipales, PBA). Saladillo es `/cities/108`.
- **Alcance**: 129 boletines (del 1º, 08/01/2018, al 129º, 24/07/2026), 17 páginas
  de paginación, 8 boletines por página.
- **Hallazgo clave**: cada ordenanza/decreto tiene página propia
  (`/bulletins/{bid}/contents/{cid}`) con el **texto completo ya en HTML**.
  No hace falta descargar PDFs ni hacer OCR. El PDF del boletín completo
  (`/bulletins/{bid}.pdf`) se descarta como estrategia.
- El sitio responde a **HTTP simple** (curl/requests), sin JS, sin login, sin
  anti-bot. Ocasionalmente corta conexiones (10054) o da timeouts: el script ya
  reintentа 3 veces con backoff.
- **Anexos**: algunas normas tienen anexos PDF con link propio
  (`/bulletins/{bid}/contents/{cid}/download_annex?annex_id={aid}`).
- **Numeración doble en ordenanzas**: SIBOM las lista con correlativo global
  (ej: "Ordenanza Nº 4252") pero el texto legal termina con "ORDENANZA Nº 20/2026"
  (número/año). Los decretos ya vienen como "Decreto Nº 603/2026" (sin correlativo).
- Muchos decretos están **"Publicado en versión extractada"** (texto resumido por
  el municipio). Se guardan igual, con flag.
- Volúmenes: **20.643 normas** (1.006 ordenanzas + 19.637 decretos).

## Decisiones ya tomadas (NO re-discutir)

| Tema | Decisión |
|---|---|
| Estrategia | Solo HTML de páginas individuales. Sin PDFs de boletines. |
| Nombre de archivo | Número/año legal: `ordenanza-0020-2026.md`, `decreto-0603-2026.md` (número con padding a 4 dígitos) |
| Fallback de nombre | Si no se detecta número: `{tipo}-sibom-{correlativo}.md` o `{tipo}-cid-{cid}.md`, con `numero_detectado: false` |
| Anexos | Sí, descargarlos a `sibom/anexos/` con nombre `{slug}-{anexo}.pdf` |
| Metadatos | YAML front-matter (ver formato abajo) |
| Tecnología | Python 3.13 + requests + BeautifulSoup (ya instalados) |
| Cortesía | Delay 0,4 s entre requests, retry ×3 backoff 3/6/9 s |

## Estado actual (100% COMPLETADO)

```
Boletines indexados : 129  (sibom/_estado/boletines.json)
Contenidos indexados: 20.643  (sibom/_estado/contenidos.json)
  ordenanza: 1.006 | decreto: 19.637
Estados             : {'hecho': 20.643, 'pendiente': 0, 'error': 0}
Archivos Markdown   : 20.601 únicos en disco (1.004 ordenanzas, 19.597 decretos)
Anexos PDF          : 350 en disco (100% de anexos declarados descargados)
Republicaciones     : 42 casos consolidados cross-boletín (reporte en duplicados-resueltos.csv)
Aritmética de cierre: 20.601 archivos únicos + 42 duplicados consolidados = 20.643 normas
```

Todas las fases (1 a 5) y el pase de deduplicación cross-boletín fueron ejecutados y validados.

## Herramienta existente

`scripts/sibom_scraper.py` — un solo script, subcomandos:

```powershell
python scripts\sibom_scraper.py index-bulletins   # Fase 1 (ya hecho)
python scripts\sibom_scraper.py index-contents    # Fase 2 (ya hecho)
python scripts\sibom_scraper.py status            # progreso
python scripts\sibom_scraper.py download --todo   # Fase 3: descarga lo pendiente
python scripts\sibom_scraper.py download --boletin 128  # descarga un boletín puntual
python scripts\sibom_scraper.py download-anexos   # Fase 4: baja anexos pendientes
```

- **Idempotente**: reanuda donde quedó (estado en `sibom/_estado/contenidos.json`,
  guardado cada 10 ítems). Si se corta, relanzar el mismo comando.
- A 0,4 s/request, los ~20.100 ítems restantes llevan **3-5 horas**.
- Revisar `errores.log` al final; reintentar los que hayan quedado `estado: error`
  (resetear su estado a `pendiente` en el JSON y relanzar `download --todo`).

## Fases ejecutadas y completadas

### 1. Descarga masiva (Fase 3) - [COMPLETADO]
- Las 20.643 normas fueron descargadas sin errores (`hecho: 20643`).
- Se corrigió el soporte para años de 2 dígitos (`/18`, `/19`) en títulos de decretos que inicialmente colisionaban sobre `decreto-sibom-0018.md` y `0019.md`. Todos los 4.740 decretos afectados fueron re-descargados individualmente.

### 2. Anexos (Fase 4) - [COMPLETADO]
- Descargados los 350 anexos PDF declarados a `sibom/anexos/` con 0 errores (`python scripts/sibom_scraper.py download-anexos`).

### 3. Validación (Fase 5) - [COMPLETADO]
1. `python scripts/sibom_scraper.py status` → `hecho: 20643`, `pendiente: 0`, `error: 0`.
2. `errores.log` verificado (0 errores pendientes).
3. Conteo de archivos: 20.601 archivos Markdown únicos en disco (1.004 ordenanzas, 19.597 decretos).
4. `numero_detectado: false`: solo 20 registros en todo el corpus (99,9% con detección exitosa de número y año legal).
5. Spot-check: 5 archivos verificados de múltiples épocas (2018, 2019, 2021, 2023, 2025); front-matter y texto íntegros.
6. Aritmética exacta: 20.601 archivos únicos + 42 duplicados consolidados = 20.643 registros.

### 4. Deduplicación cross-boletín - [COMPLETADO]
- Script: `scripts/dedup_cross_boletin.py`.
- Casos resueltos: 42 archivos compartidos por normas republicadas.
- Front-matter actualizado con `tambien_en: ["..."]` y metadatos del boletín más antiguo / versión completa.
- Reporte detallado en: `sibom/_estado/duplicados-resueltos.csv`.

## Formato de salida (referencia, ya validado)

```markdown
---
tipo: ordenanza
numero: "20"
anio: "2026"
numero_sibom: "4252"        # correlativo SIBOM; en decretos va vacío
fecha: "2026-05-07"         # fecha de la norma
boletin: "129"
boletin_id: 15435
contenido_id: 2419636
version: completa           # o "extractada"
numero_detectado: true
anexos: [Anexo I]           # nombres declarados
tambien_en: []              # otros boletines que la republicaron
url: "https://sibom.slyt.gba.gob.ar/bulletins/15435/contents/2419636"
descargado: 2026-09-15T18:09:08
---

# Ordenanza Nº 20/2026

*Ordenanza Nº 4252*

VISTO el expediente N° 229/2025 ...

ORDENANZA Nº 20/2026.-
```

Estructura de carpetas:

```
sibom/
├── ordenanzas/   ordenanza-0020-2026.md ...
├── decretos/     decreto-0603-2026.md ...
├── anexos/       ordenanza-0020-2026-anexo-i.pdf ...
└── _estado/
    ├── boletines.json      índice de boletines
    ├── contenidos.json     índice de normas + estado (fuente de verdad)
    ├── errores.log
    └── descarga.log / descarga.err.log   (solo si corre en background)
```

## Riesgos y notas

- **No acelerar el delay**: es cortesía hacia el servidor provincial; bajarlo
  puede provocar bloqueos por IP.
- `contenidos.json` es la fuente de verdad. No editar a mano salvo reset
  puntual de `estado`.
- Fases 1-2 NO requieren re-ejecutarse salvo que se quiera descubrir boletines
  nuevos publicados después de sept-2026 (re-run es incremental y seguro).
- Los archivos .md son UTF-8. En consola PowerShell pueden verse mal con
  `Get-Content` (mojibake de display), pero el contenido es correcto: validar
  con editor/Read, no por pantalla de consola.
- Este repositorio tiene un MCP propio (`ordenanzas-saladillo`) con una base
  existente de normas; estos .md son un corpus nuevo independiente en `sibom/`.
  No mezclar ni borrar datos del MCP.
