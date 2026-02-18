import { pipeline } from "@xenova/transformers";

async function classifyOrdinance() {
    // 1. Modelo más adecuado para español y textos legales
    const MODEL = 'Xenova/roberta-large-mnli';
    
    // 2. Etiquetas mejor definidas y con contexto
    const labels = ["Contrataciones Publicas",        "Contratación de servicios informáticos para tasas municipales",

  "Servicios Públicos",
  "Tasas y Tarifas",
  "Salud Pública",
  "Juegos y Entretenimientos"]/*,
  "Urbanismo y Obras",
  "Presupuesto y Gastos Municipales",
  "Exenciones y Beneficios Fiscales",
  "Educación y Acción Comunitaria",
  "Tránsito y Transporte",
  "Documentación y Habilitaciones Comerciales",
  "Personal Municipal",
  "Donaciones y Colaboraciones",
  "Régimen Impositivo",
  "Control y Regulación Comercial",
  "Seguridad y Orden Público",
  "Procedimientos Administrativos",
  "Gestión de Residuos",
  "Servicios de Alumbrado Público",
  "Higiene y Seguridad en Establecimientos Comerciales",
  "Servicios Sanitarios",
  "Uso del Suelo y Desarrollo Urbano",
  "Concesiones y Servicios Públicos Esenciales",
  "Promoción Social y Comunitaria",
  "Cultura y Patrimonio Local",
  "Movilidad y Transporte Público",
  "Gestión de Deportes y Recreación",
  "Administración de Personal y Escala Salarial",
  "Gestión Cemeterial y Servicios Funerarios",
  "Viveros Municipales y Distribución de Plantas",
  "Contratos, Convenios y Locaciones de Servicios",
  "Gestión del Patrimonio Histórico y Cultural",
  "Fomento y Desarrollo Económico Local",
  "Gestión Ambiental y Sustentabilidad"
]*/

    // 3. Texto procesado y enfocado
    const text = `

VISTO, el expediente nº 315/2016, iniciado por el Departamento Ejecutivo, mediante el expediente nº 5258/2016, quién eleva Decreto nº 1736/2016, ad referéndum del Honorable Cuerpo,  autorizando la firma de un contrato con la firma GRID IT SEVEN S.A., a fin de formalizar la prestación del servicio de implantación del cálculo automatizado de la tasa de […]
VISTO, el expediente nº 315/2016, iniciado por el Departamento Ejecutivo, mediante el expediente nº 5258/2016, quién eleva Decreto nº 1736/2016, ad referéndum del Honorable Cuerpo,  autorizando la firma de un contrato con la firma GRID IT SEVEN S.A., a fin de formalizar la prestación del servicio de implantación del cálculo automatizado de la tasa de Red Vial al sistema Rafam;
que, el expediente 5258-D-2016 y lo solicitado por el Director de Ingreso Público, donde requiere autorización para suscribir un convenio para la migración de la tasa de Red Vial al sistema informático RAFAM, con la firma GRID IT SEVEN S.A.;
que, el sistema RAFAM fué desarrollado por el Ministerio de Economía de la Provincia de Buenos Aires e implementado por este Municipio;
que, el Municipio no cuenta con personal para la asistencia diaria en las dificultades que se presentan en la utilización del sistema informático y software provisto por la Provincia de Buenos Aires;
que, resulta necesario contratar asistencia para la tarea de implantación del cálculo automatizado de la tasa de Red Vial en el sistema informático RAFAM;
que, dicha contratación debe ser autorizada por el Honorable Concejo Deliberante;
que, dada la premura que merece la contratación del servicio mencionado, resulta necesario autorizar la suscripción del contrato mediante el dictado de un decreto del Departamento Ejecutivo ad referéndum del Honorable Concejo Deliberante, y
CONSIDERANDO que en la Décima Tercera Sesión Ordinaria, llevada a cabo el día 11 de octubre de 2016, este Honorable Cuerpo aprobó por unanimidad el despacho de la Comisión de Presupuesto y Hacienda, que aconseja aprobar dicho contrato;
por todo ello, el HONORABLE CONCEJO DELIBERANTE DE SALADILLO, en uso de sus atribuciones, acuerda y sanciona la siguiente
O R D E N A N Z A
ARTICULO 1º: Autorízase la suscripción de un contrato entre la Municipalidad de Saladillo y la firma GRID IT SEVEN S.A. a los fines de formalizar la prestación del servicio de implantación del cálculo automatizado de la tasa de Red Vial al sistema RAFAM desarrollado por el Ministerio de Economía de la Provincia de Buenos Aires.-
ARTICULO 2º: Comuníquese al Departamento Ejecutivo Municipal, dése al Registro Oficial, cúmplase, publíquese y archívese.-
DADO EN LA SALA DE SESIONES DEL HOMORABLE CONCEJO DELIBERANTE DE SALADILLO, a los once días del mes de octubre del año dos mil dieciséis.-
ORDENANZA Nº 60/2016.- 
    `;
 const MODEL_SUMMARY = 'jdp8/distilbert-nsfw-text-classifier';
    //const classifier = await pipeline('zero-shot-classification', MODEL);
        const summarizer = await pipeline('summarization', MODEL_SUMMARY, {
        max_length: 150,  // Longitud del resumen
        min_length: 50,
        num_beams: 4,     // Mejor calidad que greedy search
        repetition_penalty: 2.0  // Evita repeticiones
    });
    const resumen = await summarizer(text)
    console.log(resumen)
    // 4. Configuración especializada
    const result = await classifier(resumen, labels, {
        multi_label: true,
        hypothesis_template: "El documento legal trata sobre {}",
        temperature: 0.3  // Reduce aleatoriedad
    });

    // 5. Procesamiento avanzado de resultados
    const minScore = 1/labels.length + 0.15; // Umbral dinámico
    const processed = labels
        .map((label, i) => ({
            label: label.split(' ')[0], // Simplifica para visualización
            fullLabel: label,
            score: result.scores[i],
            normalized: (result.scores[i] - 1/labels.length) * labels.length
        }))
        .filter(x => x.normalized > minScore)
        .sort((a, b) => b.normalized - a.normalized);

    console.log("RESULTADOS MEJORADOS:");
    console.log(processed);
    
    return processed;
}

classifyOrdinance();