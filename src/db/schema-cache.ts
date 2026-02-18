import {
  pgTable,
  serial,
  uuid,
  timestamp,
  text,
  pgEnum,
} from "drizzle-orm/pg-core";
import { ordenanzas } from "./schema.js";

// =============================================================================
// ENUMS
// =============================================================================

export const estiloResumenEnum = pgEnum("estilo_resumen", [
  "formal",
  "simple",
  "bullet-points",
]);

// =============================================================================
// TABLA: embeddings_cache
// =============================================================================

/**
 * Cache de embeddings vectoriales para búsqueda semántica.
 *
 * NOTA: Almacenamos embeddings como array JSON (TEXT) porque pgvector
 * puede no estar disponible en el servidor PostgreSQL.
 * Formato: "[0.123, -0.456, ...]"
 *
 * Algoritmo:
 * 1. Verificar si embedding existe para ordenanza_id
 * 2. Si no existe, generar con OpenAI text-embedding-3-small
 * 3. Buscar similares calculando cosine similarity en memoria (JavaScript)
 */
export const embeddingsCache = pgTable(
  "embeddings_cache",
  {
    id: serial("id").primaryKey(),
    ordenanzaId: uuid("ordenanza_id")
      .notNull()
      .references(() => ordenanzas.id, { onDelete: "cascade" }),
    modelo: text("modelo").notNull().default("text-embedding-3-small"),
    vector: text("vector").notNull(), // JSON array format "[0.123,...]"
    dimensions: text("dimensions").notNull().default("1536"),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [
    {
      name: "uq_embeddings_ordenanza_modelo",
      columns: [table.ordenanzaId, table.modelo],
    },
  ]
);

// =============================================================================
// TABLA: resumenes_cache
// =============================================================================

/**
 * Cache de resúmenes generados por LLM.
 *
 * Algoritmo:
 * 1. Verificar si resumen existe para texto+estilo+longitud
 * 2. Si no existe, generar con Groq Llama 3.3 70B
 * 3. Guardar en cache para reuso
 */
export const resumenesCache = pgTable(
  "resumenes_cache",
  {
    id: serial("id").primaryKey(),
    ordenanzaId: uuid("ordenanza_id").references(() => ordenanzas.id, {
      onDelete: "set null",
    }),
    textoOriginal: text("texto_original").notNull(),
    textoResumen: text("texto_resumen").notNull(),
    longitudPalabras: text("longitud_palabras").notNull(),
    estilo: estiloResumenEnum("estilo").notNull(),
    modelo: text("modelo").notNull().default("llama-3.3-70b"),
    tokensUsados: text("tokens_usados"),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [
    {
      name: "uq_resumen_params",
      columns: [
        table.ordenanzaId,
        table.textoOriginal,
        table.estilo,
        table.longitudPalabras,
      ],
    },
  ]
);

// =============================================================================
// INDICES
// =============================================================================

/**
 * NOTA: Para búsqueda eficiente de similitud vectorial cuando pgvector
 * esté disponible, crear índice IVFFlat o HNSW:
 *
 * CREATE INDEX idx_embeddings_vector
 *   ON embeddings_cache USING ivfflat (vector vector_cosine_ops)
 *   WITH (lists = 100);
 *
 * Mientras tanto, la búsqueda de similares se hace en memoria (JavaScript)
 * calculando cosine similarity entre vectores almacenados como TEXT.
 */
