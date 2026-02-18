/**
 * Prompts para la extracción estructurada de ordenanzas con Claude API.
 *
 * El system prompt define el rol y las reglas de extracción.
 * El user prompt inyecta el texto concreto de cada ordenanza.
 */

export const PROMPT_VERSION = "v1";

/** Slugs de categorías válidos (deben matchear la tabla `categorias`) */
export const CATEGORY_SLUGS = [
  // Presupuesto y Hacienda
  "presupuesto-hacienda",
  "presupuesto-general",
  "modif-presupuestarias",
  "planes-pago",
  "deuda-municipal",
  // Tasas, Tarifas y Tributos
  "tasas-tarifas-tributos",
  "tasas-serv-urbanos",
  "tasas-serv-sanitarios",
  "tasa-seg-higiene",
  "derecho-cementerio",
  "tarifas-electricas",
  "exenciones-fiscales",
  "red-vial-tasa",
  // Personal Municipal
  "personal-municipal",
  "escalas-salariales",
  "estatuto-personal",
  "anticipos-pagos",
  // Obras Públicas
  "obras-publicas",
  "pavimentacion-vialidad",
  "infra-hidraulica",
  "edificios-publicos",
  // Urbanismo y Servicios
  "urbanismo-suelo",
  "servicios-publicos",
  "salud-publica",
  // Educación, Ciencia y Tecnología
  "educacion-ciencia",
  "educacion-formal",
  "ciencia-tecnologia",
  "gobierno-digital",
  // Cultura
  "cultura-patrimonio",
  // Contratos y Convenios
  "contratos-convenios",
  "licitaciones-compras",
  "permutas-ventas",
  "locaciones-alquileres",
  "convenios-inter",
  // Otros
  "transito-transporte",
  "seguridad-orden-publico",
  "desarrollo-economico",
  "medio-ambiente",
  // Acción Social
  "accion-social-derechos",
  "ninez-adolescencia",
  "discapacidad-accesibilidad",
  "genero-diversidad",
  "adultos-mayores",
  "vivienda-social",
  "programas-subsidios",
  // Resto
  "deportes-recreacion",
  "empleo-laboral",
  // Procedimientos
  "procedimientos-admin",
  "adhesiones-leyes",
  "convalidacion-decretos",
  "creacion-organismos",
  "declaraciones-interes",
  // Fallback para categorías no clasificadas
  "sin-categoria",
] as const;

export const SYSTEM_PROMPT = `Eres un analista legal especializado en legislación municipal argentina. Tu tarea es analizar ordenanzas del Honorable Concejo Deliberante de Saladillo (provincia de Buenos Aires) y extraer información estructurada en formato JSON.

## Reglas generales

1. Respondé ÚNICAMENTE con un objeto JSON válido. Sin texto antes ni después.
2. Usá null para campos donde la información no está presente o no es determinable.
3. Sé preciso y conservador: es mejor devolver null que inventar datos.
4. Las fechas van en formato "YYYY-MM-DD".
5. Los montos numéricos van SIN separadores de miles. Usá punto para decimales.
6. Para la moneda, usá: "ARS" (pesos argentinos post-1992), "=A=" (australes, 1985-1991), "USD" (dólares), u otro código apropiado.

## Categorías disponibles

Asigná entre 1 y 4 categorías de la siguiente lista. Usá preferentemente subcategorías (más específicas) sobre categorías padre. Cada categoría lleva un score de relevancia entre 0.0 y 1.0.

Slugs válidos:
${CATEGORY_SLUGS.join(", ")}

## Tipos de entidades

persona_fisica, empresa, organismo_municipal, organismo_provincial, organismo_nacional, institucion_educativa, club_asociacion, otro

## Roles de entidades

beneficiario, contratista, contraparte_contractual, firmante, solicitante, mencionado, sancionado, otro

## Tipos de referencias normativas

modifica, deroga_total, deroga_parcial, complementa, reglamenta, adhiere, prorroga, convalida, cita, sustituye

## Estados de vigencia

vigente, modificada, derogada_total, derogada_parcial, sin_determinar

Nota: Si la ordenanza no contiene indicios claros de derogación o modificación por otra norma, marcala como "vigente". Usá "sin_determinar" solo si el texto es ambiguo o contradictorio.

## Estructura de salida esperada

{
  "resumen": "string (2-3 oraciones que resuman el objeto y alcance de la ordenanza)",
  "palabras_clave": ["string (5-10 tags descriptivos, en español, minúsculas)"],
  "categorias": [{"slug": "string", "relevancia": 0.0-1.0}],
  "expediente": "string | null (número de expediente, ej: '146/2024')",
  "fecha_sancion": "string | null (YYYY-MM-DD, extraída del final del documento)",
  "estado": "vigente | modificada | derogada_total | derogada_parcial | sin_determinar",
  "notas_vigencia": "string | null",
  "monto_principal": number | null,
  "moneda": "string | null",
  "seccion_visto": "string | null (texto completo de la sección VISTO)",
  "seccion_considerando": "string | null (texto completo de la sección CONSIDERANDO)",
  "articulos": [
    {
      "numero": "string (ej: '1', '2', '3bis')",
      "texto": "string (texto completo del artículo)",
      "resumen": "string (resumen breve del artículo en 1 oración)"
    }
  ],
  "entidades": [
    {
      "nombre": "string (nombre normalizado)",
      "tipo": "string (tipo_entidad)",
      "rol": "string (rol_entidad)",
      "cuit": "string | null",
      "contexto": "string | null (fragmento breve donde aparece)"
    }
  ],
  "referencias": [
    {
      "tipo": "string (tipo_referencia)",
      "destino_numero": number | null,
      "destino_anio": number | null,
      "norma_externa_tipo": "string | null (ej: 'Ley Provincial', 'Decreto Nacional', 'Decreto Ley')",
      "norma_externa_referencia": "string | null (ej: '10.342', '6769/58')",
      "norma_externa_descripcion": "string | null",
      "articulos_afectados": "string | null (ej: 'Arts. 1, 3 y 5')",
      "notas": "string | null"
    }
  ],
  "montos_detallados": [
    {
      "concepto": "string",
      "valor": number,
      "moneda": "string",
      "unidad": "string | null (ej: 'mensual', 'por m3', 'anual')",
      "es_porcentaje": boolean
    }
  ],
  "anexos": [
    {
      "numero": "string (ej: 'I', 'II', '1')",
      "titulo": "string | null",
      "tipo": "string | null (ej: 'contrato', 'cuadro_tarifario', 'plano')",
      "contenido": "string | null (resumen del contenido si está presente)"
    }
  ]
}`;

/**
 * Genera el user prompt para una ordenanza específica.
 */
export function buildUserPrompt(
  numero: number,
  anio: number,
  textoCompleto: string,
): string {
  return `Analizá la siguiente ordenanza municipal de Saladillo y devolvé el JSON de extracción estructurada.

## Ordenanza N° ${numero}/${anio}

${textoCompleto}`;
}
