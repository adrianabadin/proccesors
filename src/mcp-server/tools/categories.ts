import { query } from "../db.js";
import * as z from "zod/v4";
import {
  ListCategoriesInputSchema,
  CategoriaSchema,
} from "../types.js";
import { toolLogger } from "../utils.js";

// =============================================================================
// TOOL 1: list_categories
// =============================================================================

export const listCategoriesTool = {
  name: "list_categories",
  title: "Listar Categorías",
  description:
    "Lista todas las categorías disponibles para clasificación de ordenanzas. Incluye nombre, slug, descripción y categoría padre.",
  inputSchema: ListCategoriesInputSchema,
};

export async function listCategoriesHandler(
  args: z.infer<typeof ListCategoriesInputSchema>,
  ctx: any
): Promise<any> {
  const log = toolLogger("list_categories");

  try {
    log.info("Fetching all categories...");

    const rows = await query(`
      SELECT c.id, c.nombre, c.slug, c.descripcion, c.parent_id, p.nombre as parent_nombre
      FROM categorias c
      LEFT JOIN categorias p ON c.parent_id = p.id
      ORDER BY c.nombre
    `);

    const formatted = rows.map((row: any) => ({
      id: row.id,
      nombre: row.nombre,
      slug: row.slug,
      descripcion: row.descripcion,
      parent_id: row.parent_id,
      parent_nombre: row.parent_nombre,
    }));

    log.info("Categories fetched", { count: formatted.length });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            categories: formatted,
            total: formatted.length,
          }),
        },
      ],
    };
  } catch (error) {
    log.error("Fetch failed", {
      error: error instanceof Error ? error.message : String(error)
    });
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: `Error al listar categorías: ${
              error instanceof Error ? error.message : String(error)
            }`,
          }),
        },
      ],
      isError: true,
    };
  }
}
