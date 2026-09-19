import { Pool } from "pg";
import "dotenv/config";
import { createArticuloTable, ArticuloEmbedding } from "../mcp-server/vector-store.js";

const pool = new Pool({ connectionString: process.env.DATABASE_URL, ssl: false });

const { rows } = await pool.query(`
  SELECT aec.articulo_id, aec.vector,
         a.ordenanza_id, a.numero_articulo, a.texto,
         o.numero, o.anio, o.titulo, o.estado
  FROM articulos_embeddings_cache aec
  JOIN articulos a ON a.id = aec.articulo_id
  JOIN ordenanzas o ON o.id = a.ordenanza_id
  WHERE aec.modelo = 'text-embedding-3-large'
`);

console.log(`Syncing ${rows.length} article embeddings to LanceDB...`);

const embeddings: ArticuloEmbedding[] = rows.map(r => ({
  articulo_id: r.articulo_id,
  ordenanza_id: r.ordenanza_id,
  numero_articulo: r.numero_articulo,
  texto: r.texto,
  numero: r.numero,
  anio: r.anio,
  titulo: r.titulo,
  estado: r.estado,
  vector: JSON.parse(r.vector),
}));

const t0 = Date.now();
await createArticuloTable(embeddings);
console.log(`Done in ${Date.now() - t0}ms`);

await pool.end();
process.exit(0);
