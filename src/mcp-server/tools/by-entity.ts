import { query } from "../db.js";
import * as z from "zod/v4";
import {
  SearchByEntityInputSchema,
  OrdenanzaSummarySchema,
  EntidadSchema,
} from "../types.js";
import { toolLogger, truncate } from "../utils.js";

// =============================================================================
// TOOL 1: search_by_entity
// =============================================================================

export const searchByEntityTool = {
  name: "search_by_entity",
  title: "Buscar por Entidad",
  description:
    "Busca ordenanzas que mencionan una entidad específica (persona, empresa, organismo, etc.). Filtra por nombre (parcial match) y opcionalmente por tipo de entidad.",
  inputSchema: SearchByEntityInputSchema,
};

export async function searchByEntityHandler(
  args: z.infer<typeof SearchByEntityInputSchema>,
  ctx: any
): Promise<any> {
  const log = toolLogger("search_by_entity");

  try {
    log.info("Searching...", { nombre: args.nombre, tipo: args.tipo });

    let whereClause = "e.nombre ILIKE $1";
    const params: any[] = [`%${args.nombre}%`];

    if (args.tipo) {
      whereClause += " AND e.tipo = $2";
      params.push(args.tipo);
    }

    params.push(args.limit);
    const rows = await query(`
      SELECT DISTINCT
        o.id, o.numero, o.anio, o.titulo, o.resumen, o.estado,
        e.nombre as entidad_nombre, e.tipo as entidad_tipo, oe.rol as entidad_rol
      FROM entidades e
      JOIN ordenanza_entidades oe ON oe.entidad_id = e.id
      JOIN ordenanzas o ON o.id = oe.ordenanza_id
      WHERE ${whereClause}
      ORDER BY o.anio DESC, o.numero DESC
      LIMIT $${params.length}
    `, params);

    const formatted = rows.map((row: any) => ({
      id: row.id,
      numero: row.numero,
      anio: row.anio,
      titulo: row.titulo,
      resumen: row.resumen,
      estado: row.estado,
      categorias: [],
    }));

    log.info("Search completed", { count: formatted.length });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            results: formatted,
            total: formatted.length,
            entity: args.nombre,
            entity_type: args.tipo,
          }),
        },
      ],
    };
  } catch (error) {
    log.error("Search failed", {
      error: error instanceof Error ? error.message : String(error)
    });
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: `Error al buscar por entidad: ${
              error instanceof Error ? error.message : String(error)
            }`,
          }),
        },
      ],
      isError: true,
    };
  }
}
