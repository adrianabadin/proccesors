/**
 * Schema Zod para validar la respuesta JSON de Claude API.
 *
 * Tolerante a errores parciales:
 * - Campos nullable también aceptan undefined/omitido (→ null por default)
 * - Enums inválidos caen al valor fallback (.catch)
 * - Fechas se normalizan a YYYY-MM-DD
 */

import { z } from "zod";
import { CATEGORY_SLUGS } from "./prompts.js";

// ─── Date normalization ────────────────────────────────────────

const MESES: Record<string, string> = {
  enero: "01", febrero: "02", marzo: "03", abril: "04",
  mayo: "05", junio: "06", julio: "07", agosto: "08",
  septiembre: "09", octubre: "10", noviembre: "11", diciembre: "12",
};

/**
 * Normaliza fechas a formato YYYY-MM-DD.
 * Acepta: YYYY-MM-DD, DD/MM/YYYY, "31 de marzo de 1986".
 * Retorna null si el formato no es reconocible.
 */
function normalizeDate(val: string): string | null {
  const trimmed = val.trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) return trimmed;
  const dmy = trimmed.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (dmy) {
    return `${dmy[3]}-${dmy[2].padStart(2, "0")}-${dmy[1].padStart(2, "0")}`;
  }
  const spa = trimmed
    .toLowerCase()
    .match(/^(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})$/);
  if (spa && MESES[spa[2]]) {
    return `${spa[3]}-${MESES[spa[2]]}-${spa[1].padStart(2, "0")}`;
  }
  return null;
}

// Shorthand: campo nullable que el modelo puede omitir → null
const nullStr = z.string().nullable().optional().default(null);
const nullNum = z.number().nullable().optional().default(null);
const nullBool = z.boolean().nullable().optional().default(null);

// ─── Sub-schemas ──────────────────────────────────────────────

const CategoriaSchema = z.object({
  slug: z.enum(CATEGORY_SLUGS).catch("sin-categoria"),
  relevancia: z.number().min(0).max(1).catch(() => 0.5),
});

const ArticuloSchema = z.object({
  numero: z.string(),
  texto: z.string(),
  resumen: z.string(),
});

const EntidadSchema = z.object({
  nombre: z.string(),
  tipo: z
    .enum([
      "persona_fisica",
      "empresa",
      "organismo_municipal",
      "organismo_provincial",
      "organismo_nacional",
      "institucion_educativa",
      "club_asociacion",
      "otro",
    ])
    .catch("otro"),
  rol: z
    .enum([
      "beneficiario",
      "contratista",
      "contraparte_contractual",
      "firmante",
      "solicitante",
      "mencionado",
      "sancionado",
      "otro",
    ])
    .catch("otro"),
  cuit: nullStr,
  contexto: nullStr,
});

const ReferenciaSchema = z.object({
  tipo: z
    .enum([
      "modifica",
      "deroga_total",
      "deroga_parcial",
      "complementa",
      "reglamenta",
      "adhiere",
      "prorroga",
      "convalida",
      "cita",
      "sustituye",
    ])
    .catch("cita"),
  destino_numero: nullNum,
  destino_anio: nullNum,
  norma_externa_tipo: nullStr,
  norma_externa_referencia: nullStr,
  norma_externa_descripcion: nullStr,
  articulos_afectados: nullStr,
  notas: nullStr,
});

const MontoDetalladoSchema = z.object({
  concepto: nullStr,
  valor: nullNum,
  moneda: nullStr,
  unidad: nullStr,
  es_porcentaje: nullBool,
});

const AnexoSchema = z.object({
  numero: nullStr,
  titulo: nullStr,
  tipo: nullStr,
  contenido: nullStr,
});

// ─── Schema principal ─────────────────────────────────────────

export const ExtractionResultSchema = z.object({
  resumen: z.string(),
  palabras_clave: z.array(z.string()).default([]),
  categorias: z.array(CategoriaSchema).default([]),
  expediente: nullStr,
  fecha_sancion: z
    .string()
    .nullable()
    .optional()
    .transform((val) => (val ? normalizeDate(val) : null))
    .catch(() => null),
  estado: z
    .enum([
      "vigente",
      "modificada",
      "derogada_total",
      "derogada_parcial",
      "sin_determinar",
    ])
    .catch("sin_determinar"),
  notas_vigencia: nullStr,
  monto_principal: nullNum,
  moneda: nullStr,
  seccion_visto: nullStr,
  seccion_considerando: nullStr,
  articulos: z.array(ArticuloSchema).default([]),
  entidades: z.array(EntidadSchema).default([]),
  referencias: z.array(ReferenciaSchema).default([]),
  montos_detallados: z.array(MontoDetalladoSchema).default([]),
  anexos: z.array(AnexoSchema).default([]),
});

export type ExtractionResult = z.infer<typeof ExtractionResultSchema>;

/**
 * Parsea y valida la respuesta JSON del LLM.
 * Extrae el JSON del texto de respuesta con tres estrategias:
 * 1. Bloque de código fenced (```json ... ```)
 * 2. Primer { al último } en el texto (para respuestas con texto previo)
 * 3. El texto completo directamente
 */
export function parseExtractionResponse(rawText: string): ExtractionResult {
  let jsonStr = rawText.trim();

  // 1. Extraer de bloque de código (```json ... ``` o ``` ... ```)
  const fencedMatch = jsonStr.match(/```(?:json)?\s*\n?([\s\S]*?)\n?```/);
  if (fencedMatch) {
    jsonStr = fencedMatch[1].trim();
  } else {
    // 2. Buscar primer { y último } para extraer JSON embebido en texto
    const firstBrace = jsonStr.indexOf("{");
    const lastBrace = jsonStr.lastIndexOf("}");
    if (firstBrace !== -1 && lastBrace > firstBrace) {
      jsonStr = jsonStr.slice(firstBrace, lastBrace + 1);
    }
  }

  // Parsear JSON raw
  let parsed: unknown;
  try {
    parsed = JSON.parse(jsonStr);
  } catch {
    throw new Error(
      `Respuesta no es JSON válido. Primeros 200 chars: ${rawText.slice(0, 200)}`,
    );
  }

  // Validar con Zod
  const result = ExtractionResultSchema.safeParse(parsed);

  if (!result.success) {
    const issues = result.error.issues
      .map((i) => `  - ${i.path.join(".")}: ${i.message}`)
      .join("\n");
    throw new Error(`Validación Zod fallida:\n${issues}`);
  }

  return result.data;
}
