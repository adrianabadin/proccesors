# AGENTS.md - Reglas para Asistente de Coding

Este archivo define reglas automáticas que OpenCode (el asistente de coding) debe seguir cuando trabaja con el proyecto de ordenanzas municipales.

---

## 🎯 Principio General

**Prioriza siempre el uso de las herramientas del servidor MCP de ordenanzas en lugar de consultas SQL directas.**

Las herramientas MCP proporcionan:
- Interfaz especializada y amigable
- Validación automática de parámetros
- Manejo robusto de errores
- Contexto enriquecido con metadatos

**Solo usa SQL directo cuando las herramientas MCP no cubren el caso de uso.**

---

## 📋 Reglas por Categoría

### 1. Búsqueda y Consulta

Cuando necesites buscar ordenanzas:

#### **Primero, intenta estas herramientas MCP:**
- `ordenanzas-saladillo_search_ordenanzas` - Para búsquedas full-text con ranking
- `ordenanzas-saladillo_search_by_category` - Para filtrar por categoría específica
- `ordenanzas-saladillo_search_by_year_range` - Para análisis histórico por rango de años
- `ordenanzas-saladillo_search_by_entity` - Para buscar ordenanzas que mencionan una entidad

#### **Solo usa SQL directo si:**
- Necesitas joins complejos no soportados por las herramientas
- Necesitas agregaciones personalizadas
- Las herramientas MCP no funcionan para tu caso específico

### 2. Consulta de Detalles

Cuando necesites detalles específicos de una ordenanza:

#### **Usa herramientas MCP:**
- `ordenanzas-saladillo_get_ordenanza` - Para obtener ordenanza completa con artículos, entidades, referencias, montos, anexos y categorías
- `ordenanzas-saladillo_get_anexo` - Para obtener contenido de un anexo específico

#### **No uses SQL directo para:**
- Consultar tablas individuales de ordenanzas
- Obtener artículos de una ordenanza
- Buscar entidades relacionadas
- Consultar referencias normativas

### 3. Análisis y Comparación

Cuando necesites analizar o comparar ordenanzas:

#### **Usa herramientas MCP:**
- `ordenanzas-saladillo_similar_ordenanzas` - Para encontrar precedentes semánticamente similares
- `ordenanzas-saladillo_get_references` - Para entender el árbol de vigencia y referencias normativas

#### **Solo usa SQL directo si:**
- Necesitas análisis de similitud personalizado
- Requieres joins complejos de referencias
- Las herramientas MCP no cubren tu análisis específico

### 4. Generación de Resúmenes

Cuando necesites resumir texto:

#### **Usa herramienta MCP:**
- `ordenanzas-saladillo_summarize_texto` - Para generar resúmenes con IA (Groq Llama 3.3 70B)

#### **Beneficios:**
- Usa cache para evitar reprocesar el mismo texto
- Reduce costos de API
- Proporciona múltiples estilos de resumen

### 5. Consultas de Metadatos

Cuando necesites información sobre el sistema:

#### **Usa herramientas MCP:**
- `ordenanzas-saladillo_list_categories` - Para listar todas las categorías disponibles
- `ordenanzas-saladillo_get_stats` - Para obtener estadísticas de procesamiento (total, procesadas, pendientes, top categorías, distribución por año)
- `ordenanzas-saladillo_health_check` - Para verificar estado del servidor y conectividad con la base de datos

#### **Solo usa SQL directo si:**
- Necesitas métricas personalizadas no disponibles
- Requieres agregaciones complejas no soportadas

---

## 🔄 Flujo de Decisión

```
┌─────────────────────────────────────────────┐
│  ¿Necesito buscar ordenanzas?          │
└────────────────┬────────────────────────┘
               │ Sí
               ▼
┌─────────────────────────────────────────────┐
│  ¿Búsqueda full-text?                  │
└────────────────┬────────────────────────┘
               │ Sí          │ No
               ▼              ▼
     search_ordenanzas   search_by_category
          o por entidad

┌─────────────────────────────────────────────┐
│  ¿Necesito detalles específicos?        │
└────────────────┬────────────────────────┘
               │ Sí
               ▼
      get_ordenanza o get_anexo

┌─────────────────────────────────────────────┐
│  ¿Necesito análisis/comparación?       │
└────────────────┬────────────────────────┘
               │ Sí
               ▼
   similar_ordenanzas o get_references

┌─────────────────────────────────────────────┐
│  ¿Necesito resumir texto?            │
└────────────────┬────────────────────────┘
               │ Sí
               ▼
     summarize_texto

┌─────────────────────────────────────────────┐
│  ¿Necesito información del sistema?      │
└────────────────┬────────────────────────┘
               │ Sí
               ▼
   list_categories, get_stats, health_check
```

---

## ⚠️ Consideraciones Importantes

### 1. Documenta Uso de SQL Directo

Si usas SQL directo, documenta por qué:
```markdown
**Nota**: Usé SQL directo porque las herramientas MCP no soportan [razón específica].
```

Esto ayuda a mejorar las herramientas MCP en el futuro.

### 2. Prioriza Herramientas MCP

El orden de prioridad debe ser:
1. **Herramientas MCP disponibles**
2. **Combinaciones de herramientas MCP**
3. **SQL directo** (último recurso)

### 3. Usa el Nombre Completo de Herramientas

Los nombres de herramientas MCP incluyen el prefijo `ordenanzas-saladillo_`:
- ✅ `ordenanzas-saladillo_search_ordenanzas`
- ❌ `search_ordenanzas` (incorrecto, falta prefijo)

### 4. Aprovecha el Cache

Las herramientas MCP usan cache automático:
- Embeddings cacheados para búsquedas semánticas
- Resúmenes cacheados para evitar reprocesamiento
- No necesitas preocuparte por la eficiencia

### 5. Manejo de Errores

Las herramientas MCP proporcionan mensajes de error claros:
- Si una herramienta falla, el mensaje indica el problema
- Usa el mensaje para ajustar tu consulta o estrategia
- Si es un error de API, intenta nuevamente después de un breve delay

---

## 📊 Ejemplos de Uso Preferido

### ✅ Uso Correcto

```markdown
"Busca ordenanzas sobre salud pública en el año 2020"

→ Usa: ordenanzas-saladillo_search_by_category (slug: "salud-publica", anio: 2020)
```

```markdown
"Encuentra ordenanzas semánticamente similares a la ordenanza sobre transporte"

→ Usa: ordenanzas-saladillo_similar_ordenanzas (id: <uuid>)
```

```markdown
"Resume esta ordenanza de forma concisa"

→ Usa: ordenanzas-saladillo_summarize_texto (texto: <texto>, estilo: "conciso")
```

### ❌ Uso Evitado

```markdown
"Busca ordenanzas sobre salud pública en el año 2020"

→ ❌ No uses: SELECT * FROM ordenanzas WHERE ...
→ ✅ Usa: ordenanzas-saladillo_search_by_category
```

```markdown
"Dame el resumen de esta ordenanza"

→ ❌ No uses: Generar resumen manualmente
→ ✅ Usa: ordenanzas-saladillo_summarize_texto
```

---

## 🚀 Optimización de Rendimiento

### Reduce Contexto Innecesario

Las herramientas MCP agregan contexto al chat de OpenCode. Para optimizar:
- Solo usa las herramientas MCP realmente necesarias
- Deshabilita el servidor MCP si no lo necesitas (`enabled: false` en `opencode.jsonc`)
- Usa filtros específicos en lugar de consultas generales

### Aprovecha Caché de Herramientas

Muchas herramientas MCP usan cache:
- Los resúmenes idénticos usan cache
- Los embeddings de búsquedas semánticas se cachean
- No preocuparte por reprocesar el mismo contenido

---

## 📖 Referencias Adicionales

- **Documentación del Servidor MCP**: Ver `OPENCODE-MCP.md` para información completa de todas las herramientas disponibles
- **Documentación del Proyecto**: Ver `CLAUDE.md` para información general del proyecto
- **Configuración**: Ver `opencode.jsonc` para habilitar/deshabilitar el servidor MCP

---

## 🎯 Objetivo Final

**Estas reglas tienen como objetivo:**
1. ✅ Maximizar el uso de herramientas MCP especializadas
2. ✅ Minimizar el uso de SQL directo
3. ✅ Proporcionar respuestas más eficientes y precisas
4. ✅ Mejorar la experiencia del usuario final
5. ✅ Facilitar el desarrollo de nuevas funcionalidades

**Si tienes dudas sobre cuál herramienta usar, prioriza siempre las herramientas MCP disponibles.**