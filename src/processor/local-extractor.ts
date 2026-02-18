/**
 * Extractor estructural basado en Regex para ordenanzas.
 * 
 * Extrae información determinística del texto sin usar IA:
 * - Expediente
 * - Fecha de sanción
 * - Sección VISTO
 * - Sección CONSIDERANDO
 * - Artículos (número + texto)
 * - Referencias a otras ordenanzas/leyes
 * - Montos y monedas
 */

export interface ExtractedStructure {
  expediente: string | null;
  fecha_sancion: string | null;
  seccion_visto: string | null;
  seccion_considerando: string | null;
  articulos: Array<{
    numero: string;
    texto: string;
  }>;
  referencias: Array<{
    tipo: string;
    destino_numero: number | null;
    destino_anio: number | null;
    norma_externa_tipo: string | null;
    norma_externa_referencia: string | null;
  }>;
  montos_detallados: Array<{
    concepto: string;
    valor: number;
    moneda: string;
    es_porcentaje: boolean;
  }>;
}

/**
 * Extrae el número de expediente del VISTO.
 * Formatos comunes: "expediente N° 146/2024", "expediente nº 315/2016"
 */
function extractExpediente(texto: string): string | null {
  const match = texto.match(/expediente\s+[nNº°]+\s*(\d+\/\d{4})/i);
  return match ? match[1] : null;
}

/**
 * Extrae la fecha de sanción del final del documento.
 * Formato: "a los veinticinco días del mes de junio del año dos mil veinticuatro"
 */
function extractFechaSancion(texto: string): string | null {
  // Buscar la línea "DADA EN LA SALA DE SESIONES..."
  const match = texto.match(
    /DADA?\s+EN\s+LA\s+SALA.*?a\s+los\s+(\w+)\s+días?\s+del\s+mes\s+de\s+(\w+)\s+del?\s+año\s+(.*?)\.?$/im,
  );

  if (!match) return null;

  const [, diaTexto, mesTexto, anioTexto] = match;

  // Mapeos de texto a número
  const dias: Record<string, number> = {
    un: 1, uno: 1, dos: 2, tres: 3, cuatro: 4, cinco: 5, seis: 6, siete: 7,
    ocho: 8, nueve: 9, diez: 10, once: 11, doce: 12, trece: 13, catorce: 14,
    quince: 15, dieciséis: 16, diecisiete: 17, dieciocho: 18, diecinueve: 19,
    veinte: 20, veintiuno: 21, veintidós: 22, veintitrés: 23, veinticuatro: 24,
    veinticinco: 25, veintiséis: 26, veintisiete: 27, veintiocho: 28,
    veintinueve: 29, treinta: 30, treintayuno: 31,
  };

  const meses: Record<string, number> = {
    enero: 1, febrero: 2, marzo: 3, abril: 4, mayo: 5, junio: 6,
    julio: 7, agosto: 8, septiembre: 9, setiembre: 9, octubre: 10,
    noviembre: 11, diciembre: 12,
  };

  const dia = dias[diaTexto.toLowerCase()] || parseInt(diaTexto, 10);
  const mes = meses[mesTexto.toLowerCase()];

  if (!dia || !mes) return null;

  // Parsear año (formato: "dos mil veinticuatro" o "mil novecientos ochenta y seis")
  let anio = 0;
  const anioLower = anioTexto.toLowerCase().replace(/\s+/g, " ").trim();

  if (anioLower.startsWith("dos mil")) {
    anio = 2000;
    const resto = anioLower.replace("dos mil", "").trim();
    const unidades: Record<string, number> = {
      uno: 1, dos: 2, tres: 3, cuatro: 4, cinco: 5, seis: 6, siete: 7,
      ocho: 8, nueve: 9, diez: 10, once: 11, doce: 12, trece: 13,
      catorce: 14, quince: 15, dieciséis: 16, diecisiete: 17, dieciocho: 18,
      diecinueve: 19, veinte: 20, veintiuno: 21, veintidós: 22, veintitrés: 23,
      veinticuatro: 24, veinticinco: 25,
    };
    if (resto && unidades[resto]) {
      anio += unidades[resto];
    }
  } else if (anioLower.startsWith("mil novecientos")) {
    anio = 1900;
    const resto = anioLower.replace("mil novecientos", "").trim();
    const decenas: Record<string, number> = {
      ochenta: 80, "ochenta y seis": 86, "ochenta y siete": 87,
      "ochenta y ocho": 88, "ochenta y nueve": 89, noventa: 90,
      "noventa y uno": 91, "noventa y dos": 92, "noventa y tres": 93,
      "noventa y cuatro": 94,
    };
    anio += decenas[resto] || 0;
  }

  if (!anio || anio < 1900) return null;

  return `${anio}-${String(mes).padStart(2, "0")}-${String(dia).padStart(2, "0")}`;
}

/**
 * Extrae la sección VISTO completa.
 */
function extractSeccionVisto(texto: string): string | null {
  const match = texto.match(
    /VISTO\s+(.*?)\s+(?:y\s+)?CONSIDERANDO/is,
  );
  return match ? match[1].trim() : null;
}

/**
 * Extrae la sección CONSIDERANDO completa.
 */
function extractSeccionConsiderando(texto: string): string | null {
  const match = texto.match(
    /CONSIDERANDO\s+(.*?)\s+(?:por\s+todo\s+ello|O\s+R\s+D\s+E\s+N\s+A\s+N\s+Z\s+A)/is,
  );
  return match ? match[1].trim() : null;
}

/**
 * Extrae todos los artículos del texto.
 * Formato: "ARTICULO 1°:" o "ARTÍCULO 2º:"
 */
function extractArticulos(texto: string): Array<{ numero: string; texto: string }> {
  const articulos: Array<{ numero: string; texto: string }> = [];

  // Buscar todos los artículos
  const regex = /ART[ÍI]CULO\s+(\d+(?:bis)?)[°º]:\s*(.*?)(?=ART[ÍI]CULO\s+\d+|DADA?\s+EN\s+LA\s+SALA|$)/gis;

  let match;
  while ((match = regex.exec(texto)) !== null) {
    const numero = match[1];
    const textoArticulo = match[2].trim();

    if (textoArticulo) {
      articulos.push({ numero, texto: textoArticulo });
    }
  }

  return articulos;
}

/**
 * Extrae referencias a otras ordenanzas y normas externas.
 */
function extractReferencias(texto: string): Array<{
  tipo: string;
  destino_numero: number | null;
  destino_anio: number | null;
  norma_externa_tipo: string | null;
  norma_externa_referencia: string | null;
}> {
  const referencias: Array<{
    tipo: string;
    destino_numero: number | null;
    destino_anio: number | null;
    norma_externa_tipo: string | null;
    norma_externa_referencia: string | null;
  }> = [];

  // Adherir a leyes provinciales/nacionales
  const leyRegex = /adhier[ea]\s+(?:a\s+)?(?:la\s+)?Ley\s+[nNº°]*\s*(\d+[\./]\d+|\d+)/gi;
  let match;
  while ((match = leyRegex.exec(texto)) !== null) {
    referencias.push({
      tipo: "adhiere",
      destino_numero: null,
      destino_anio: null,
      norma_externa_tipo: "Ley Provincial",
      norma_externa_referencia: match[1],
    });
  }

  // Modificar ordenanzas anteriores
  const modifRegex = /modifica(?:r|ndo|se)?\s+(?:la\s+)?Ordenanza\s+[nNº°]*\s*(\d+)\/(\d{4})/gi;
  while ((match = modifRegex.exec(texto)) !== null) {
    referencias.push({
      tipo: "modifica",
      destino_numero: parseInt(match[1], 10),
      destino_anio: parseInt(match[2], 10),
      norma_externa_tipo: null,
      norma_externa_referencia: null,
    });
  }

  // Derogar ordenanzas
  const derogarRegex = /derog[ar|a]\s+(?:la\s+)?Ordenanza\s+[nNº°]*\s*(\d+)\/(\d{4})/gi;
  while ((match = derogarRegex.exec(texto)) !== null) {
    referencias.push({
      tipo: "deroga_total",
      destino_numero: parseInt(match[1], 10),
      destino_anio: parseInt(match[2], 10),
      norma_externa_tipo: null,
      norma_externa_referencia: null,
    });
  }

  // Decreto Ley (común en ordenanzas viejas)
  const decretoLeyRegex = /Decreto\s+Ley\s+(\d+\/\d+)/gi;
  while ((match = decretoLeyRegex.exec(texto)) !== null) {
    referencias.push({
      tipo: "cita",
      destino_numero: null,
      destino_anio: null,
      norma_externa_tipo: "Decreto Ley",
      norma_externa_referencia: match[1],
    });
  }

  return referencias;
}

/**
 * Extrae montos mencionados en el texto.
 * Busca patrones como: "=A= 24", "$500", "ARS 1000"
 */
function extractMontos(texto: string): Array<{
  concepto: string;
  valor: number;
  moneda: string;
  es_porcentaje: boolean;
}> {
  const montos: Array<{
    concepto: string;
    valor: number;
    moneda: string;
    es_porcentaje: boolean;
  }> = [];

  // Australes (moneda 1985-1991): "=A= 24"
  const australRegex = /=A=\s*([\d,.]+)/g;
  let match;
  while ((match = australRegex.exec(texto)) !== null) {
    const valor = parseFloat(match[1].replace(/\./g, "").replace(",", "."));
    montos.push({
      concepto: "Monto en australes",
      valor,
      moneda: "=A=",
      es_porcentaje: false,
    });
  }

  // Pesos argentinos: "$1000", "ARS 500"
  const pesosRegex = /(?:\$|ARS)\s*([\d,.]+)/gi;
  while ((match = pesosRegex.exec(texto)) !== null) {
    const valor = parseFloat(match[1].replace(/\./g, "").replace(",", "."));
    montos.push({
      concepto: "Monto en pesos",
      valor,
      moneda: "ARS",
      es_porcentaje: false,
    });
  }

  // Porcentajes: "50%", "10 por ciento"
  const porcentajeRegex = /([\d,.]+)\s*(?:%|por\s+ciento)/gi;
  while ((match = porcentajeRegex.exec(texto)) !== null) {
    const valor = parseFloat(match[1].replace(",", "."));
    montos.push({
      concepto: "Porcentaje",
      valor,
      moneda: "ARS",
      es_porcentaje: true,
    });
  }

  return montos;
}

/**
 * Función principal que orquesta todas las extracciones.
 */
export function extractStructure(texto: string): ExtractedStructure {
  return {
    expediente: extractExpediente(texto),
    fecha_sancion: extractFechaSancion(texto),
    seccion_visto: extractSeccionVisto(texto),
    seccion_considerando: extractSeccionConsiderando(texto),
    articulos: extractArticulos(texto),
    referencias: extractReferencias(texto),
    montos_detallados: extractMontos(texto),
  };
}
