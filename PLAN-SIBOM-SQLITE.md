# PLAN — Ingesta SIBOM a SQLite, Extracción GLM-4.7-Flash y Grafo de Vigencia

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformar los 20.601 archivos Markdown de Saladillo en `sibom/` en una base de datos relacional SQLite (`sibom/sibom.db`) semánticamente enriquecida con GLM-4.7-Flash (Zhipu AI), que descomponga artículos, extraiga el árbol de vigencia (derogaciones totales, parciales y modificaciones), genere resúmenes estructurados (trata, resuelve, depende) y almacene embeddings vectoriales.

**Architecture:** Pipeline modular en Python/SQLite en 4 etapas: (1) Esquema relacional SQLite compatible con el modelo existente del repositorio (normas, articulos, referencias_normativas, anexos y FTS5); (2) Ingesta estructural instantánea de metadatos front-matter e ingesta directa de decretos extractados; (3) Extractor concurrente GLM-4.7-Flash (API BigModel gratuita) con salida JSON unificada (summary + articulos + relaciones de vigencia) y actualización en cascada de estados normativos; (4) Vectorización de summary y texto completo guardados como BLOB float32 para búsqueda semántica híbrida.

**Tech Stack:** Python 3.13, SQLite3 (FTS5 + JSON1), OpenAI SDK / Requests (para BigModel GLM-4.7-Flash API), Ollama (`nomic-embed-text` para embeddings vectoriales locales).

---

## 1. Esquema de Base de Datos (`sibom/sibom.db`)

### Tabla `normas`
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `tipo` TEXT NOT NULL CHECK(tipo IN ('ordenanza', 'decreto'))
- `numero` INTEGER
- `anio` INTEGER
- `numero_sibom` TEXT
- `fecha` TEXT (YYYY-MM-DD)
- `boletin` INTEGER
- `boletin_id` INTEGER
- `contenido_id` INTEGER UNIQUE NOT NULL
- `version` TEXT NOT NULL CHECK(version IN ('completa', 'extractada'))
- `titulo` TEXT NOT NULL
- `seccion_visto` TEXT
- `seccion_considerando` TEXT
- `texto_completo` TEXT NOT NULL
- `estado` TEXT NOT NULL DEFAULT 'vigente' CHECK(estado IN ('vigente', 'modificada', 'derogada_total', 'derogada_parcial', 'sin_determinar'))
- `notas_vigencia` TEXT
- `summary` TEXT (Texto legible unificado)
- `summary_trata` TEXT (Materia / objeto)
- `summary_resuelve` TEXT (Disposición resolutiva)
- `summary_depende` TEXT (Antecedentes: expedientes, leyes, normas)
- `embedding_summary` BLOB (Vector float32)
- `embedding_texto` BLOB (Vector float32)
- `tambien_en` TEXT (JSON array de boletines que republicaron)
- `url` TEXT NOT NULL
- `archivo_md` TEXT NOT NULL
- `localidad` TEXT NOT NULL DEFAULT 'Saladillo'
- `codigo_localidad` INTEGER NOT NULL DEFAULT 108
- `procesado_llm` INTEGER NOT NULL DEFAULT 0 (0: pendiente, 1: hecho, 2: extractada_directa, -1: error)
- `fecha_procesado_llm` TEXT
- `created_at` TEXT DEFAULT CURRENT_TIMESTAMP

### Tabla `articulos`
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `norma_id` INTEGER NOT NULL REFERENCES normas(id) ON DELETE CASCADE
- `numero_articulo` TEXT NOT NULL (ej: "1", "2", "3 bis")
- `orden` INTEGER NOT NULL (1, 2, 3...)
- `texto` TEXT NOT NULL
- `resumen` TEXT
- `estado` TEXT NOT NULL DEFAULT 'vigente' CHECK(estado IN ('vigente', 'modificado', 'derogado', 'sin_determinar'))
- `modificado_por_norma_id` INTEGER REFERENCES normas(id) ON DELETE SET NULL
- `created_at` TEXT DEFAULT CURRENT_TIMESTAMP
- UNIQUE(norma_id, numero_articulo)

### Tabla `referencias_normativas` (Grafo de Vigencia)
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `norma_origen_id` INTEGER NOT NULL REFERENCES normas(id) ON DELETE CASCADE
- `norma_destino_id` INTEGER REFERENCES normas(id) ON DELETE SET NULL
- `destino_tipo` TEXT NOT NULL (ordenanza, decreto, ley_provincial, decreto_provincial, ley_nacional, otro)
- `destino_numero` INTEGER
- `destino_anio` INTEGER
- `destino_referencia` TEXT (ej: "Ley Provincial 11.723", "Decreto-Ley 6769/58", "Expte 145/2023")
- `tipo_relacion` TEXT NOT NULL CHECK(tipo_relacion IN (
    'deroga_total',
    'deroga_parcial',
    'modifica',
    'sustituye',
    'prorroga',
    'convalida',
    'adhiere',
    'reglamenta',
    'cita'
  ))
- `articulos_afectados` TEXT (ej: "Arts. 1, 3", "Art. 5 bis")
- `texto_cita` TEXT (Fragmento literal de la norma que formula la derogación/modificación)
- `notas` TEXT
- `created_at` TEXT DEFAULT CURRENT_TIMESTAMP

### Tabla `anexos`
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `norma_id` INTEGER NOT NULL REFERENCES normas(id) ON DELETE CASCADE
- `nombre` TEXT NOT NULL
- `archivo_pdf` TEXT (Ruta relativa en sibom/anexos/)
- `url` TEXT NOT NULL

### Tabla Virtual FTS5 `normas_fts`
- Búsqueda Full-Text por `titulo`, `summary`, `texto_completo`, `seccion_visto`, `seccion_considerando`.

### Vista Recursiva `v_arbol_vigencia`
- Resuelve relaciones entrantes (`afectada_por`) y salientes (`afecta_a`) permitiendo reconstruir la vigencia histórica completa.

---

## 2. Desglose de Fases y Tareas

### Tarea 1: Inicialización de la Base de Datos SQLite
**Archivos:**
- Crear: `scripts/sibom_db_init.py`
- Salida: `sibom/sibom.db`

- Crear: `scripts/sibom_db_init.py`
- Salida: `sibom/sibom.db`

- [x] **Paso 1.1**: Escribir DDL SQL con todas las tablas, índices (`idx_normas_num_anio`, `idx_ref_origen`, `idx_ref_destino`, `idx_articulos_norma`), tabla virtual FTS5 y triggers de sincronización.
- [x] **Paso 1.2**: Ejecutar `python scripts/sibom_db_init.py` y validar la creación de `sibom/sibom.db`.

---

### Tarea 2: Ingesta Base de los 20.601 Archivos Markdown
**Archivos:**
- Crear: `scripts/sibom_ingest_markdown.py`

- [x] **Paso 2.1**: Desarrollar lector de archivos `.md` en `sibom/ordenanzas` y `sibom/decretos`:
  - Parsea YAML front-matter (`tipo`, `numero`, `anio`, `fecha`, `boletin`, `url`, `version`, etc.).
  - Extrae secciones `VISTO` y `CONSIDERANDO` con regex.
  - Para los decretos `version: extractada` (14.182):
    - Prellena `summary` = texto del extracto.
    - Asigna `procesado_llm = 2` (resuelto por extracto oficial, sin costo de API).
- [x] **Paso 2.2**: Cargar los 350 registros de anexos vinculados en la tabla `anexos`.
- [x] **Paso 2.3**: Ejecutar la ingesta masiva y verificar paridad 1:1 con SQLite (20.601 normas cargadas).

---

### Tarea 3: Extractor Concurrente GLM Flash (Summary + Artículos + Relaciones)
**Archivos:**
- Crear: `scripts/sibom_enrich_glm.py`
- Utiliza: `BIGMODEL_API_KEY` desde `.env` (modelos `glm-4.7-flash` / `glm-4-flash` en `https://open.bigmodel.cn/api/paas/v4/`).

- [x] **Paso 3.1**: Definir el System Prompt y JSON Schema estricto:
  - `summary`: `{"trata": "...", "resuelve": "...", "depende": "..."}`
  - Desglose determinístico de artículos con parser regex en Python (cero alucinación, 100% fidelidad de texto).
  - `relaciones`: `[{"tipo": "deroga_total|deroga_parcial|modifica|sustituye|convalida|adhiere|cita", "destino_tipo": "ordenanza|decreto|ley_provincial", "destino_numero": ..., "destino_anio": ..., "articulos_afectados": "...", "texto_cita": "..."}]`
- [x] **Paso 3.2**: Implementar worker pool concurrente (4 a 6 workers paralelos) con manejo de reintentos y fallback ante saturación 429.
- [x] **Paso 3.3**: Guardado incremental en `sibom.db` (enriqueciendo `normas`, insertando filas en `articulos` y en `referencias_normativas`).
- [x] **Paso 3.4**: Modo de ejecución selectivo:
  - Subcomando `--ordenanzas`: Procesa las ordenanzas pendientes (en ejecución concurrente).
  - Subcomando `--status`: Muestra progreso en tiempo real.

---

### Tarea 4: Motor de Cruce de Vigencia y Derogaciones en Cascada
**Archivos:**
- Crear: `scripts/sibom_reconcile_vigencia.py`

- [x] **Paso 4.1**: Mapear referencias salientes a normas locales existentes en `sibom.db`:
  - Cruza `destino_tipo`, `destino_numero`, `destino_anio` con `normas(tipo, numero, anio)` para poblar `norma_destino_id`.
- [x] **Paso 4.2**: Aplicar impacto en cascada:
  - Si `tipo_relacion == 'deroga_total'`: actualiza `normas.estado = 'derogada_total'` y todos sus artículos a `'derogado'`.
  - Si `tipo_relacion == 'deroga_parcial'`: actualiza `normas.estado = 'derogada_parcial'` y los artículos específicos mencionados a `'derogado'`.
  - Si `tipo_relacion in ('modifica', 'sustituye')`: actualiza `normas.estado = 'modificada'` y los artículos específicos a `'modificado'`.
- [x] **Paso 4.3**: Generar reporte de vigencia `sibom/_estado/arbol-vigencia-resumen.csv`.

---

### Tarea 5: Vectorización y Embeddings Duales
**Archivos:**
- Crear: `scripts/sibom_generate_embeddings.py`

- [x] **Paso 5.1**: Conectar con modelo de embeddings multilingüe (`paraphrase-multilingual-MiniLM-L12-v2` vía `sentence-transformers`).
- [x] **Paso 5.2**: Generar embeddings en batches para:
  1. `summary` de cada norma.
  2. `texto_completo` (primeros 2.500 caracteres representativos).
- [x] **Paso 5.3**: Guardar los vectores serializados en `embedding_summary` y `embedding_texto` (`BLOB` float32) y búsqueda vectorial por coseno.

---

### Tarea 6: Validación Final y Scripts de Consulta
**Archivos:**
- Crear: `scripts/sibom_query.py`

- [x] **Paso 6.1**: Verificación de integridad:
  - Conteo total de normas: 20.601 en `sibom.db`.
  - Conteo de artículos y relaciones desglosadas.
- [x] **Paso 6.2**: Pruebas de consulta con `scripts/sibom_query.py`:
  - `buscar "termino"` (búsqueda FTS5 BM25).
  - `buscar-semantica "consulta"` (búsqueda vectorial por embeddings).
  - `ver --tipo ordenanza --numero X --anio Y` (muestra front-matter, artículos y árbol de vigencia).
  - `arbol --tipo ordenanza --numero X --anio Y` (historial de derogaciones y vigencia).
