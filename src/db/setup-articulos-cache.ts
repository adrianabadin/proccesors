import { Pool } from "pg";
import "dotenv/config";

const pool = new Pool({ connectionString: process.env.DATABASE_URL, ssl: false });

async function main() {
  console.log("Creando tabla articulos_embeddings_cache...");

  await pool.query(`
    CREATE TABLE IF NOT EXISTS articulos_embeddings_cache (
      id SERIAL PRIMARY KEY,
      articulo_id UUID NOT NULL REFERENCES articulos(id) ON DELETE CASCADE,
      modelo TEXT NOT NULL,
      vector TEXT NOT NULL,
      dimensions TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      CONSTRAINT uq_articulos_embeddings_modelo UNIQUE (articulo_id, modelo)
    )
  `);

  await pool.query(`
    CREATE INDEX IF NOT EXISTS idx_articulos_embeddings
    ON articulos_embeddings_cache (articulo_id)
  `);

  console.log("Tabla creada correctamente.");
  await pool.end();
}

main().catch(e => { console.error(e); pool.end().then(() => process.exit(1)); });
