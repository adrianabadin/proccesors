import pg from "pg";
import "dotenv/config";

const pool = new pg.Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: false,
});

async function run(label: string, sql: string) {
  console.log(`  ${label}...`);
  await pool.query(sql);
}

async function main() {
  console.log("=== Setup de Cache Tables (embeddings, resumenes) ===\n");

  // Create embeddings_cache table
  console.log("[1/3] Creando tabla embeddings_cache...");
  await pool.query(`
    CREATE TABLE IF NOT EXISTS embeddings_cache (
      id SERIAL PRIMARY KEY,
      ordenanza_id UUID NOT NULL REFERENCES ordenanzas(id) ON DELETE CASCADE,
      modelo TEXT NOT NULL DEFAULT 'text-embedding-3-small',
      vector TEXT NOT NULL,
      dimensions TEXT NOT NULL DEFAULT '1536',
      created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
      CONSTRAINT uq_embeddings_ordenanza_modelo UNIQUE (ordenanza_id, modelo)
    );
  `);

  // Create resumenes_cache table
  console.log("[2/3] Creando tabla resumenes_cache...");

  // Check if enum exists first
  const enumExists = await pool.query(`
    SELECT EXISTS (
      SELECT 1 FROM pg_type WHERE typname = 'estilo_resumen'
    ) as exists
  `);

  if (!enumExists.rows[0].exists) {
    console.log("  Creando ENUM estilo_resumen...");
    await pool.query(`
      CREATE TYPE estilo_resumen AS ENUM ('formal', 'simple', 'bullet-points');
    `);
  }

  await pool.query(`
    CREATE TABLE IF NOT EXISTS resumenes_cache (
      id SERIAL PRIMARY KEY,
      ordenanza_id UUID REFERENCES ordenanzas(id) ON DELETE SET NULL,
      texto_original TEXT NOT NULL,
      texto_resumen TEXT NOT NULL,
      longitud_palabras TEXT NOT NULL,
      estilo estilo_resumen NOT NULL,
      modelo TEXT NOT NULL DEFAULT 'llama-3.3-70b',
      tokens_usados TEXT,
      created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
      CONSTRAINT uq_resumen_params UNIQUE (ordenanza_id, texto_original, estilo, longitud_palabras)
    );
  `);

  // Create indexes
  console.log("[3/3] Creando índices...");
  await pool.query(`
    CREATE INDEX IF NOT EXISTS idx_embeddings_ordenanza
      ON embeddings_cache (ordenanza_id);
  `);

  await pool.query(`
    CREATE INDEX IF NOT EXISTS idx_resumenes_ordenanza
      ON resumenes_cache (ordenanza_id);
  `);

  console.log("\n=== Setup completado ===");
  console.log("💡 NOTA: Embeddings se almacenan como TEXT (array JSON)");
  console.log("   La búsqueda semántica se hace en memoria calculando cosine similarity");
  console.log("   Para usar pgvector nativo, instala la extensión en el servidor");

  await pool.end();
}

main().catch((err) => {
  console.error("Setup fallido:", err);
  pool.end();
  process.exit(1);
});
