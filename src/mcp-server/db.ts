import { Pool } from "pg";
import "dotenv/config";
import { logger } from "./logger.js";

const isVerbose = process.env.VERBOSE === "true" || process.env.NODE_ENV === "development";

/**
 * Connection pool a PostgreSQL
 * 
 * Configuración optimizada para MCP server:
 * - max: 20 conexiones concurrentes
 * - idleTimeoutMillis: 30s de inactividad antes de cerrar
 * - connectionTimeoutMillis: 5s para fallar rápido si hay problemas
 */
const dbUrl = process.env.DATABASE_URL;
if (dbUrl) {
  const maskedUrl = dbUrl.replace(/:([^:@]+)@/, ':****@');
  logger.info(`Conectando a base de datos: ${maskedUrl}`);
} else {
  logger.error("DATABASE_URL no definida");
}

const pool = new Pool({
  connectionString: dbUrl,
  ssl: false,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

/**
 * Wrapper para query con logging verbose
 */
export async function query<T = any>(
  sql: string,
  params?: any[],
): Promise<T[]> {
  const startTime = Date.now();

  if (isVerbose) {
    logger.debug(
      { sql, params },
      "Executing query..."
    );
  }

  try {
    const result = await pool.query(sql, params);
    const elapsed = Date.now() - startTime;

    if (isVerbose) {
      logger.debug(
        { rows: result.rowCount, elapsed: `${elapsed}ms` },
        "Query completed"
      );
    }

    return result.rows as T[];
  } catch (error) {
    const elapsed = Date.now() - startTime;
    logger.error(
      {
        sql,
        params,
        error: error instanceof Error ? error.message : String(error),
        elapsed: `${elapsed}ms`,
      },
      "Query failed"
    );
    throw error;
  }
}

/**
 * Wrapper para ejecutar una sola query (INSERT, UPDATE, DELETE)
 */
export async function execute(
  sql: string,
  params?: any[],
): Promise<import("pg").QueryResult> {
  const startTime = Date.now();

  if (isVerbose) {
    logger.debug(
      { sql, params },
      "Executing statement..."
    );
  }

  try {
    const result = await pool.query(sql, params);
    const elapsed = Date.now() - startTime;

    if (isVerbose) {
      logger.debug(
        { rows: result.rowCount, elapsed: `${elapsed}ms` },
        "Statement completed"
      );
    }

    return result;
  } catch (error) {
    const elapsed = Date.now() - startTime;
    logger.error(
      {
        sql,
        params,
        error: error instanceof Error ? error.message : String(error),
        elapsed: `${elapsed}ms`,
      },
      "Statement failed"
    );
    throw error;
  }
}

/**
 * Cerrar el pool cuando el server se detiene
 */
export async function closePool(): Promise<void> {
  logger.info("Closing database connection pool...");
  await pool.end();
  logger.info("Connection pool closed");
}

/**
 * Export del pool para uso directo si es necesario
 */
export { pool };

/**
 * Health check
 */
export async function healthCheck(): Promise<boolean> {
  try {
    await pool.query("SELECT 1");
    return true;
  } catch (error) {
    logger.error(
      { error: error instanceof Error ? error.message : String(error) },
      "Database health check failed"
    );
    return false;
  }
}
