import pg from "pg";
import "dotenv/config";

const pool = new pg.Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: false,
});

async function main() {
  const { rows } = await pool.query(
    "SELECT id FROM categorias WHERE slug = 'sin-categoria'"
  );

  if (rows.length > 0) {
    console.log("sin-categoria already exists with id:", rows[0].id);
    await pool.end();
    return;
  }

  const result = await pool.query(`
    INSERT INTO categorias (nombre, slug, descripcion)
    VALUES ('Sin Categoría', 'sin-categoria', 'Ordenanzas pendientes de categorización')
    RETURNING id
  `);
  console.log("Added sin-categoria with id:", result.rows[0].id);
  await pool.end();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
