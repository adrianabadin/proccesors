import * as z from "zod/v4";
import { ArticuloSemanticSearchInputSchema } from "../types.js";
import { generateEmbeddingForModel } from "../embeddings.js";
import { searchArticulosSimilar } from "../vector-store.js";
import { toolLogger } from "../utils.js";

const MODEL = "text-embedding-3-large" as const;

export const semanticSearchArticulosTool = {
  name: "semantic_search_articulos",
  title: "Búsqueda Semántica de Artículos",
  description:
    "Busca artículos de ordenanzas por concepto o situación en lenguaje natural usando embeddings vectoriales. " +
    "A diferencia de search_ordenanzas (búsqueda por palabras clave en ordenanzas completas), esta herramienta " +
    "busca a nivel de artículo individual — útil para encontrar disposiciones específicas dentro de ordenanzas. " +
    "Requiere embeddings de artículos pre-generados (ejecutar script de generación batch de artículos primero).",
  inputSchema: ArticuloSemanticSearchInputSchema,
};

export async function semanticSearchArticulosHandler(
  args: z.infer<typeof ArticuloSemanticSearchInputSchema>,
  _ctx: any,
): Promise<any> {
  const log = toolLogger("semantic_search_articulos");

  try {
    log.info("Articulo semantic search", { query: args.query, limit: args.limit });

    const queryEmbedding = await generateEmbeddingForModel(args.query, MODEL);

    const results = await searchArticulosSimilar(
      queryEmbedding,
      args.limit,
      args.umbral,
    );

    if (results.length === 0) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: "No se encontraron artículos. Ejecutá 'npx tsx src/processor/generate-articulo-embeddings.ts' para generar los embeddings de artículos primero.",
            modelo: MODEL,
          }),
        }],
        isError: true,
      };
    }

    const filtered = args.solo_vigentes
      ? results.filter(r => r.estado === "vigente" || r.estado === "modificada")
      : results;

    const output = filtered.map(r => ({
      articulo_id: r.articulo_id,
      ordenanza_id: r.ordenanza_id,
      numero_articulo: r.numero_articulo,
      texto: r.texto,
      score: r.score,
      ordenanza: {
        numero: r.numero,
        anio: r.anio,
        titulo: r.titulo,
        estado: r.estado,
      },
    }));

    log.info("Articulo search complete", { results: output.length, total_found: results.length });

    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          resultados: output,
          total: output.length,
          query: args.query,
          modelo: MODEL,
          umbral: args.umbral,
        }),
      }],
    };
  } catch (error) {
    log.error("Articulo search failed", {
      error: error instanceof Error ? error.message : String(error),
    });
    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          error: `Error en búsqueda de artículos: ${error instanceof Error ? error.message : String(error)}`,
        }),
      }],
      isError: true,
    };
  }
}
