import * as z from "zod/v4";

// =============================================================================
// ESTADOS
// =============================================================================

export const EstadoVigenciaEnum = z.enum([
  "vigente",
  "modificada",
  "derogada_total",
  "derogada_parcial",
  "sin_determinar",
]);

export type EstadoVigencia = z.infer<typeof EstadoVigenciaEnum>;

export const EstiloResumenEnum = z.enum([
  "formal",
  "simple",
  "bullet-points",
]);

export type EstiloResumen = z.infer<typeof EstiloResumenEnum>;

// =============================================================================
// RESPUESTAS COMUNES
// =============================================================================

export const ErrorSchema = z.object({
  error: z.string(),
});

export type ErrorResponse = z.infer<typeof ErrorSchema>;

// =============================================================================
// ORDENANZA (Summary)
// =============================================================================

export const CategoriaSummarySchema = z.object({
  nombre: z.string(),
  slug: z.string(),
  relevancia: z.number().min(0).max(1),
});

export type CategoriaSummary = z.infer<typeof CategoriaSummarySchema>;

export const OrdenanzaSummarySchema = z.object({
  id: z.string().uuid(),
  numero: z.number().positive(),
  anio: z.number().int().min(1980).max(2100),
  titulo: z.string(),
  resumen: z.string().nullable(),
  estado: EstadoVigenciaEnum,
  rank: z.number().optional(),
  headline: z.string().optional(),
  categorias: z.array(CategoriaSummarySchema).default([]),
});

export type OrdenanzaSummary = z.infer<typeof OrdenanzaSummarySchema>;

// =============================================================================
// ORDENANZA (Completa)
// =============================================================================

export const ArticuloSchema = z.object({
  numero: z.string(),
  texto: z.string(),
  resumen: z.string().nullable(),
});

export type Articulo = z.infer<typeof ArticuloSchema>;

export const EntidadSchema = z.object({
  nombre: z.string(),
  tipo: z.string(),
  rol: z.string(),
  cuit: z.string().nullable().optional(),
  contexto: z.string().nullable().optional(),
});

export type Entidad = z.infer<typeof EntidadSchema>;

export const ReferenciaSchema = z.object({
  id: z.string().uuid().optional(),
  direccion: z.enum(["afecta_a", "afectada_por"]),
  tipo: z.string(),
  ordenanza_relacionada_id: z.string().uuid().nullable(),
  numero: z.number().nullable(),
  anio: z.number().nullable(),
  titulo: z.string().nullable(),
  norma_externa: z.string().nullable(),
  articulos_afectados: z.string().nullable(),
  notas: z.string().nullable(),
});

export type Referencia = z.infer<typeof ReferenciaSchema>;

export const MontoSchema = z.object({
  concepto: z.string(),
  valor: z.number(),
  moneda: z.string(),
  unidad: z.string().nullable().optional(),
  es_porcentaje: z.boolean(),
});

export type Monto = z.infer<typeof MontoSchema>;

export const AnexoSchema = z.object({
  numero: z.string(),
  titulo: z.string().nullable(),
  tipo: z.string().nullable(),
  contenido: z.string().nullable(),
});

export type Anexo = z.infer<typeof AnexoSchema>;

export const OrdenanzaCompletaSchema = z.object({
  id: z.string().uuid(),
  numero: z.number().positive(),
  anio: z.number().int().min(1980).max(2100),
  titulo: z.string(),
  texto_completo: z.string(),
  resumen: z.string().nullable(),
  palabras_clave: z.array(z.string()).default([]),
  expediente: z.string().nullable(),
  fecha_sancion: z.string().nullable(),
  estado: EstadoVigenciaEnum,
  notas_vigencia: z.string().nullable(),
  seccion_visto: z.string().nullable(),
  seccion_considerando: z.string().nullable(),
  monto_principal: z.number().nullable(),
  moneda: z.string().nullable(),
  articulos: z.array(ArticuloSchema).default([]),
  entidades: z.array(EntidadSchema).default([]),
  referencias: z.array(ReferenciaSchema).default([]),
  montos: z.array(MontoSchema).default([]),
  anexos: z.array(AnexoSchema).default([]),
  categorias: z.array(CategoriaSummarySchema).default([]),
});

export type OrdenanzaCompleta = z.infer<typeof OrdenanzaCompletaSchema>;

// =============================================================================
// CATEGORÍAS
// =============================================================================

export const CategoriaSchema = z.object({
  id: z.number().positive(),
  nombre: z.string(),
  slug: z.string(),
  descripcion: z.string().nullable(),
  parent_id: z.number().nullable(),
});

export type Categoria = z.infer<typeof CategoriaSchema>;

// =============================================================================
// ESTADÍSTICAS
// =============================================================================

export const StatsSchema = z.object({
  total: z.number().nonnegative(),
  procesadas: z.number().nonnegative(),
  pendientes: z.number().nonnegative(),
  porcentaje_completado: z.number().min(0).max(100),
  top_categorias: z.array(
    z.object({
      nombre: z.string(),
      cantidad: z.number().nonnegative(),
    })
  ),
  por_anio: z.array(
    z.object({
      anio: z.number().int(),
      cantidad: z.number().nonnegative(),
    })
  ),
});

export type Stats = z.infer<typeof StatsSchema>;

// =============================================================================
// EMBEDDINGS
// =============================================================================

export const OrdenanzaSimilarSchema = z.object({
  id: z.string().uuid(),
  numero: z.number().positive(),
  anio: z.number().int(),
  titulo: z.string(),
  resumen: z.string(),
  score: z.number().min(0).max(1),
  categorias: z.array(CategoriaSummarySchema).default([]),
});

export type OrdenanzaSimilar = z.infer<typeof OrdenanzaSimilarSchema>;

// =============================================================================
// RESÚMENES
// =============================================================================

export const ResumenGeneradoSchema = z.object({
  resumen: z.string(),
  tokens_usados: z.number().nullable().optional(),
  modelo: z.string(),
  cached: z.boolean().default(false),
});

export type ResumenGenerado = z.infer<typeof ResumenGeneradoSchema>;

// =============================================================================
// INPUT SCHEMAS PARA TOOLS
// =============================================================================

// search_ordenanzas
export const SearchOrdenanzasInputSchema = z.object({
  query: z.string().min(1).describe("Término de búsqueda"),
  limit: z.number().min(1).max(100).optional().default(20),
  solo_vigentes: z.boolean().optional().default(false),
});

export type SearchOrdenanzasInput = z.infer<typeof SearchOrdenanzasInputSchema>;

// search_by_category
export const SearchByCategoryInputSchema = z.object({
  slug: z.string().describe("Slug de categoría"),
  anio: z.number().int().min(1980).max(2100).optional(),
  limit: z.number().min(1).max(100).optional().default(20),
});

export type SearchByCategoryInput = z.infer<typeof SearchByCategoryInputSchema>;

// search_by_year_range
export const SearchByYearRangeInputSchema = z.object({
  desde: z.number().int().min(1980).max(2100),
  hasta: z.number().int().min(1980).max(2100),
  limit: z.number().min(1).max(100).optional().default(20),
});

export type SearchByYearRangeInput = z.infer<typeof SearchByYearRangeInputSchema>;

// get_ordenanza
export const GetOrdenanzaInputSchema = z.object({
  id: z.string().uuid().describe("UUID de la ordenanza"),
});

export type GetOrdenanzaInput = z.infer<typeof GetOrdenanzaInputSchema>;

// get_anexo
export const GetAnexoInputSchema = z.object({
  ordenanza_id: z.string().uuid().describe("UUID de la ordenanza"),
  anexo_numero: z.string().describe("Número del anexo"),
});

export type GetAnexoInput = z.infer<typeof GetAnexoInputSchema>;

// search_by_entity
export const SearchByEntityInputSchema = z.object({
  nombre: z.string().min(1).describe("Nombre o parte del nombre de la entidad"),
  tipo: z.string().optional().describe("Tipo de entidad (opcional)"),
  limit: z.number().min(1).max(100).optional().default(20),
});

export type SearchByEntityInput = z.infer<typeof SearchByEntityInputSchema>;

// get_references
export const GetReferencesInputSchema = z.object({
  ordenanza_id: z.string().uuid().describe("UUID de la ordenanza"),
});

export type GetReferencesInput = z.infer<typeof GetReferencesInputSchema>;

// list_categories
export const ListCategoriesInputSchema = z.object({});

export type ListCategoriesInput = z.infer<typeof ListCategoriesInputSchema>;

// get_stats
export const GetStatsInputSchema = z.object({});

export type GetStatsInput = z.infer<typeof GetStatsInputSchema>;

// similar_ordenanzas
export const SimilarOrdenanzasInputSchema = z.object({
  ordenanza_id: z.string().uuid().describe("UUID de la ordenanza de referencia"),
  limit: z.number().min(1).max(50).optional().default(10),
  umbral: z.number().min(0).max(1).optional().default(0.7),
});

export type SimilarOrdenanzasInput = z.infer<typeof SimilarOrdenanzasInputSchema>;

export const SimilarOrdenanzasOutputSchema = z.object({
  similares: z.array(OrdenanzaSimilarSchema),
});

export type SimilarOrdenanzasOutput = z.infer<typeof SimilarOrdenanzasOutputSchema>;

// summarize_texto
export const SummarizeTextoInputSchema = z.object({
  texto: z.string().min(1).max(100_000).describe("Texto a resumir"),
  longitud: z.number().min(10).max(300).optional().default(50),
  estilo: EstiloResumenEnum.optional().default("formal"),
});

export type SummarizeTextoInput = z.infer<typeof SummarizeTextoInputSchema>;

export const SummarizeTextoOutputSchema = z.object({
  resumen: z.string(),
  tokens_usados: z.number().optional(),
  modelo: z.string(),
  cached: z.boolean().default(false),
});

export type SummarizeTextoOutput = z.infer<typeof SummarizeTextoOutputSchema>;

// semantic_search
export const SemanticSearchInputSchema = z.object({
  query: z.string().min(1).describe(
    "Consulta en lenguaje natural. Ejemplo: 'ordenanzas sobre habilitación de comercios nocturnos'"
  ),
  limit: z.number().min(1).max(50).optional().default(10),
  umbral: z.number().min(0).max(1).optional().default(0.7),
  solo_vigentes: z.boolean().optional().default(false),
});

export type SemanticSearchInput = z.infer<typeof SemanticSearchInputSchema>;

// health_check
export const HealthCheckInputSchema = z.object({});

export type HealthCheckInput = z.infer<typeof HealthCheckInputSchema>;

export const HealthCheckOutputSchema = z.object({
  status: z.enum(["ok", "error"]),
  db: z.enum(["connected", "disconnected", "error"]),
  timestamp: z.string(),
  uptime_ms: z.number().nonnegative(),
});

export type HealthCheckOutput = z.infer<typeof HealthCheckOutputSchema>;
