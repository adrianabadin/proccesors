import { query } from "../db.js";
import * as z from "zod/v4";
import {
  GetStatsInputSchema,
  StatsSchema,
} from "../types.js";
import { toolLogger } from "../utils.js";

// =============================================================================
// TOOL 1: get_stats
// =============================================================================

export const getStatsTool = {
  name: "get_stats",
  title: "Obtener Estadísticas",
  description:
    "Obtiene estadísticas generales del procesamiento de ordenanzas: total, procesadas, pendientes, top categorías, distribución por año.",
  inputSchema: GetStatsInputSchema,
};

export async function getStatsHandler(
  args: z.infer<typeof GetStatsInputSchema>,
  ctx: any
): Promise<any> {
  const log = toolLogger("get_stats");

  try {
    log.info("Calculating statistics...");

    // Totales generales
    const totalRows = await query("SELECT COUNT(*) as total FROM ordenanzas");
    const procesadasRows = await query(
      "SELECT COUNT(*) as procesadas FROM ordenanzas WHERE procesado_ia = true"
    );
    const total = parseInt(totalRows[0].total);
    const procesadas = parseInt(procesadasRows[0].procesadas);
    const pendientes = total - procesadas;
    const porcentaje_completado =
      total > 0 ? parseFloat(((procesadas / total) * 100).toFixed(2)) : 0;

    // Top categorías
    const topCategoriasRows = await query(`
      SELECT c.nombre, COUNT(*) as cantidad
      FROM ordenanza_categorias oc
      JOIN categorias c ON oc.categoria_id = c.id
      GROUP BY c.nombre
      ORDER BY cantidad DESC
      LIMIT 10
    `);

    // Distribución por año
    const porAnioRows = await query(`
      SELECT anio, COUNT(*) as cantidad
      FROM ordenanzas
      GROUP BY anio
      ORDER BY anio DESC
      LIMIT 20
    `);

    const result = {
      total,
      procesadas,
      pendientes,
      porcentaje_completado,
      top_categorias: topCategoriasRows,
      por_anio: porAnioRows,
    };

    log.info("Statistics calculated", {
      total,
      procesadas,
      pendientes,
      porcentaje_completado,
    });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result),
        },
      ],
    };
  } catch (error) {
    log.error("Calculation failed", {
      error: error instanceof Error ? error.message : String(error)
    });
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: `Error al calcular estadísticas: ${
              error instanceof Error ? error.message : String(error)
            }`,
          }),
        },
      ],
      isError: true,
    };
  }
}
