import { drizzle } from "drizzle-orm/node-postgres";
import pg from "pg";
import * as schema from "./schema.js";
import "dotenv/config";

const pool = new pg.Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: false,
});

export const db = drizzle(pool, { schema });
export { schema };
export { pool };
