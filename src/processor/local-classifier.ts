/**
 * Clasificador semántico local usando @xenova/transformers.
 * 
 * Usa modelos locales (sin API) para:
 * 1. Clasificación Zero-Shot (categorías)
 * 2. Resumen abstractivo (T5)
 * 3. Generación de palabras clave
 */

import { pipeline, env } from "@xenova/transformers";
import { CATEGORY_SLUGS } from "./prompts.js";

// Configurar caché local para modelos
env.cacheDir = "./.cache/transformers";

// ─── Tipos ────────────────────────────────────────────────────

export interface ClassificationResult {
  resumen: string;
  palabras_clave: string[];
  categorias: Array<{
    slug: string;
    relevancia: number;
  }>;
  estado: "vigente" | "modificada" | "derogada_total" | "derogada_parcial" | "sin_determinar";
}

// ─── Pipelines (lazy load) ────────────────────────────────────

let classifierPipeline: any = null;
let summarizerPipeline: any = null;

/**
 * Inicializa el pipeline de clasificación zero-shot.
 * Modelo: mDeBERTa-v3 entrenado en MNLI/XNLI (multilingual).
 */
async function getClassifier(): Promise<any> {
  if (!classifierPipeline) {
    console.log("📦 Descargando modelo de clasificación (primera vez, ~500MB)...");
    classifierPipeline = await pipeline(
      "zero-shot-classification",
      "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
    );
    console.log("✅ Clasificador listo.");
  }
  return classifierPipeline;
}

/**
 * Inicializa el pipeline de resumen abstractivo.
 * Modelo: LaMini-Flan-T5-248M (generativo pequeño, funciona en CPU).
 */
async function getSummarizer(): Promise<any> {
  if (!summarizerPipeline) {
    console.log("📦 Descargando modelo de resumen (primera vez, ~250MB)...");
    summarizerPipeline = await pipeline(
      "summarization",
      "Xenova/LaMini-Flan-T5-248M",
    );
    console.log("✅ Resumidor listo.");
  }
  return summarizerPipeline;
}

/**
 * Mapeo de category slugs a labels legibles en español.
 */
const CATEGORY_LABELS: Record<string, string> = {
  "presupuesto-hacienda": "Presupuesto y Hacienda",
  "presupuesto-general": "Presupuesto General de Gastos y Recursos",
  "modif-presupuestarias": "Modificaciones Presupuestarias",
  "planes-pago": "Planes de Pago y Regularización",
  "deuda-municipal": "Deuda Municipal",
  "tasas-tarifas-tributos": "Tasas, Tarifas y Tributos",
  "tasas-serv-urbanos": "Tasas por Servicios Urbanos",
  "tasas-serv-sanitarios": "Tasas por Servicios Sanitarios",
  "tasa-seg-higiene": "Tasa de Seguridad e Higiene",
  "derecho-cementerio": "Derecho de Cementerio",
  "tarifas-electricas": "Tarifas Eléctricas",
  "exenciones-fiscales": "Exenciones y Beneficios Fiscales",
  "red-vial-tasa": "Red Vial Municipal (Tasa)",
  "personal-municipal": "Personal Municipal",
  "escalas-salariales": "Escalas Salariales",
  "estatuto-personal": "Estatuto del Personal",
  "anticipos-pagos": "Anticipos y Pagos Extraordinarios",
  "obras-publicas": "Obras Públicas e Infraestructura",
  "pavimentacion-vialidad": "Pavimentación y Vialidad",
  "infra-hidraulica": "Infraestructura Hidráulica",
  "edificios-publicos": "Edificios Públicos",
  "urbanismo-suelo": "Urbanismo y Uso del Suelo",
  "servicios-publicos": "Servicios Públicos",
  "salud-publica": "Salud Pública",
  "educacion-ciencia": "Educación, Ciencia y Tecnología",
  "educacion-formal": "Educación Formal y Cooperadoras",
  "ciencia-tecnologia": "Ciencia y Tecnología",
  "gobierno-digital": "Modernización y Gobierno Digital",
  "cultura-patrimonio": "Cultura y Patrimonio",
  "contratos-convenios": "Contratos y Convenios",
  "licitaciones-compras": "Licitaciones y Compras",
  "permutas-ventas": "Permutas y Ventas de Inmuebles",
  "locaciones-alquileres": "Locaciones y Alquileres",
  "convenios-inter": "Convenios Interinstitucionales",
  "transito-transporte": "Tránsito y Transporte",
  "seguridad-orden-publico": "Seguridad y Orden Público",
  "desarrollo-economico": "Desarrollo Económico y Producción",
  "medio-ambiente": "Medio Ambiente",
  "accion-social-derechos": "Acción Social y Derechos",
  "ninez-adolescencia": "Niñez y Adolescencia",
  "discapacidad-accesibilidad": "Discapacidad y Accesibilidad",
  "genero-diversidad": "Género y Diversidad",
  "adultos-mayores": "Adultos Mayores",
  "vivienda-social": "Vivienda Social",
  "programas-subsidios": "Programas y Subsidios Sociales",
  "deportes-recreacion": "Deportes y Recreación",
  "empleo-laboral": "Empleo y Relaciones Laborales",
  "procedimientos-admin": "Procedimientos y Administración",
  "adhesiones-leyes": "Adhesiones a Leyes",
  "convalidacion-decretos": "Convalidación de Decretos",
  "creacion-organismos": "Creación de Organismos",
  "declaraciones-interes": "Declaraciones de Interés",
};

/**
 * Clasifica el texto en las categorías del proyecto.
 * Usa zero-shot classification con hypothesis template en español.
 */
export async function classifyText(
  texto: string,
): Promise<Array<{ slug: string; relevancia: number }>> {
  const classifier = await getClassifier();

  // Usar las primeras 2000 chars para clasificación (suficiente para VISTO + primer artículo)
  const textoParcial = texto.slice(0, 2000);

  // Obtener labels legibles
  const candidateLabels = CATEGORY_SLUGS.map((slug) => CATEGORY_LABELS[slug]);

  // Clasificar
  const result = await classifier(textoParcial, candidateLabels, {
    multi_label: true,
    hypothesis_template: "Este documento legal municipal trata sobre {}",
  }) as { labels: string[]; scores: number[] };

  // Tomar top 3 categorías con score > 0.3
  const categorias = result.labels
    .map((label, idx) => {
      // Encontrar el slug correspondiente
      const slug = CATEGORY_SLUGS.find((s) => CATEGORY_LABELS[s] === label);
      return {
        slug: slug || "procedimientos-admin",
        relevancia: result.scores[idx],
      };
    })
    .filter((cat) => cat.relevancia > 0.3)
    .slice(0, 3);

  // Si no hay ninguna con score > 0.3, devolver la top 1
  if (categorias.length === 0 && result.labels.length > 0) {
    const slug = CATEGORY_SLUGS.find((s) => CATEGORY_LABELS[s] === result.labels[0]);
    categorias.push({
      slug: slug || "procedimientos-admin",
      relevancia: result.scores[0],
    });
  }

  return categorias;
}

/**
 * Genera un resumen abstractivo del texto usando T5.
 */
export async function summarizeText(texto: string): Promise<string> {
  const summarizer = await getSummarizer();

  // Tomar VISTO + CONSIDERANDO + primer artículo (máx 1500 chars)
  const textoParcial = texto.slice(0, 1500);

  try {
    const result = await summarizer(textoParcial, {
      max_length: 150,
      min_length: 40,
      do_sample: false,
    }) as { summary_text: string }[];

    return result[0]?.summary_text || "Resumen no disponible.";
  } catch (error) {
    console.warn("  ⚠️  Error en resumen, usando extractivo:", error);
    // Fallback: resumen extractivo (primeras 2 oraciones del VISTO)
    const oraciones = texto.split(/\.\s+/);
    return oraciones.slice(0, 2).join(". ") + ".";
  }
}

/**
 * Genera palabras clave usando frecuencia TF (simple).
 * Filtrado por stopwords españolas.
 */
export function generateKeywords(texto: string): string[] {
  const stopwords = new Set([
    "el", "la", "de", "que", "y", "a", "en", "un", "ser", "se", "no", "haber",
    "por", "con", "su", "para", "como", "estar", "tener", "le", "lo", "todo",
    "pero", "más", "hacer", "o", "poder", "decir", "este", "ir", "otro", "ese",
    "la", "si", "me", "ya", "ver", "porque", "dar", "cuando", "él", "muy",
    "sin", "vez", "mucho", "saber", "qué", "sobre", "mi", "alguno", "mismo",
    "yo", "también", "hasta", "año", "dos", "querer", "entre", "así", "primero",
    "desde", "grande", "eso", "ni", "nos", "llegar", "pasar", "tiempo", "ella",
    "sí", "día", "uno", "bien", "poco", "deber", "entonces", "poner", "cosa",
    "tanto", "hombre", "parecer", "nuestro", "tan", "donde", "ahora", "parte",
    "después", "vida", "quedar", "siempre", "creer", "hablar", "llevar", "dejar",
    "nada", "cada", "seguir", "menos", "nuevo", "encontrar", "algo", "solo",
  ]);

  // Extraer palabras (minúsculas, sin acentos)
  const palabras = texto
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .match(/\b[a-z]{4,}\b/g) || [];

  // Contar frecuencias
  const freq: Record<string, number> = {};
  for (const palabra of palabras) {
    if (!stopwords.has(palabra)) {
      freq[palabra] = (freq[palabra] || 0) + 1;
    }
  }

  // Top 8 más frecuentes
  return Object.entries(freq)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 8)
    .map(([palabra]) => palabra);
}

/**
 * Detecta el estado de vigencia basándose en palabras clave.
 */
export function detectEstado(texto: string, referencias: any[]): "vigente" | "modificada" | "derogada_total" | "derogada_parcial" | "sin_determinar" {
  const textoLower = texto.toLowerCase();

  // Si deroga totalmente otra ordenanza
  if (referencias.some((r) => r.tipo === "deroga_total")) {
    return "derogada_total";
  }

  // Si deroga parcialmente
  if (referencias.some((r) => r.tipo === "deroga_parcial")) {
    return "derogada_parcial";
  }

  // Si modifica otra
  if (referencias.some((r) => r.tipo === "modifica")) {
    return "modificada";
  }

  // Si menciona "derogar" o "dejar sin efecto"
  if (textoLower.includes("derog") || textoLower.includes("sin efecto")) {
    return "derogada_total";
  }

  // Default: vigente
  return "vigente";
}

/**
 * Función principal que orquesta clasificación + resumen.
 */
export async function processWithAI(
  texto: string,
  referencias: any[],
): Promise<ClassificationResult> {
  console.log("  🤖 Clasificando con IA local...");

  const [categorias, resumen] = await Promise.all([
    classifyText(texto),
    summarizeText(texto),
  ]);

  const palabras_clave = generateKeywords(texto);
  const estado = detectEstado(texto, referencias);

  return {
    resumen,
    palabras_clave,
    categorias,
    estado,
  };
}
