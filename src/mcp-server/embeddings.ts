import OpenAI from "openai";
import "dotenv/config";
import { logger } from "./logger.js";
import { query, execute } from "./db.js";
import { parseVector, formatVector } from "./utils.js";

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

  // 1. Buscar en cache
  const cached = await query(
    `SELECT vector FROM embeddings_cache WHERE ordenanza_id = $1`,
    [ordenanzaId]
  );

  if (cached.length > 0) {
    toolLog.debug({ ordenanzaId }, "Embedding found in cache");
    return parseVector(cached[0].vector);
  }

  // 2. Generar nuevo embedding
  toolLog.info({ ordenanzaId }, "Generating new embedding...");

  const embedding = await generateEmbedding(textoCompleto);

  // 3. Guardar en cache
  await execute(
    `
    INSERT INTO embeddings_cache (ordenanza_id, vector, dimensions)
    VALUES ($1, $2, $3)
    ON CONFLICT (ordenanza_id, modelo) DO UPDATE SET
      vector = EXCLUDED.vector,
      updated_at = NOW()
    `,
    [ordenanzaId, formatVector(embedding), EMBEDDING_DIMENSIONS.toString()]
  );

  toolLog.info({ ordenanzaId }, "Embedding cached");

  return embedding;
}

/**
 * Obtiene todos los embeddings en memoria para búsqueda de similitud
 * 
 * @returns Array de { id, vector } para calcular similitudes
 */
export async function getAllEmbeddingsForSimilarity(): Promise<
  Array<{ id: string; ordenanza_id: string; vector: string }>
> {
  const toolLog = logger.child({ tool: "embeddings" });

  const rows = await query(
    `
    SELECT ec.id, ec.ordenanza_id, ec.vector, o.numero, o.anio, o.titulo, o.resumen
    FROM embeddings_cache ec
    JOIN ordenanzas o ON o.id = ec.ordenanza_id
    ORDER BY ec.created_at DESC
    `
  );

  toolLog.debug({ count: rows.length }, "Loaded embeddings for similarity");

  return rows.map((row) => ({
    id: row.id,
    ordenanza_id: row.ordenanza_id,
    vector: row.vector,
  }));
}

/**
 * Obtiene embedding específico de una ordenanza
 */
export async function getEmbedding(
  ordenanzaId: string
): Promise<number[] | null> {
  const cached = await query(
    `SELECT vector FROM embeddings_cache WHERE ordenanza_id = $1`,
    [ordenanzaId]
  );

  if (cached.length === 0) {
    return null;
  }

  return parseVector(cached[0].vector);
}

/**
 * Calcula cosine similarity entre dos vectores
 * Utilizado para búsqueda semántica cuando pgvector no está disponible
 */
export function calculateCosineSimilarity(vecA: number[], vecB: number[]): number {
  if (vecA.length !== vecB.length) {
    throw new Error("Vectors must have the same length");
  }

  let dotProduct = 0;
  let normA = 0;
  let normB = 0;

  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    normA += vecA[i] * vecA[i];
    normB += vecB[i] * vecB[i];
  }

  const similarity = dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
  return similarity;
}

/**
 * Parsea un vector almacenado como JSON string a array de números
 */
export function parseEmbeddingVector(vectorStr: string): number[] {
  try {
    const parsed = JSON.parse(vectorStr);
    if (!Array.isArray(parsed)) {
      throw new Error("Vector is not an array");
    }
    return parsed;
  } catch (error) {
    logger.error(
      { vectorStr, error },
      "Failed to parse vector from string"
    );
    throw new Error(`Invalid vector format: ${vectorStr}`);
  }
}

/**
 * Formatea un array de números a JSON string
 */
export function formatEmbeddingVector(vector: number[]): string {
  return JSON.stringify(vector);
}

/**
 * Calcula cosine similarity entre dos vectores
 * Utilizado para búsqueda semántica cuando pgvector no está disponible
 */
export function cosineSimilarity(vecA: number[], vecB: number[]): number {
  if (vecA.length !== vecB.length) {
    throw new Error("Vectors must have the same length");
  }

  let dotProduct = 0;
  let normA = 0;
  let normB = 0;

  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    normA += vecA[i] * vecA[i];
    normB += vecB[i] * vecB[i];
  }

  const similarity = dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
  return similarity;
}

/**
 * Parsea un vector almacenado como JSON string a array de números
 */
export function parseVector(vectorStr: string): number[] {
  try {
    const parsed = JSON.parse(vectorStr);
    if (!Array.isArray(parsed)) {
      throw new Error("Vector is not an array");
    }
    return parsed;
  } catch (error) {
    logger.error(
      { vectorStr, error },
      "Failed to parse vector from string"
    );
    throw new Error(`Invalid vector format: ${vectorStr}`);
  }
}

/**
 * Formatea un array de números a JSON string
 */
export function formatVector(vector: number[]): string {
  return JSON.stringify(vector);
}

/**
 * Valida si el cliente está configurado
 */
export function isConfigured(): boolean {
  return openai !== null;
}
