import * as z from "zod/v4";
import { SemanticSearchInputSchema, OrdenanzaSimilarSchema } from "../types.js";
import { generateEmbeddingForModel, getEmbeddingsForSimilarity } from "../embeddings.js";
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

    // 2. Load embeddings (lightweight query — no category JOINs)
    const allEmbeddings = await getEmbeddingsForSimilarity(MODEL);

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

    // 3. Single pass: parse each vector once, compute similarity once, track totalAboveThreshold
    let totalAboveThreshold = 0;

    const scored = new Array<{ ordenanza_id: string; numero: number; anio: number; titulo: string; resumen: string; estado: string; score: number }>(allEmbeddings.length);

    for (let i = 0; i < allEmbeddings.length; i++) {
      const emb = allEmbeddings[i];
      const vector = parseVector(emb.vector);
      const score = cosineSimilarity(queryEmbedding, vector);

      if (score >= args.umbral) {
        totalAboveThreshold++;
      }

      scored[i] = {
        ordenanza_id: emb.ordenanza_id,
        numero: emb.numero,
        anio: emb.anio,
        titulo: emb.titulo,
        resumen: emb.resumen ?? "",
        estado: emb.estado,
        score,
      };
    }

    // 4. Filter, sort, and limit
    const results = scored
      .filter((r) => r.score >= args.umbral)
      .filter((r) => !args.solo_vigentes || r.estado === "vigente" || r.estado === "modificada")
      .sort((a, b) => b.score - a.score)
      .slice(0, args.limit);

    // 5. Remove estado from output (match OrdenanzaSimilarSchema shape)
    const output = results.map(({ estado, ...rest }) => rest);

    log.info("Semantic search complete", {
      results: output.length,
      total_above_threshold: totalAboveThreshold,
    });

    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          resultados: output,
          total: output.length,
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
