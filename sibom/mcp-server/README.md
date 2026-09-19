# SIBOM MCP Server

Servidor MCP (Model Context Protocol) multi-municipio de alto rendimiento para consulta y análisis normativo de la Provincia de Buenos Aires (SIBOM).

## Características principales
- **17 herramientas normativas**: 15 herramientas equivalentes al servidor de ordenanzas original más compilación temática y comparación intermunicipal.
- **Acceso SQLite de solo lectura**: La base de datos fuente `sibom.db` se abre estrictamente con `mode=ro` y `PRAGMA query_only = ON`.
- **Índice derivado separado**: Almacena taxonomía versionada, asignaciones, entidades, vectores de artículos y manifiestos en `data/sibom-index.db`.
- **Búsqueda híbrida**: Búsqueda textual mediante SQLite FTS5 con ranking BM25 combinada con similitud semántica coseno sobre matrices NumPy en memoria y fusión RRF.
- **Transporte stdio puro**: FastMCP sobre entrada/salida estándar, con registro de logs confinado a `stderr`.

---

## Requisitos
- Python 3.11+ (Probado con Python 3.13 en Windows).
- Dependencias: `fastmcp`, `mcp`, `numpy`, `sentence-transformers`, `pydantic`, `pytest`.

---

## Instalación y Configuración (PowerShell)

### 1. Variables de entorno recomendadas
Crear archivo `.env` en la raíz de `mcp-server` o definir variables en la sesión:
```powershell
$env:SIBOM_DB_PATH = "C:\Users\aabad\Documents\CODE\ordenanzas\sibom\sibom.db"
$env:SIBOM_INDEX_DB_PATH = "C:\Users\aabad\Documents\CODE\ordenanzas\sibom\mcp-server\data\sibom-index.db"
$env:GROQ_API_KEY = "tu_clave_aqui"  # Opcional, para resúmenes LLM
```

### 2. Construcción del índice derivado
Para indexar artículos y sembrar la taxonomía:
```powershell
python -m sibom_mcp.indexer --db $env:SIBOM_DB_PATH --output $env:SIBOM_INDEX_DB_PATH
```

### 3. Ejecución del servidor MCP
```powershell
python -m sibom_mcp
```

### 4. Ejecución de la suite de pruebas
```powershell
python -m pytest -v
```

---

## Catálogo de Herramientas (17)

| Herramienta | Función Principal |
|---|---|
| `sibom_search_normas` | Búsqueda textual full-text FTS5 con ranking BM25 y filtros de tipo y municipio. |
| `sibom_search_by_category` | Búsqueda de normas por slug de categoría taxonómica versionada. |
| `sibom_search_by_year_range` | Búsqueda cronológica por rango de años inclusivo (`desde`..`hasta`). |
| `sibom_get_norma` | Detalle completo por ID: texto, artículos, referencias, anexos y categorías. |
| `sibom_get_anexo` | Consulta segura de anexos PDF con extracción de texto disponible. |
| `sibom_search_by_entity` | Búsqueda de normas asociadas a personas, empresas u organismos con evidencia. |
| `sibom_get_references` | Árbol de vigencia y referencias normativas con control de ciclos y profundidad. |
| `sibom_list_categories` | Catálogo jerárquico de categorías y conteos de normas asignadas. |
| `sibom_get_stats` | Estadísticas generales de normas, municipios, años y cobertura de embeddings. |
| `sibom_similar_normas` | Similitud semántica vectorial respecto a una norma consultada. |
| `sibom_summarize_texto` | Generación de resúmenes legales con LLM y caché persistente de hashes. |
| `sibom_health_check` | Diagnóstico del estado del servidor, conectividad DB, FTS5 y modelos. |
| `sibom_semantic_search` | Búsqueda conceptual en normas mediante embeddings y matrices NumPy. |
| `sibom_semantic_search_articulos` | Búsqueda semántica a nivel de artículo individual en el índice derivado. |
| `sibom_full_semantic_search` | Búsqueda semántica combinada de normas y artículos con identidad diferenciada. |
| `sibom_compilar_tematica` | Generación de dossiers temáticos normativos estructurados y en Markdown. |
| `sibom_comparar_intermunicipal` | Comparación de antecedentes normativos entre municipios de referencia y destino. |
