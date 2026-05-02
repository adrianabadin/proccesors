import { Pool } from "pg";
import OpenAI from "openai";
import pLimit from "p-limit";
import "dotenv/config";
import { createArticuloTable, ArticuloEmbedding } from "../mcp-server/vector-store.js";

const MODEL = "text-embedding-3-large";

const CONFIG = {
  MODEL,
  CONCURRENCY: parseInt(process.env.EMBEDDING_CONCURRENCY ?? "3", 10),
  BATCH_SIZE: parseInt(process.env.EMBEDDING_BATCH_SIZE ?? "100", 10),
  MIN_TEXT_LENGTH: 50,
  API_MAX_RETRIES: 5,
  DELAY_MS: 100,
} as const;

const pool = new Pool({ connectionString: process.env.DATABASE_URL, ssl: false });
const openai = new OpenAI({ maxRetries: CONFIG.API_MAX_RETRIES });

interface RawArticulo {
  id: string;
  ordenanza_id: string;
  numero_articulo: string;
  texto: string;
  numero: number;
  anio: number;
  titulo: string;
  estado: string;
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  const t0 = Date.now();
  console.log("=== Generar embeddings de artículos ===\n");
  console.log(`Modelo: ${MODEL}, Concurrencia: ${CONFIG.CONCURRENCY}, Batch: ${CONFIG.BATCH_SIZE}\n`);

  // 1. Get unembedded articles
  console.log("[1] Buscando artículos sin embedding...");
  const { rows }: { rows: RawArticulo[] } = await pool.query(`
    SELECT a.id, a.ordenanza_id, a.numero_articulo, a.texto,
           o.numero, o.anio, o.titulo, o.estado
    FROM articulos a
    JOIN ordenanzas o ON o.id = a.ordenanza_id
    WHERE a.id NOT IN (
      SELECT articulo_id FROM articulos_embeddings_cache WHERE modelo = $1
    )
    AND a.texto IS NOT NULL
    AND length(trim(a.texto)) >= $2
    ORDER BY o.anio DESC, o.numero DESC, a.orden ASC
  `, [MODEL, CONFIG.MIN_TEXT_LENGTH]);

  console.log(`    ${rows.length} artículos pendientes\n`);
  if (rows.length === 0) {
    console.log("Nada que procesar.");
    await pool.end();
    process.exit(0);
  }

  // 2. Process in batches
  const limit = pLimit(CONFIG.CONCURRENCY);
  let processed = 0;
  let skipped = 0;
  let errors = 0;
  const allEmbeddings: ArticuloEmbedding[] = [];

  const totalBatches = Math.ceil(rows.length / CONFIG.BATCH_SIZE);

  for (let bi = 0; bi < totalBatches; bi++) {
    const batch = rows.slice(bi * CONFIG.BATCH_SIZE, (bi + 1) * CONFIG.BATCH_SIZE);

    const batchPromises = batch.map(art => limit(async () => {
      try {
        const texto = art.texto.trim();
        if (texto.length < CONFIG.MIN_TEXT_LENGTH) {
          skipped++;
          return null;
        }

        const response = await openai.embeddings.create({
          model: MODEL,
          input: texto,
        });

        const vector = response.data[0].embedding;

        // Insert into PostgreSQL
        await pool.query(
          `INSERT INTO articulos_embeddings_cache (articulo_id, modelo, vector, dimensions)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (articulo_id, modelo) DO UPDATE SET
             vector = EXCLUDED.vector, updated_at = NOW()`,
          [art.id, MODEL, JSON.stringify(vector), String(vector.length)]
        );

        processed++;
        return {
          articulo_id: art.id,
          ordenanza_id: art.ordenanza_id,
          numero_articulo: art.numero_articulo,
          texto: art.texto,
          numero: art.numero,
          anio: art.anio,
          titulo: art.titulo,
          estado: art.estado,
          vector,
        } as ArticuloEmbedding;
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        if (msg.includes("429") || msg.includes("rate")) {
          console.log(`    [rate-limit] esperando 10s...`);
          await sleep(10_000);
        }
        errors++;
        return null;
      }
    }));

    const results = await Promise.all(batchPromises);
    for (const r of results) {
      if (r) allEmbeddings.push(r);
    }

    const pct = Math.round((processed / rows.length) * 100);
    console.log(`    Procesado ${processed}/${rows.length} (${pct}%) — errores: ${errors}, skip: ${skipped}`);
  }

  // 3. Sync to LanceDB
  console.log(`\n[2] Sincronizando ${allEmbeddings.length} embeddings a LanceDB...`);
  if (allEmbeddings.length > 0) {
    await createArticuloTable(allEmbeddings);
  }

  // 4. Summary
  const elapsed = ((Date.now() - t0) / 1000).toFixed(0);
  console.log(`\n=== Completado en ${elapsed}s ===`);
  console.log(`Embeddings: ${processed}, Errores: ${errors}, Skipped: ${skipped}`);
  console.log(`LanceDB: ${allEmbeddings.length} vectores en '.lancedb/'`);

  await pool.end();
  process.exit(0);
}

main().catch(e => {
  console.error("Fatal:", e);
  pool.end().then(() => process.exit(1));
});
