# MCP Server de Ordenanzas Municipales de Saladillo

Servidor MCP para consultar y analizar ordenanzas municipales usando Claude Desktop.

## Características

- **11 herramientas MCP** para consulta y análisis
- Búsqueda full-text con ranking FTS
- Búsqueda semántica con embeddings vectoriales
- Generación de resúmenes con IA (Groq Llama 3.3 70B)
- Estadísticas de procesamiento
- Acceso a datos detallados de ordenanzas

- **Cache inteligente** para reducir costos de API:
  - Embeddings almacenados en DB (TEXT format)
  - Resúmenes cacheados por parámetros
- **Logging verboso** configurable

## Instalación

```bash
# Instalar dependencias
npm install

# Crear tablas de cache en la base de datos
npx tsx src/db/setup-cache.ts
```

## Configuración

### Variables de Entorno

Crear archivo `.env` con:

```bash
# Database (obligatorio)
DATABASE_URL=postgresql://usuario:contrasena@host:5432/db_ordenanzas

# API Keys (obligatorios para funcionalidades de IA)
GROQ_API_KEY=gsk_...  # Para resúmenes
OPENAI_API_KEY=sk-...  # Para embeddings

# Opcionales
VERBOSE=true              # Habilita logging detallado
LOG_LEVEL=debug         # debug, info, warn, error
NODE_ENV=development  # Formato pretty de logs
```

### Configuración de Claude Desktop

Agregar a `~/.claude/config.json`:

```json
{
  "mcpServers": {
    "ordenanzas": {
      "command": "npx",
      "args": ["tsx", "C:\\Users\\Adria\\Documents\\code\\ordenanzas\\src\\mcp-server\\index.ts"],
      "env": {
        "DATABASE_URL": "postgresql://...",
        "GROQ_API_KEY": "gsk_...",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

## Ejecución

### Modo desarrollo
```bash
# Ejecutar con logging verbose
VERBOSE=true npx tsx src/mcp-server/index.ts
```

### Modo producción (VPS)
```bash
# Ejecutar en segundo plano
npx tsx src/mcp-server/index.ts &
```

## Herramientas MCP

### Búsqueda
| Tool | Descripción |
|------|-------------|
| `search_ordenanzas` | Búsqueda full-text de ordenanzas con ranking de relevancia FTS |
| `search_by_category` | Filtra ordenanzas por categoría específica y año |
| `search_by_year_range` | Consultas históricas por rango de años |

### Detalle por ID
| Tool | Descripción |
|------|-------------|
| `get_ordenanza` | Obtiene ordenanza completa con artículos, entidades, referencias, montos, anexos y categorías |
| `get_anexo` | Obtiene el contenido de un anexo específico |

### Búsqueda por Entidad
| Tool | Descripción |
|------|-------------|
| `search_by_entity` | Busca ordenanzas que mencionan una entidad (persona, empresa, organismo, etc.) |

### Referencias
| Tool | Descripción |
|------|-------------|
| `get_references` | Obtiene el árbol de vigencia y referencias normativas (qué ordenanzas modifica, deroga, cita, etc.) |

### Categorías y Estadísticas
| Tool | Descripción |
|------|-------------|
| `list_categories` | Lista todas las categorías disponibles |
| `get_stats` | Obtiene estadísticas de procesamiento (total, procesadas, pendientes, top categorías, distribución por año) |

### IA y Similitud
| Tool | Descripción |
|------|-------------|
| `similar_ordenanzas` | Búsqueda semántica usando embeddings vectoriales (OpenAI) y cosine similarity en memoria |
| `summarize_texto` | Genera resúmenes de texto arbitrario usando Groq Llama 3.3 70B con cache |

### Sistema
| Tool | Descripción |
|------|-------------|
| `health_check` | Verifica estado del servidor y conectividad con la base de datos |

## Workflow del Asistente Jurídico

El servidor MCP permite actuar como asistente jurídico del municipio:

1. **"¿Qué ordenanzas sobre salud hay en el municipio?"**
   - `search_ordenanzas` + `search_by_category(slug: "salud-publica")`

2. **"¿Qué propuestas de ordenanza de salud podríamos hacer?"**
   - `get_stats` - Entender estado actual
   - `search_by_year_range` - Ver precedentes históricos
   - `similar_ordenanzas` - Encontrar precedentes semánticamente similares
   - `summarize_texto` - Generar propuesta basada en contexto

## Arquitectura

```
src/mcp-server/
├── index.ts              # Servidor principal (@modelcontextprotocol/sdk)
├── db.ts                # Connection pool PostgreSQL
├── logger.ts             # Logger (pino, configurable)
├── utils.ts              # Utils (error handlers, formatters, cosine similarity)
├── types.ts              # TypeScript schemas (todos los tipos)
├── embeddings.ts           # Cliente OpenAI para embeddings
├── llm.ts                # Cliente Groq para resúmenes
└── tools/
    ├── index.ts           # Exportador de herramientas
    ├── search.ts           # 3 tools de búsqueda
    ├── by-id.ts           # 2 tools de detalle
    ├── by-entity.ts        # 1 tool de búsqueda por entidad
    ├── references.ts        # 1 tool de referencias
    ├── categories.ts        # 1 tool de categorías
    ├── stats.ts            # 2 tools de estadísticas
    ├── similar.ts           # 1 tool de similitud (embeddings)
    ├── summarize.ts         # 1 tool de resúmenes
    └── health.ts           # 1 tool de health check
```

## Base de Datos

### Tablas principales (existentes)
- `ordenanzas` - 2789 ordenanzas con texto completo
- `articulos` - Artículos de cada ordenanza
- `ordenanza_entidades` - Relación entre ordenanzas y entidades
- `entidades` - Personas, empresas, organismos
- `categorias` - 53 categorías de clasificación
- `ordenanza_categorias` - Relación muchos-a-muchos ordenanza-categoría
- `referencias_normativas` - Referencias entre ordenanzas
- `montos` - Montos económicos en ordenanzas
- `anexos` - Documentos adjuntos

### Tablas de cache (nuevas)
- `embeddings_cache` - Almacena embeddings vectoriales como TEXT (1536 dimensiones, OpenAI text-embedding-3-small)
- `resumenes_cache` - Cache de resúmenes generados por IA (Groq Llama 3. 3 70B)

## Costos Estimados de API

| Componente | Modelo | Costo Estimado |
|-----------|-------|-------------------|
| Embeddings (1 por ordenanza) | OpenAI text-embedding-3-small | ~$0.02 por 1000 ordenanzas |
| Resúmenes (variable) | Groq Llama 3.3 70B | ~$0.0006 por resumen (500 palabras) |
| **Total inicial** | ~$50-100 para 2789 ordenanzas | **Total con cache** | ~$2-10 |

## Troubleshooting

### Logging
Habilitar `VERBOSE=true` para ver logs detallados de cada operación.

### Erres comunes

- **Error "No se encontró ordenanza"**: Verificar que el ID sea correcto
- **Error de conexión a DB**: Revisar `DATABASE_URL` en `.env`
- **Error de API**: Verificar que `GROQ_API_KEY` y `OPENAI_API_KEY` están configurados

### Performance
- La búsqueda semántica carga todos los embeddings en memoria al iniciar
- Para conjuntos grandes, considera implementar paginación en `getAllEmbeddingsForSimilarity`

## Desarrollo

### Tests
```bash
# Ejecutar tests unitarios
npm test

# Ejecutar tests con cobertura
npm run test -- --coverage
```
