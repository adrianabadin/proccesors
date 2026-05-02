import * as z from "zod/v4";
import { SemanticSearchInputSchema, OrdenanzaSimilarSchema } from "../types.js";
import { generateEmbeddingForModel, getAllEmbeddingsByModel } from "../embeddings.js";
import { cosineSimilarity, parseVector, toolLogger } from "../utils.js";

const MODEL = "text-embedding-3-large" as const;

// =============================================================================
// TOOL: semantic_search
// =============================================================================

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
  ctx: any
): Promise<any> {
  const log = toolLogger("semantic_search");

  try {
    log.info("Semantic search", { query: args.query, limit: args.limit, umbral: args.umbral });

    // 1. Generate query embedding (NOT cached — ephemeral)
    const queryEmbedding = await generateEmbeddingForModel(args.query, MODEL);

    // 2. Load all pre-generated large embeddings
    const allEmbeddings = await getAllEmbeddingsByModel(MODEL);

    if (allEmbeddings.length === 0) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: "No hay embeddings pre-generados para el modelo text-embedding-3-large. Ejecuta el script de generación batch primero (npx tsx src/processor/generate-embeddings.ts).",
            modelo: MODEL,
          }),
        }],
        isError: true,
      };
    }

    log.debug("Comparing embeddings", { total: allEmbeddings.length, query_dims: queryEmbedding.length });

    // 3. Compute cosine similarity for each
    const results = allEmbeddings
      .map((emb) => {
        const vector = parseVector(emb.vector);
        const score = cosineSimilarity(queryEmbedding, vector);
        return {
          id: emb.ordenanza_id,
          numero: emb.numero,
          anio: emb.anio,
          titulo: emb.titulo,
          resumen: emb.resumen ?? "",
          estado: emb.estado,
          score,
          categorias: emb.categorias ? JSON.parse(emb.categorias) : [],
        };
      })
      // 4. Filter by threshold
      .filter((r) => r.score >= args.umbral)
      // 5. Optional: solo_vigentes post-filter
      .filter((r) => !args.solo_vigentes || r.estado === "vigente" || r.estado === "modificada")
      // 6. Sort by score desc, slice to limit
      .sort((a, b) => b.score - a.score)
      .slice(0, args.limit)
      // 7. Remove estado from output (match OrdenanzaSimilarSchema shape)
      .map(({ estado, ...rest }) => rest);

    const totalAboveThreshold = allEmbeddings
      .map((emb) => cosineSimilarity(queryEmbedding, parseVector(emb.vector)))
      .filter((s) => s >= args.umbral).length;

    log.info("Semantic search complete", {
      results: results.length,
      total_above_threshold: totalAboveThreshold,
    });

    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          resultados: results,
          total: results.length,
          total_above_threshold: totalAboveThreshold,
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
