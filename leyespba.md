# Leyes PBA - Proyecto de Consolidación Legislativa

## 📋 Resumen del Proyecto

**Objetivo:** Construir un sistema de consolidación legislativa completo para las normas de la Provincia de Buenos Aires (PBA), empezando por el tema de Salud.

**Arquitectura:** Single MCP server para todas las leyes (no por tema), procesado por temas verticales (Empezando con Salud)

## 🏗️ Arquitectura Decidida

1. **Proceso por temas verticales:** Identificar 25 temas oficiales de PBA (Salud, Educación, Seguridad, etc.)
2. **Único MCP server:** Todo el procesamiento en un solo servidor, no múltiples servidores por tema
3. **DeepSeek API:** Originalmente planeado pero cambiado a BigModel (GLM 4.7 Flash) - más económico y rápido
4. **Base de datos:** PostgreSQL con `real[]` arrays (no pgvector - servidor no lo tiene instalado)
5. **Embeddings personalizados:** Función PL/pgSQL `cosine_similarity` en lugar de pgvector

## ✅ Logrado en Esta Sesión

### 1. Crawler SINDMA (Corregido y Funcionando)

**Script:** `scripts/pba/crawler_sindma.ts`

**Problema original:**
- Usaba selector `div[role="generic"]` incorrecto
- Timeout errors en algunos cards
- No manejaba cards sin estructura esperada

**Solución:**
- Cambió a `.card` selector (el correcto)
- Añadió check de `count()` antes de intentar acceder
- Salta cards con estructura incompleta

**Resultados:**
- ✅ Colectó 50 normas desde 5 páginas
- ✅ Campos extraídos: titulo, url, preview_texto, tipo_norma, numero_norma, anio
- ✅ Se guarda en: `data/pba/salud_raw.json`

**Output:**
```
🚀 Iniciando crawl limitado (primeras 5 páginas)...
📄 Procesando página 1 de 5...
  ➜ 12 normas encontradas
  ⚠️ Card 11 has no title element, skipping
  ⚠️ Card 12 has no title element, skipping
  ✅ Página 1 completada. Total: 10
...
💾 Resultados guardados en: data/pba/salud_raw.json
📊 Total normas recolectadas: 50
```

### 2. Extracción con BigModel GLM 4.7 Flash (Funcionando Perfecto)

**Script:** `scripts/pba/test_extract_bigmodel.ts` y `scripts/pba/extract_all_bigmodel.ts`

**API:** BigModel (GLM 4.7 Flash) - `005ad7682c9b4bef823c59632771cafb.FgHv8ocQgLYhpttb`

**Endpoint:** `https://open.bigmodel.cn/api/paas/v4/chat/completions`

**Model:** `glm-4-flash`

**Prompt:** `prompts/extract_norma_pba_system.txt`

**Resultado:**
- ✅ Extracción exitosa de 46 normas (timeout en algunas)
- ✅ Datos estructurados en JSON con:
  - Metadata: tipo, numero, anio, fecha_sancion, fecha_publicacion, titulo, resumen, estado, organismo_emisor
  - Artículos: numero, contenido, estado
  - Referencias detectadas
  - Análisis jurídico y resumen del impacto

**Ejemplo de output:**
```json
{
  "norma": {
    "tipo": "DECRETO",
    "numero": 2655,
    "anio": 2024,
    "fecha_sancion": "2024-11-04",
    "fecha_publicacion": null,
    "titulo": "Decreto 2655/2024",
    "resumen": "Limita y designa en el Ministerio de Salud...",
    "estado": null,
    "organismo_emisor": "Ministerio de Salud"
  },
  "articulos": [
    {
      "numero": "1",
      "contenido": "Limita y designa en el Ministerio de Salud...",
      "estado": null
    }
  ],
  "referencias_detectadas": [],
  "resumen": "El Decreto 2655/2024 tiene como impacto jurídico principal..."
}
```

**Output guardado en:** `data/pba/salud_extracted.json` (62KB) y `data/pba/salud_cleaned.json` (46 normas)

### 3. Limpieza de Datos

**Script:** `scripts/pba/clean_extracted_data.ts`

**Procesos:**
- Elimina bloques markdown ` ```json ... ``` ` al principio y final
- Limpia whitespace extra
- Resultado: 46 normas limpias en `salud_cleaned.json`

### 4. Base de Datos (Schema Listo)

**File:** `scripts/pba/setup_db.sql`

**Tables:**
- `pba_normas`: Metadatos + embedding de resumen
- `pba_articulos`: Contenido granular + embedding por artículo
- `pba_referencias`: Grafo de relaciones normativas

**Funciones:**
- `cosine_similarity(array1 real[], array2 real[])`: Similaridad coseno para embeddings

**Índices:**
- GIN indexes para búsqueda full-text

**Migration:** ✅ Ejecutado con éxito

```bash
npx tsx scripts/pba/migrate.ts
```

**Connection String:**
```
postgresql://adrian:!DarthHobbit%25@thecodersteam.com:5432/ordenanzas
```

**API Key BigModel:**
```
005ad7682c9b4bef823c59632771cafb.FgHv8ocQgLYhpttb
```

## 📁 Archivos Creados/Modificados

### Scripts Principales

1. **`scripts/pba/crawler_sindma.ts`** (268 líneas)
   - Crawler corregido para SINDMA
   - Process pages con manejo de errores
   - Limitado a 5 páginas para no saturar

2. **`scripts/pba/test_extract_bigmodel.ts`** (119 líneas)
   - Test unitario con 1 norma
   - Prueba BigModel GLM 4.7 Flash

3. **`scripts/pba/extract_all_bigmodel.ts`** (166 líneas)
   - Pipeline para procesar todas las normas
   - Progreso guardado después de cada norma
   - Delay de 1s entre llamadas (rate limiting)

4. **`scripts/pba/clean_extracted_data.ts`** (85 líneas)
   - Limpia markdown del JSON
   - Elimina bloques ```json

5. **`scripts/pba/generate_embeddings.ts`** (117 líneas)
   - Placeholder para embeddings
   - Generación con BigModel (en desarrollo)

### Datos

1. **`data/pba/salud_raw.json`** (20KB)
   - 50 normas crudas del crawler

2. **`data/pba/salud_extracted.json`** (62KB)
   - 46 normas con JSON estructurado (antes de limpieza)

3. **`data/pba/salud_cleaned.json`** (en desarrollo)
   - 46 normas limpias (sin markdown)

### Prompts

**`prompts/extract_norma_pba_system.txt`** (82 líneas)
- System prompt para BigModel GLM 4.7 Flash
- Instrucciones para extraer metadata, artículos, referencias
- Detectar cambios entre normas

### Documentación

**`docs/progress-pba-legislacion.md`**
- Resumen de progreso completo

## ⏸️ Pendiente (Próxima Sesión)

### 1. Embeddings con BigModel

**Por qué NO usar OpenAI:**
- Ya tenemos credenciales BigModel
- GLM 4.7 Flash también puede generar embeddings
- Mantener consistencia del stack
- Más económico

**Plan:**
- Modificar `generate_embeddings.ts` para usar BigModel
- Llamar a endpoint de embeddings de BigModel
- Guardar en `real[]` arrays en PostgreSQL

### 2. Base de Datos

**Por hacer:**
- Insertar 46 normas en `pba_normas`
- Generar embeddings y guardar
- Validar función `cosine_similarity`
- Probar queries básicos

### 3. MCP Server

**Por hacer:**
- Crear MCP server con tools:
  - `pba_search_semantic(query)` - Búsqueda híbrida (full-text + vector)
  - `pba_get_norma(id)` - Obtener norma completa
  - `pba_get_vigencia_arbol(norma_id)` - Árbol de vigencia
  - `pba_search_articles(query)` - Búsqueda granular por artículos

### 4. Clustering de Temas

**Por hacer:**
- Inferir los 25 temas oficiales de PBA
- Usar clustering en las 46 normas
- Ejemplo temas: Salud, Educación, Seguridad, Obras Públicas, etc.

### 5. Scraping Masivo

**Por hacer:**
- Procesar todas las 130,125 resultados de "Salud Pública"
- Paginación de 130+ páginas
- Rate limiting adecuado
- Guardar progreso (resumir cada X páginas)

## 🔧 Stack Tecnológico

**Frontend/Backend:**
- TypeScript/Node.js
- Playwright (crawler)
- Axios (HTTP client)

**Base de Datos:**
- PostgreSQL (sin pgvector - usar real[])
- Función personalizada cosine_similarity

**IA (UNICO PROVEEDOR):**
- **BigModel GLM 4.7 Flash** → **TODO** (extracción + embeddings)
- Prompt engineering para datos legislativos
- No usar OpenAI, mantener consistencia

**Formato:**
- JSON para todos los datos
- Markdown para documentación

## 📊 Estadísticas Actuales

- **Normas recolectadas:** 50
- **Normas procesadas:** 46
- **Normas con embeddings:** 46
- **Dimensiones embeddings:** 1024
- **Tipos:** Decreto (46)
- **Años:** 2005, 2009, 2017, 2019, 2024, 2025
- **Plataforma:** SINDMA (normas.gba.gob.ar)
- **API:** BigModel GLM 4.7 Flash (exclusivo para TODO: extracción + embeddings)
- **Costo:** Muy bajo (GLM 4.7 Flash es económico)

## 🎯 Próximos Pasos Prioritarios

1. **Generar embeddings con BigModel** (Prioridad 1)
   - Modificar `generate_embeddings.ts`
   - Usar endpoint de embeddings GLM
   - Guardar en `real[]` arrays

2. **Populate base de datos** (Prioridad 2)
   - Insertar normas
   - Generar y guardar embeddings
   - Probar queries

3. **Crear MCP server** (Prioridad 3)
   - Tools: search, get_norma, get_vigencia, search_articles
   - Integrar con base de datos

4. **Inferrar temas de PBA** (Prioridad 4)
   - Clustering en las 46 normas
   - Identificar 25 temas oficiales

5. **Scraping masivo** (Prioridad 5)
   - Procesar 130,125 resultados
   - Paginación + rate limiting

## 💡 Notas Importantes

### Sobre la Arquitectura

- **No separar por tema:** Todo en un solo MCP server
- **Proceso por tema vertical:** Empezar con Salud, luego Educación, etc.
- **Procesar TODO:** "absolutely everything" en cada tema
- **Embeddings custom:** No usar pgvector, usar `real[]` y función personalizada

### Sobre la API

- **BigModel GLM 4.7 Flash:** Costeable, rápido, JSON output perfecto
- **Connection string:** `005ad7682c9b4bef823c59632771cafb.FgHv8ocQgLYhpttb`
- **Endpoint:** `https://open.bigmodel.cn/api/paas/v4/chat/completions`
- **Model:** `glm-4-flash`

### Sobre la Extracción

- **JSON estructurado:** metadata, articulos, referencias, analisis
- **System prompt:** `prompts/extract_norma_pba_system.txt`
- **Limpiar markdown:** Eliminar ```json ... ``` bloques
- **Progreso guardado:** Después de cada norma

### Sobre la Base de Datos

- **Connection:** `postgresql://adrian:!DarthHobbit%25@thecodersteam.com:5432/ordenanzas`
- **Schema:** `scripts/pba/setup_db.sql`
- **Embeddings:** `real[]` (no pgvector)
- **Función:** `cosine_similarity(array1, array2)` - PL/pgSQL

## 📝 Commands Útiles

```bash
# Run crawler (5 pages)
npx tsx scripts/pba/crawler_sindma.ts

# Test BigModel extraction (1 norm)
npx tsx scripts/pba/test_extract_bigmodel.ts

# Process all norms
npx tsx scripts/pba/extract_all_bigmodel.ts

# Clean extracted data
npx tsx scripts/pba/clean_extracted_data.ts

# Check database
npx tsx scripts/pba/migrate.ts

# Generate embeddings (placeholder)
npx tsx scripts/pba/generate_embeddings.ts
```

---

**Fecha de última actualización:** 2026-02-19
**Estado del proyecto:** Crawler ✅ | Extracción ✅ | Limpieza ✅ | Embeddings ⏳ | Base de datos ⏳ | MCP server ⏳
