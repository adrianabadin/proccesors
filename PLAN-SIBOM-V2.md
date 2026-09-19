# PLAN v2 — Scraper SIBOM multi-municipio (ciudades 1-135)

> Complementa a `PLAN-SIBOM.md` (v1, Saladillo 108, ya en ejecución por otro agente).
> Este plan parametriza el scraper para CUALQUIER municipio del SIBOM.
> Leer también PLAN-SIBOM.md para contexto del sitio y decisiones de formato
> (estrategia HTML-only, front-matter, naming) que v2 hereda sin cambios.

## Objetivo

Extender `scripts/sibom_scraper.py` para que opere sobre
`https://sibom.slyt.gba.gob.ar/cities/{numero}` con `numero` parametrizable
(rango válido: 1-134; la 135 devuelve 404), sin tocar la descarga en curso de
Saladillo (108).

## Decisiones cerradas (NO re-discutir)

| Tema | Decisión |
|---|---|
| Layout de datos | `sibom/{id:03d}-{slug}/ordenanzas|decretos|anexos/` (ej: `sibom/001-adolfo-alsina/`) |
| Estado por ciudad | `sibom/_estado/{id}/boletines.json` y `contenidos.json` |
| Inventario global | `sibom/_estado/ciudades.json` |
| Saladillo (108) | **Intocable**: conserva layout v1 (`sibom/ordenanzas/`, `sibom/_estado/*.json`). v2 lo omite por defecto |
| Modo lote | Sí: `--rango A-B` itera ciudades; omite 108, inexistentes y vacías |
| Backward compat | Sin `--ciudad`: el script sigue comportándose como v1 (Saladillo legacy) |

## Hallazgos de la exploración (ya realizada)

- IDs **1-134 existen** con status 200. **135 = 404**. (La 136 = La Matanza existe;
  el orden de IDs no es alfabético.)
- Estructura HTML idéntica en todas: `h1.title` = "Municipio de {Nombre}",
  `div.bulletin`, misma paginación, mismos paneles `#Ordinance` / `#Decree_de`.
- Hay ciudades **sin boletines** (ej: 50 General Las Heras, 100 Punta Indio,
  136 La Matanza): `div.bulletin` vacío en página 1.
- Volumen potencial: Saladillo solo tiene 20.643 normas → el total provincial
  puede ser de cientos de miles. La corrida completa a 0,4 s/request toma **días**:
  el diseño debe ser resumible por ciudad y por ítem.

## Cambios al script (versión 2)

### 1. Slug de municipio

De `h1.title` "Municipio de Adolfo Alsina" → `adolfo-alsina`:
lowercase + `unicodedata.normalize('NFKD')` para quitar acentos + no-alfanuméricos
a `-`. Prefijo con ID: `001-adolfo-alsina` (evita colisiones de nombres).

### 2. Nuevo subcomando `index-cities`

```powershell
python scripts\sibom_scraper.py index-cities --desde 1 --hasta 135
```

- GET `/cities/{id}` por cada ID. Registra: `id`, `nombre`, `slug`, `existe`
  (status 200), `boletines_pagina1`, `paginas` (de la paginación),
  `estado`: `inexistente` | `vacia` | `pendiente`.
- **Omite el 108** (queda `omitida` con nota "en proceso v1").
- Guarda `sibom/_estado/ciudades.json`. Re-ejecutable e incremental.

### 3. Parametrización `--ciudad` en los subcomandos existentes

```powershell
python scripts\sibom_scraper.py index-bulletins --ciudad 7
python scripts\sibom_scraper.py index-contents  --ciudad 7
python scripts\sibom_scraper.py download        --ciudad 7
python scripts\sibom_scraper.py download-anexos --ciudad 7
```

Con `--ciudad N`: rutas de datos y estado resueltas a
`sibom/{id:03d}-{slug}/...` y `sibom/_estado/{N}/...` (el nombre/slug se lee de
`ciudades.json`). Sin `--ciudad`: rutas v1 legacy (Saladillo), comportamiento
idéntico al actual — no romper el flujo del otro agente.

### 4. Modo lote

```powershell
python scripts\sibom_scraper.py download --rango 1-135 --omitir 108
```

Pipeline por ciudad en estado `pendiente`: index-bulletins → index-contents →
download → download-anexos. Al terminar cada ciudad, su estado pasa a `completa`
y se imprime resumen (normas descargadas, errores). Un fallo de ciudad NO corta
el lote: se loguea en `errores.log` y se continúa con la siguiente.

Flags: `--solo-indexar` (inventario sin descarga), `--reanudar` (default:
salta ciudades `completa`).

### 5. Paneles desconocidos

El parser de paneles ya es genérico (`panel-{kind}`). v2 agrega **log de
advertencia** cuando aparece un `panel-{kind}` fuera de `{ordinance, decree_de}`
(posibles `resolucion`, `disposicion`, etc. en otros municipios) → revisar y
agregar al mapa `TIPO_PANEL` si corresponde. No perder contenido silenciosamente.

### 6. `status` global

`python scripts\sibom_scraper.py status --global` → tabla por ciudad:
id, slug, boletines, contenidos, hechos, pendientes, errores, estado.

## Tareas de implementación (orden)

1. [ ] Refactor de rutas: resolver `dirs(ciudad=None)` que devuelva las rutas
       legacy o por-ciudad según flag. Todas las funciones usan ese resolver.
2. [ ] Utilidad `slugify(nombre)` + lectura de `ciudades.json`.
3. [ ] Subcomando `index-cities` (+ omisión del 108).
4. [ ] Plomería `--ciudad` en los 5 subcomandos existentes.
5. [ ] Modo lote `--rango` con manejo de fallos por ciudad.
6. [ ] Warning de paneles desconocidos (log + contador en status).
7. [ ] `status --global`.
8. [ ] Prueba piloto v2 con UNA ciudad chica (ej: 7 o 109 Salliqueló, ~8
       boletines): validar layout, front-matter idéntico a v1, estado per-city.

## Validación v2

1. `index-cities` → `ciudades.json` con ~134 ciudades, 108 marcada omitida,
   vacías/inexistentes correctamente clasificadas.
2. Piloto ciudad chica: archivos en `sibom/{id:03d}-{slug}/ordenanzas|decretos/`,
   estado en `sibom/_estado/{id}/`, formato .md idéntico al piloto v1.
3. `status --global` refleja la ciudad piloto `completa` y el resto `pendiente`.
4. Regresión: `download --boletin 128` (sin `--ciudad`) sigue operando sobre el
   layout legacy de Saladillo sin errores.
5. `errores.log` sin entradas nuevas.

## Notas operativas

- **No bajar el delay** (0,4 s). Con volumen provincial, un bloqueo de IP
  frenaría todo el proyecto.
- Para corridas largas usar el patrón desatendido de `PLAN-SIBOM.md`
  (`Start-Process ... -RedirectStandardOutput`), un log por lote.
- El lote completo (1-135) puede tardar días: preferir tandas por rango
  (ej: 1-40, 41-80, 81-135) y monitorear con `status --global`.
- `contenidos.json` por ciudad es la fuente de verdad; idempotencia y
  reanudación idénticas a v1.
- No tocar `sibom/ordenanzas`, `sibom/decretos`, `sibom/anexos` ni
  `sibom/_estado/*.json` raíz: son de Saladillo v1.
