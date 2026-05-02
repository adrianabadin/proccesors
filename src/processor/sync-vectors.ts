import { Pool } from "pg";
import "dotenv/config";
import { createTable } from "../mcp-server/vector-store.js";

const MODEL = "text-embedding-3-large";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: false,
});

function parseVector(str: string): number[] {
  return JSON.parse(str);
}

async function main() {
  console.log("=== Sync PostgreSQL embeddings → LanceDB ===\n");

  const t0 = Date.now();

  // 1. Fetch from PostgreSQL
  console.log("[1/3] Fetching embeddings from PostgreSQL...");
  const tFetch = Date.now();
  const { rows } = await pool.query(
    `SELECT ec.ordenanza_id, ec.vector, o.numero, o.anio, o.titulo, o.resumen, o.estado
     FROM embeddings_cache ec
     JOIN ordenanzas o ON o.id = ec.ordenanza_id
     WHERE ec.modelo = $1`,
    [MODEL]
  );
  console.log(`    Fetched ${rows.length} rows in ${Date.now() - tFetch}ms\n`);

  // 2. Parse vectors
  console.log(`[2/3] Parsing ${rows.length} vectors...`);
  const tParse = Date.now();
  const embeddings = rows.map((r, i) => {
    if (i % 500 === 0 && i > 0) console.log(`    ${i}/${rows.length}...`);
    return {
      ordenanza_id: r.ordenanza_id,
      vector: parseVector(r.vector),
      numero: r.numero,
      anio: r.anio,
      titulo: r.titulo,
      resumen: r.resumen || "",
      estado: r.estado,
    };
  });
  console.log(`    Parsed in ${Date.now() - tParse}ms\n`);

  // 3. Write to LanceDB
  console.log(`[3/3] Writing ${embeddings.length} vectors to LanceDB...`);
  const tWrite = Date.now();
  await createTable(embeddings);
  console.log(`    Written in ${Date.now() - tWrite}ms\n`);

  const total = Date.now() - t0;
  console.log(`=== Done in ${total}ms (${(total / 1000).toFixed(1)}s) ===`);
  console.log(`LanceDB stored at: .lancedb/`);

  await pool.end();
  process.exit(0);
}

main().catch(e => {
  console.error("Sync failed:", e);
  pool.end().then(() => process.exit(1));
});
