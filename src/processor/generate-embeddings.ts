/**
 * Batch embedding generation script for text-embedding-3-large.
 *
 * Generates embeddings for all ordinances that don't already have one
 * in embeddings_cache for the "text-embedding-3-large" model.
 *
 * Features:
 * - Resumable: skips already-processed ordinances (DB-as-checkpoint)
 * - Token-aware text selection: full text if short, resumen if long
 * - Rate-limited with concurrency control via p-limit
 * - Progress reporting
 *
 * Usage: npx tsx src/processor/generate-embeddings.ts
 */

import OpenAI from "openai";
import "dotenv/config";
import pg from "pg";
import pLimit from "p-limit";
import { encodingForModel } from "js-tiktoken";

// ─── Configuration ──────────────────────────────────────────────────────

const CONFIG = {
  MODEL: "text-embedding-3-large" as const,
  CONCURRENCY: parseInt(process.env.EMBEDDING_CONCURRENCY ?? "3", 10),
  BATCH_SIZE: parseInt(process.env.EMBEDDING_BATCH_SIZE ?? "100", 10),
  TOKEN_THRESHOLD: 6000,
  MIN_TEXT_LENGTH: 100,
  API_MAX_RETRIES: 5,
  API_TIMEOUT: 60_000,
  DELAY_MS: 200,
};

// ─── Clients ────────────────────────────────────────────────────────────

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  maxRetries: CONFIG.API_MAX_RETRIES,
  timeout: CONFIG.API_TIMEOUT,
});

const pool = new pg.Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: false,
});

const enc = encodingForModel("text-embedding-3-large");

// ─── Types ──────────────────────────────────────────────────────────────

interface OrdenanzaRow {
  id: string;
  texto_completo: string | null;
  resumen: string | null;
  palabras_clave: string[] | null;
}

// ─── Utilities ──────────────────────────────────────────────────────────

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Selects the best text to embed based on length and token count.
 * - Prefer full text if long enough and within token limit
 * - Fall back to resumen if full text is too long or too short
 * - Return null if both are insufficient
 */
function selectText(ordenanza: OrdenanzaRow): string | null {
  const fullText = ordenanza.texto_completo?.trim() ?? "";
  const resumen = ordenanza.resumen?.trim() ?? "";

  // Prefer full text if long enough and within token limit
  if (fullText.length >= CONFIG.MIN_TEXT_LENGTH) {
    const tokens = enc.encode(fullText).length;
    if (tokens <= CONFIG.TOKEN_THRESHOLD) return fullText;
  }

  // Fall back to resumen
  if (resumen.length >= CONFIG.MIN_TEXT_LENGTH) return resumen;

  // Both too short — skip
  return null;
}

/**
 * Generates an embedding using the OpenAI API with retry on rate limits.
 */
async function generateEmbeddingWithRetry(
  text: string
): Promise<number[]> {
  try {
    const response = await openai.embeddings.create({
      model: CONFIG.MODEL,
      input: text,
    });
    return response.data[0].embedding;
  } catch (error: any) {
    // Handle 429 rate limit
    if (error?.status === 429) {
      console.log("  Rate limited, waiting 10s...");
      await sleep(10_000);
      const response = await openai.embeddings.create({
        model: CONFIG.MODEL,
        input: text,
      });
      return response.data[0].embedding;
    }
    throw error;
  }
}

/**
 * Inserts an embedding into the cache with upsert semantics.
 */
async function cacheEmbedding(
  ordenanzaId: string,
  embedding: number[]
): Promise<void> {
  const vectorStr = JSON.stringify(embedding);
  await pool.query(
    `INSERT INTO embeddings_cache (ordenanza_id, modelo, vector, dimensions)
     VALUES ($1, 'text-embedding-3-large', $2, $3)
     ON CONFLICT (ordenanza_id, modelo) DO UPDATE SET
       vector = EXCLUDED.vector, updated_at = NOW()`,
    [ordenanzaId, vectorStr, "3072"]
  );
}

// ─── Main ───────────────────────────────────────────────────────────────

async function main() {
  console.log("=== Batch Embedding Generator (text-embedding-3-large) ===\n");
  console.log("Configuration:");
  console.log(`  Model:            ${CONFIG.MODEL}`);
  console.log(`  Concurrency:      ${CONFIG.CONCURRENCY}`);
  console.log(`  Batch size:       ${CONFIG.BATCH_SIZE}`);
  console.log(`  Token threshold:  ${CONFIG.TOKEN_THRESHOLD}`);
  console.log(`  Min text length:  ${CONFIG.MIN_TEXT_LENGTH}`);
  console.log(`  API retries:      ${CONFIG.API_MAX_RETRIES}`);
  console.log(`  API timeout:      ${CONFIG.API_TIMEOUT}ms`);
  console.log(`  Delay:            ${CONFIG.DELAY_MS}ms\n`);

  const startTime = Date.now();

  // 1. Query unembedded ordinances
  const result = await pool.query<OrdenanzaRow>(
    `SELECT o.id, o.texto_completo, o.resumen, o.palabras_clave
     FROM ordenanzas o
     WHERE o.id NOT IN (
       SELECT ordenanza_id FROM embeddings_cache WHERE modelo = 'text-embedding-3-large'
     )
     AND o.texto_completo IS NOT NULL
     ORDER BY o.anio DESC, o.numero DESC`
  );

  const ordinances = result.rows;
  console.log(`Found ${ordinances.length} ordinances to embed\n`);

  if (ordinances.length === 0) {
    console.log("Nothing to do. All ordinances already have embeddings.");
    await pool.end();
    process.exit(0);
  }

  // 2. Process with concurrency control
  const limiter = pLimit(CONFIG.CONCURRENCY);
  let embedded = 0;
  let skipped = 0;
  let errors = 0;

  const tasks = ordinances.map((ord: OrdenanzaRow) =>
    limiter(async () => {
      const text = selectText(ord);
      if (!text) {
        skipped++;
        console.log(`  Skipped ${ord.id} (text too short)`);
        return;
      }

      try {
        const embedding = await generateEmbeddingWithRetry(text);
        await cacheEmbedding(ord.id, embedding);
        embedded++;

        const total = embedded + skipped + errors;
        const pct = ((total / ordinances.length) * 100).toFixed(1);
        console.log(
          `  Processed ${total}/${ordinances.length} (${pct}%) - embedded: ${embedded}, skipped: ${skipped}, errors: ${errors}`
        );
      } catch (error: any) {
        errors++;
        console.error(
          `  ERROR for ${ord.id}: ${error?.message ?? String(error)}`
        );
      }

      // Small delay between requests to avoid rate limits
      await sleep(CONFIG.DELAY_MS);
    })
  );

  await Promise.all(tasks);

  // 3. Summary
  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log("\n=== Generation Complete ===");
  console.log(`Total:      ${ordinances.length}`);
  console.log(`Embedded:   ${embedded}`);
  console.log(`Skipped:    ${skipped}`);
  console.log(`Errors:     ${errors}`);
  console.log(`Elapsed:    ${elapsed}s`);

  await pool.end();
  process.exit(0);
}

// Execute
main().catch((error) => {
  console.error("\nFatal error:", error);
  process.exit(1);
});
