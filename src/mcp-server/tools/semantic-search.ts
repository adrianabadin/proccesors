import * as z from "zod/v4";
import { SemanticSearchInputSchema, OrdenanzaSimilarSchema } from "../types.js";
import { generateEmbeddingForModel } from "../embeddings.js";
import { searchSimilar, SearchResult } from "../vector-store.js";
import { toolLogger } from "../utils.js";

const MODEL = "text-embedding-3-large" as const;

export const semanticSearchTool = {
  name: "semantic_search",
  title: "Búsqueda Semántica de Ordenanzas",
  description:
    "Busca ordenanzas por concepto o situación en lenguaje natural usando embeddings vectoriales. " +
    "A diferencia de search_ordenanzas (búsqueda por palabras clave), esta herramienta encuentra " +
    "ordenanzas por similitud semántica — útil cuando no se conocen las palabras exactas. " +
    "A diferencia de similar_ordenanzas (que requiere un ID de ordenanza), permite buscar por texto libre. " +
    "Requiere embeddings pre-generados (ejecutar script de generación batch primero).",
  inputSchema: SemanticSearchInputSchema,
};

export async function semanticSearchHandler(
  args: z.infer<typeof SemanticSearchInputSchema>,
  _ctx: any,
): Promise<any> {
  const log = toolLogger("semantic_search");

  try {
    log.info("Semantic search", { query: args.query, limit: args.limit, umbral: args.umbral });

    // 1. Generate query embedding (OpenAI API call, ~1.5s)
    const queryEmbedding = await generateEmbeddingForModel(args.query, MODEL);

    // 2. Search LanceDB local (< 100ms for 2778 vectors)
    const results = await searchSimilar(
      queryEmbedding,
      args.limit,
      args.umbral,
    );

    if (results.length === 0) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: "No se encontraron resultados. Ejecuta 'npx tsx src/processor/sync-vectors.ts' para sincronizar los embeddings a LanceDB local.",
            modelo: MODEL,
            hint: "Asegurate de haber corrido el script de sync después de generar los embeddings.",
          }),
        }],
        isError: true,
      };
    }

    // 3. Post-filter solo_vigentes on results
    const filtered = args.solo_vigentes
      ? results.filter(r => r.estado === "vigente" || r.estado === "modificada")
      : results;

    // 4. Format output (match OrdenanzaSimilarSchema shape)
    const output = filtered.map(({ estado, ...rest }) => rest);

    log.info("Semantic search complete", {
      results: output.length,
      total_found: results.length,
    });

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
    log.error("Semantic search failed", {
      error: error instanceof Error ? error.message : String(error),
    });
    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          error: `Error en búsqueda semántica: ${error instanceof Error ? error.message : String(error)}`,
        }),
      }],
      isError: true,
    };
  }
}
