import OpenAI from "openai";
import "dotenv/config";
import { logger } from "./logger.js";
import { query, execute } from "./db.js";
import { parseVector, formatVector, cosineSimilarity } from "./utils.js";

const apiKey = process.env.OPENAI_API_KEY;

if (!apiKey) {
  logger.warn(
    "OPENAI_API_KEY no está configurada. Las herramientas de embeddings no funcionarán."
  );
}

/**
 * Cliente OpenAI para generar embeddings
 * 
 * Modelo por defecto: text-embedding-3-small
 * Dimensiones: 1536
 * Costo: ~$0.02 por 1M tokens (muy económico)
 */
const openai = apiKey
  ? new OpenAI({
      apiKey,
      maxRetries: 2,
      timeout: 30_000, // 30 segundos
    })
  : null;

const EMBEDDING_MODEL = "text-embedding-3-small";
const EMBEDDING_DIMENSIONS = 1536;

/**
 * Genera embedding para un texto usando OpenAI API
 * 
 * @param text - Texto a procesar
 * @returns Array de números (1536 dimensiones)
 */
export async function generateEmbedding(
  text: string
): Promise<number[]> {
  if (!openai) {
    throw new Error(
      "OpenAI client no configurado. Set OPENAI_API_KEY en .env"
    );
  }

  logger.debug(
    { model: EMBEDDING_MODEL, textLength: text.length },
    "Generating embedding..."
  );

  try {
    const response = await openai.embeddings.create({
      model: EMBEDDING_MODEL,
      input: text,
    });

    const embedding = response.data[0].embedding;

    logger.debug(
      { dimensions: embedding.length, model: EMBEDDING_MODEL },
      "Embedding generated"
    );

    return embedding;
  } catch (error) {
    logger.error(
      { error: error instanceof Error ? error.message : String(error) },
      "Failed to generate embedding"
    );
    throw error;
  }
}

/**
 * Busca embedding en cache o genera uno nuevo
 * 
 * @param ordenanzaId - UUID de la ordenanza
 * @param textoCompleto - Texto completo de la ordenanza
 * @returns Embedding existente o nuevo generado
 */
export async function getOrCreateEmbedding(
  ordenanzaId: string,
  textoCompleto: string
): Promise<number[]> {
  const toolLog = logger.child({ tool: "embeddings" });

  // 1. Buscar en cache (filtered by model)
  const cached = await query(
    `SELECT vector FROM embeddings_cache WHERE ordenanza_id = $1 AND modelo = $2`,
    [ordenanzaId, EMBEDDING_MODEL]
  );

  if (cached.length > 0) {
    toolLog.debug({ ordenanzaId, model: EMBEDDING_MODEL }, "Embedding found in cache");
    return parseVector(cached[0].vector);
  }

  // 2. Generar nuevo embedding
  toolLog.info({ ordenanzaId, model: EMBEDDING_MODEL }, "Generating new embedding...");

  const embedding = await generateEmbedding(textoCompleto);

  // 3. Guardar en cache (with modelo)
  await execute(
    `
    INSERT INTO embeddings_cache (ordenanza_id, modelo, vector, dimensions)
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (ordenanza_id, modelo) DO UPDATE SET
      vector = EXCLUDED.vector,
      updated_at = NOW()
    `,
    [ordenanzaId, EMBEDDING_MODEL, formatVector(embedding), EMBEDDING_DIMENSIONS.toString()]
  );

  toolLog.info({ ordenanzaId, model: EMBEDDING_MODEL }, "Embedding cached");

  return embedding;
}

/**
 * Obtiene todos los embeddings en memoria para búsqueda de similitud
 * 
 * @returns Array de { id, vector } para calcular similitudes
 */
export async function getAllEmbeddingsForSimilarity(): Promise<
  Array<{ id: string; ordenanza_id: string; vector: string; numero: number; anio: number; titulo: string; resumen: string; categorias?: string }>
> {
  const toolLog = logger.child({ tool: "embeddings" });

  const rows = await query(
    `
    SELECT ec.id, ec.ordenanza_id, ec.vector, o.numero, o.anio, o.titulo, o.resumen
    FROM embeddings_cache ec
    JOIN ordenanzas o ON o.id = ec.ordenanza_id
    WHERE ec.modelo = $1
    ORDER BY ec.created_at DESC
    `,
    [EMBEDDING_MODEL]
  );

  toolLog.debug({ count: rows.length, model: EMBEDDING_MODEL }, "Loaded embeddings for similarity");

  return rows;
}

/**
 * Obtiene embedding específico de una ordenanza
 */
export async function getEmbedding(
  ordenanzaId: string
): Promise<number[] | null> {
  const cached = await query(
    `SELECT vector FROM embeddings_cache WHERE ordenanza_id = $1 AND modelo = $2`,
    [ordenanzaId, EMBEDDING_MODEL]
  );

  if (cached.length === 0) {
    return null;
  }

  return parseVector(cached[0].vector);
}

// Re-export from utils for backward compatibility
export { parseVector, formatVector, cosineSimilarity } from "./utils.js";

// Keep aliases for backward compat
export const calculateCosineSimilarity = cosineSimilarity;
export const parseEmbeddingVector = parseVector;
export const formatEmbeddingVector = formatVector;

/**
 * Genera embedding para un texto usando un modelo específico
 */
export async function generateEmbeddingForModel(
  text: string,
  model: "text-embedding-3-small" | "text-embedding-3-large"
): Promise<number[]> {
  if (!openai) throw new Error("OpenAI client no configurado");
  const response = await openai.embeddings.create({ model, input: text });
  return response.data[0].embedding;
}

/**
 * Obtiene todos los embeddings para un modelo específico
 */
export async function getAllEmbeddingsByModel(
  model: "text-embedding-3-small" | "text-embedding-3-large"
): Promise<Array<{ ordenanza_id: string; vector: string; numero: number; anio: number; titulo: string; resumen: string; estado: string; categorias: string | null }>> {
  const rows = await query(
    `SELECT ec.ordenanza_id, ec.vector, o.numero, o.anio, o.titulo, o.resumen, o.estado,
       COALESCE(jsonb_agg(jsonb_build_object('nombre', c.nombre, 'slug', c.slug, 'relevancia', oc.relevancia)), '[]'::jsonb)::text as categorias
     FROM embeddings_cache ec
     JOIN ordenanzas o ON o.id = ec.ordenanza_id
     LEFT JOIN ordenanza_categorias oc ON o.id = oc.ordenanza_id
     LEFT JOIN categorias c ON oc.categoria_id = c.id
     WHERE ec.modelo = $1
     GROUP BY ec.ordenanza_id, ec.vector, o.numero, o.anio, o.titulo, o.resumen, o.estado`,
    [model]
  );
  return rows;
}

/**
 * Valida si el cliente está configurado
 */
export function isConfigured(): boolean {
  return openai !== null;
}
