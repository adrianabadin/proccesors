import { query } from "../db.js";
import * as z from "zod/v4";
import {
  GetReferencesInputSchema,
  ReferenciaSchema,
} from "../types.js";
import { toolLogger } from "../utils.js";

// =============================================================================
// TOOL 1: get_references
// =============================================================================

export const getReferencesTool = {
  name: "get_references",
  title: "Obtener Referencias Normativas",
  description:
    "Obtiene el árbol de vigencia y referencias normativas de una ordenanza: qué ordenanzas modifica, deroga, cita, etc.",
  inputSchema: GetReferencesInputSchema,
};

export async function getReferencesHandler(
  args: z.infer<typeof GetReferencesInputSchema>,
  ctx: any
): Promise<any> {
  const log = toolLogger("get_references");

  try {
    log.info("Fetching references...", { ordenanza_id: args.ordenanza_id });

    // Usar la función SQL arbol_vigencia ya creada
    const rows = await query("SELECT * FROM arbol_vigencia($1)", [args.ordenanza_id]);

    const formatted = rows.map((row: any) => ({
      id: row.id,
      direccion: row.direccion,
      tipo: row.tipo,
      ordenanza_relacionada_id: row.ordenanza_relacionada_id || undefined,
      numero: row.numero || undefined,
      anio: row.anio || undefined,
      titulo: row.titulo || undefined,
      norma_externa: row.norma_externa || undefined,
      articulos_afectados: row.articulos_afectados || undefined,
      notas: row.notas || undefined,
    }));

    log.info("References fetched successfully", {
      ordenanza_id: args.ordenanza_id,
      total: formatted.length,
    });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            references: formatted,
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
            error: `Error al obtener referencias: ${
              error instanceof Error ? error.message : String(error)
            }`,
          }),
        },
      ],
      isError: true,
    };
  }
}
