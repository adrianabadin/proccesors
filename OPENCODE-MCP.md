# Servidor MCP de Ordenanzas Municipales de Saladillo

## 📋 Resumen

El proyecto incluye un servidor MCP (Model Context Protocol) compatible con OpenCode que proporciona **11 herramientas especializadas** para consulta y análisis de ordenanzas municipales.

Este servidor permite a OpenCode realizar consultas complejas sobre ordenanzas sin necesidad de escribir SQL manualmente.

---

## 🎯 Características

- **11 herramientas especializadas** para consulta y análisis
- **Búsqueda full-text** con ranking de relevancia
- **Búsqueda semántica** con embeddings vectoriales
- **Análisis completo** con referencias, entidades, montos y anexos
- **Generación de resúmenes** con IA (Groq Llama 3.3 70B)
- **Cache inteligente** para reducir costos de API

---

## 🛠️ Configuración

### Archivo de Configuración

El servidor se configura en `opencode.jsonc` en la raíz del proyecto:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "ordenanzas-saladillo": {
      "type": "local",
      "command": ["npx", "tsx", "src/mcp-server/index.ts"],
      "environment": {
        "DATABASE_URL": "{env:DATABASE_URL}",
        "GROQ_API_KEY": "{env:GROQ_API_KEY}",
        "OPENAI_API_KEY": "{env:GROQ_API_KEY}",
        "VERBOSE": "false",
        "LOG_LEVEL": "info"
      },
      "enabled": false
    }
  }
}
```

### Variables de Entorno

El servidor requiere las siguientes variables de entorno (configuradas en `.env`):

```bash
# Database (obligatorio)
DATABASE_URL=postgresql://usuario:contraseña@host:5432/db_ordenanzas

# API Keys (obligatorias)
GROQ_API_KEY=gsk_...         # Para resúmenes y embeddings
OPENAI_API_KEY=gsk_...       # (usa GROQ_API_KEY por defecto)

# Opcionales
VERBOSE=false               # Habilita logging detallado
LOG_LEVEL=debug            # debug, info, warn, error
NODE_ENV=development         # Formato pretty de logs
```

---

## 🚀 Habilitar el Servidor MCP

Por defecto, el servidor MCP está **deshabilitado** (`enabled: false`) para evitar cargar herramientas innecesarias al contexto.

Para habilitar:

1. Abre `opencode.jsonc`
2. Cambia `"enabled": false` a `"enabled": true`
3. Guarda el archivo
4. Reinicia OpenCode

---

## 📦 Herramientas Disponibles (11)

### Herramientas de Búsqueda (3)

#### `ordenanzas-saladillo_search_ordenanzas`
Búsqueda full-text de ordenanzas con ranking de relevancia FTS.

**Parámetros**:
- `query` (string): Término de búsqueda
- `limit` (number, opcional): Número máximo de resultados (default: 10)

#### `ordenanzas-saladillo_search_by_category`
Filtra ordenanzas por categoría específica y año.

**Parámetros**:
- `slug` (string): Slug de la categoría
- `anio` (number, opcional): Año para filtrar

#### `ordenanzas-saladillo_search_by_year_range`
Consultas históricas por rango de años.

**Parámetros**:
- `desde` (number): Año inicial
- `hasta` (number): Año final
- `limit` (number, opcional): Número máximo de resultados

---

### Herramientas de Detalle por ID (2)

#### `ordenanzas-saladillo_get_ordenanza`
Obtiene ordenanza completa con todos sus detalles.

**Parámetros**:
- `id` (string): UUID de la ordenanza

**Devuelve**: Artículos, entidades, referencias, montos, anexos y categorías

#### `ordenanzas-saladillo_get_anexo`
Obtiene el contenido de un anexo específico.

**Parámetros**:
- `id` (string): UUID de la ordenanza
- `numero` (number): Número del anexo

---

### Herramienta de Búsqueda por Entidad (1)

#### `ordenanzas-saladillo_search_by_entity`
Busca ordenanzas que mencionan una entidad (persona, empresa, organismo, etc.).

**Parámetros**:
- `nombre` (string): Nombre de la entidad
- `rol` (string, opcional): Tipo de rol (ej: "firmante", "beneficiario", "citado")

---

### Herramienta de Referencias (1)

#### `ordenanzas-saladillo_get_references`
Obtiene el árbol de vigencia y referencias normativas.

**Parámetros**:
- `id` (string): UUID de la ordenanza

**Devuelve**: Qué ordenanzas modifica, deroga, cita, etc.

---

### Herramientas de Categorías y Estadísticas (2)

#### `ordenanzas-saladillo_list_categories`
Lista todas las categorías disponibles en el sistema.

**Sin parámetros**

#### `ordenanzas-saladillo_get_stats`
Obtiene estadísticas de procesamiento de ordenanzas.

**Devuelve**: Total, procesadas, pendientes, top categorías, distribución por año

---

### Herramientas de IA y Similitud (2)

#### `ordenanzas-saladillo_similar_ordenanzas`
Búsqueda semántica usando embeddings vectoriales y cosine similarity.

**Parámetros**:
- `id` (string): UUID de la ordenanza de referencia
- `limit` (number, opcional): Número máximo de resultados similares

**Nota**: Usa embeddings cacheados en la base de datos para reducir costos.

#### `ordenanzas-saladillo_summarize_texto`
Genera resúmenes de texto arbitrario usando Groq Llama 3.3 70B.

**Parámetros**:
- `texto` (string): Texto a resumir
- `estilo` (string, opcional): Estilo de resumen ("conciso", "detallado", "técnico")
- `longitud_palabras` (number, opcional): Longitud aproximada en palabras

**Nota**: Usa cache para evitar reprocesar el mismo texto.

---

### Herramienta de Sistema (1)

#### `ordenanzas-saladillo_health_check`
Verifica estado del servidor y conectividad con la base de datos.

**Sin parámetros**

**Devuelve**: Estado del servidor, versión, conexión a BD, uptime

---

## 🔄 Caché y Performance

### Embeddings Cache
Los embeddings vectoriales se almacenan en la tabla `embeddings_cache` de la base de datos para:
- Reducir costos de API
- Acelerar búsquedas semánticas
- Evitar reprocesamiento

### Resúmenes Cache
Los resúmenes generados se cachean en la tabla `resumenes_cache` para:
- Evitar reprocesar el mismo texto
- Reducir costos de API
- Mejorar tiempo de respuesta

---

## 🚨 Troubleshooting

### Errores Comunes

**Error: "No se pudo conectar a la base de datos"**
- Verificar que `DATABASE_URL` en `.env` es correcta
- Confirmar que PostgreSQL está ejecutándose
- Verificar credenciales y puerto

**Error: "API key no encontrada"**
- Confirmar que `GROQ_API_KEY` está configurado en `.env`
- Verificar que la API key es válida

**Error: "Servidor MCP no responde"**
- Verificar que el servidor MCP está habilitado (`enabled: true`)
- Revisar logs del servidor MCP para errores
- Intentar reiniciar OpenCode

### Logging

Para activar logging detallado:

1. Cambia `VERBOSE` a `true` en `opencode.jsonc`
2. Ajusta `LOG_LEVEL` a `debug` si necesitas más detalles
3. Reinicia OpenCode

Los logs del servidor MCP aparecerán en la terminal de OpenCode.

---

## 📊 Arquitectura del Servidor

```
┌─────────────────────────────────────────────────────┐
│         OpenCode (Asistente)                │
└─────────────────┬───────────────────────────┘
                  │
                  │ MCP Protocol
                  ▼
┌─────────────────────────────────────────────────────┐
│   Servidor MCP de Ordenanzas                   │
│   (src/mcp-server/index.ts)                │
│                                             │
│   ┌──────────────────────────────────────┐    │
│   │ 11 Herramientas                 │    │
│   │ - search_ordenanzas               │    │
│   │ - search_by_category              │    │
│   │ - get_ordenanza                  │    │
│   │ - similar_ordenanzas              │    │
│   │ - summarize_texto                │    │
│   │ - ... (6 más)                  │    │
│   └──────────────────────────────────────┘    │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│   PostgreSQL Database                        │
│   - ordenanzas (2789 registros)          │
│   - artículos, entidades, categorías         │
│   - referencias, montos, anexos           │
│   - embeddings_cache, resumenes_cache        │
└─────────────────────────────────────────────────────┘
```

---

## 📖 Referencias Adicionales

- **Documentación del Proyecto**: Ver `CLAUDE.md` para información general del proyecto
- **Reglas Automáticas**: Ver `AGENTS.md` para configurar el comportamiento automático de OpenCode
- **Processor Concurrente**: Ver `src/processor/README-concurrent-deepseek.md` para información sobre procesamiento con IA

---

## ✅ Verificación

Para verificar que el servidor MCP está funcionando correctamente:

1. Habilita el servidor en `opencode.jsonc` (`enabled: true`)
2. Reinicia OpenCode
3. Ejecuta un comando de prueba: "Muestra las estadísticas del sistema de ordenanzas"
4. OpenCode debería usar la herramienta `ordenanzas-saladillo_get_stats` automáticamente

Si todo funciona correctamente, verás las estadísticas de procesamiento de ordenanzas.