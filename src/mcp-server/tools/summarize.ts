import { query } from "../db.js";
import * as z from "zod/v4";
import {
  SummarizeTextoInputSchema,
  SummarizeTextoOutputSchema,
  EstiloResumenEnum,
} from "../types.js";
import {
  getOrCreateSummary,
  isConfigured as isLLMConfigured,
} from "../llm.js";
import { toolLogger } from "../utils.js";

// =============================================================================
// TOOL 1: summarize_texto
// =============================================================================

export const summarizeTextoTool = {
  name: "summarize_texto",
  title: "Generar Resumen con IA",
  description:
    "Genera un resumen de texto arbitrario usando el modelo de IA (Groq Llama 3.3 70B). Permite configurar longitud y estilo del resumen. Los resúmenes se cachean automáticamente para reducir costos de API.",
  inputSchema: SummarizeTextoInputSchema,
};

export async function summarizeTextoHandler(
  args: z.infer<typeof SummarizeTextoInputSchema>,
  ctx: any
): Promise<any> {
  const log = toolLogger("summarize_texto");

  try {
    if (!isLLMConfigured()) {
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              error:
                "Cliente LLM no configurado. Set GROQ_API_KEY en .env para usar esta herramienta.",
            }),
          },
        ],
        isError: true,
      };
    }

    log.info("Generating summary...", {
      textLength: args.texto.length,
      estilo: args.estilo,
      longitud: args.longitud,
    });

    const { resumen, tokens_usados, cached } = await getOrCreateSummary(
      args.texto,
      args.longitud,
      args.estilo
    );

    const result: z.infer<typeof SummarizeTextoOutputSchema> = {
      resumen,
      tokens_usados,
      modelo: "llama-3.3-70b",
      cached,
    };

    log.info("Summary generated", {
      cached,
      tokens_usados,
      resumen_length: resumen.length,
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
    log.error("Summary generation failed", {
      error: error instanceof Error ? error.message : String(error)
    });
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: `Error al generar resumen: ${
              error instanceof Error ? error.message : String(error)
            }`,
          }),
        },
      ],
      isError: true,
    };
  }
}
