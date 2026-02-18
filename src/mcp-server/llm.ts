import OpenAI from "openai";
import "dotenv/config";
import { logger } from "./logger.js";
import { query, execute } from "./db.js";

const apiKey = process.env.GROQ_API_KEY;

if (!apiKey) {
  logger.warn(
    "GROQ_API_KEY no está configurada. Las herramientas de LLM no funcionarán."
  );
}

/**
 * Cliente Groq (OpenAI-compatible) para generación de resúmenes
 * 
 * Modelo por defecto: llama-3.3-70b-versatile
 * Base URL: https://api.groq.com/openai/v1
 * Rate limit: ~30 RPM
 */
const groq = apiKey
  ? new OpenAI({
      apiKey,
      baseURL: "https://api.groq.com/openai/v1",
      maxRetries: 2,
      timeout: 60_000, // 60 segundos para resúmenes largos
    })
  : null;

const DEFAULT_MODEL = "llama-3.3-70b-versatile";

/**
 * Sistema prompt para generación de resúmenes
 */
const SYSTEM_PROMPT_SUMMARIZE = `Eres un asistente jurídico especializado en ordenanzas municipales. Tu tarea es generar resúmenes concisos y precisos de textos legales.

Directrices:
- Mantener un tono formal y profesional
- Usar terminología jurídica apropiada
- Identificar los puntos clave del documento
- Estructurar el resumen con claridad
- Ser conciso: usar el número exacto de palabras solicitado`;

/**
 * Genera un resumen del texto especificado
 * 
 * @param texto - Texto a resumir
 * @param longitud - Número de palabras objetivo (default: 50)
 * @param estilo - 'formal' | 'simple' | 'bullet-points'
 * @returns Resumen y tokens usados
 */
export async function generateSummary(
  texto: string,
  longitud: number = 50,
  estilo: "formal" | "simple" | "bullet-points" = "formal"
): Promise<{ resumen: string; tokens_usados?: number }> {
  if (!groq) {
    throw new Error(
      "Groq client no configurado. Set GROQ_API_KEY en .env"
    );
  }

  logger.debug(
    { model: DEFAULT_MODEL, textLength: texto.length, estilo },
    "Generating summary..."
  );

  try {
    const styleInstructions = {
      formal: "Usa un estilo formal y jurídico.",
      simple: "Usa un lenguaje claro y accesible para público general.",
      "bullet-points":
        "Estructura el resumen como lista de bullet points concisa.",
    };

    const response = await groq.chat.completions.create({
      model: DEFAULT_MODEL,
      messages: [
        {
          role: "system",
          content: `${SYSTEM_PROMPT_SUMMARIZE}\n\n${styleInstructions[estilo]}\n\nLongitud objetivo: ${longitud} palabras.`,
        },
        {
          role: "user",
          content: texto.slice(0, 100_000), // Max 100k caracteres
        },
      ],
      temperature: 0.3,
      max_tokens: Math.ceil(longitud * 2), // Aproximación para longitud de palabras
    });

    const resumen = response.choices[0]?.message?.content || "";

    logger.debug(
      {
        tokens_usados: response.usage?.total_tokens,
        resumen_length: resumen.length,
      },
      "Summary generated"
    );

    return {
      resumen,
      tokens_usados: response.usage?.total_tokens,
    };
  } catch (error) {
    logger.error(
      { error: error instanceof Error ? error.message : String(error) },
      "Failed to generate summary"
    );
    throw error;
  }
}

/**
 * Busca resumen en cache o genera uno nuevo
 * 
 * @param texto - Texto a resumir
 * @param longitud - Longitud en palabras
 * @param estilo - Estilo de resumen
 * @param ordenanzaId - Opcional: UUID de la ordenanza para asociar
 * @returns Resumen y si fue cacheado
 */
export async function getOrCreateSummary(
  texto: string,
  longitud: number = 50,
  estilo: "formal" | "simple" | "bullet-points" = "formal",
  ordenanzaId?: string
): Promise<{ resumen: string; tokens_usados?: number; cached: boolean }> {
  const toolLog = logger.child({ tool: "summarize" });

  // 1. Buscar en cache
  const cacheKey = `${texto.slice(0, 200)}_${estilo}_${longitud}`; // Hash simplificado
  
  let whereClause = "texto_original = $1 AND estilo = $2 AND longitud_palabras = $3";
  let params: any[] = [texto, estilo, longitud.toString()];

  if (ordenanzaId) {
    whereClause += " AND ordenanza_id = $4";
    params.push(ordenanzaId);
  }

  const cached = await query(
    `SELECT texto_resumen, tokens_usados FROM resumenes_cache WHERE ${whereClause}`,
    params
  );

  if (cached.length > 0) {
    toolLog.debug(
      { cacheKey, ordenanzaId },
      "Summary found in cache"
    );
    return {
      resumen: cached[0].texto_resumen,
      tokens_usados: cached[0].tokens_usados
        ? parseInt(cached[0].tokens_usados)
        : undefined,
      cached: true,
    };
  }

  // 2. Generar nuevo resumen
  toolLog.info(
    { textLength: texto.length, estilo },
    "Generating new summary..."
  );

  const { resumen, tokens_usados } = await generateSummary(
    texto,
    longitud,
    estilo
  );

  // 3. Guardar en cache
  await execute(
    `
    INSERT INTO resumenes_cache (texto_original, texto_resumen, longitud_palabras, estilo, tokens_usados, modelo, ordenanza_id)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    ON CONFLICT (texto_original, estilo, longitud_palabras, ordenanza_id) DO UPDATE SET
      texto_resumen = EXCLUDED.texto_resumen,
      tokens_usados = EXCLUDED.tokens_usados
    `,
    [
      texto,
      resumen,
      longitud.toString(),
      estilo,
      tokens_usados?.toString(),
      DEFAULT_MODEL,
      ordenanzaId || null,
    ]
  );

  toolLog.info(
    { ordenanzaId, estilo },
    "Summary cached"
  );

  return {
    resumen,
    tokens_usados,
    cached: false,
  };
}

/**
 * Valida si el cliente está configurado
 */
export function isConfigured(): boolean {
  return groq !== null;
}
