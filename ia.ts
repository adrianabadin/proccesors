import {v4} from "uuid"
import {knex} from "knex"
import {pipeline} from "@xenova/transformers"
const BATCH_SIZE = 4; // Ajusta según tu GPU
const MODEL_SUMMARY = 'Xenova/distilbart-cnn-12-6';
const MODEL_CLASSIFICATION = 'Xenova/roberta-large-mnli';
async function getSomethingDone(){
const classificationPipe= await pipeline('zero-shot-classification', MODEL_CLASSIFICATION);
//const pipe=await pipeline('text-classification','Xenova/bert-base-multilingual-cased-finetuned-ner-ontonotes')
const labelsfor=[
  "Servicios Públicos",
  "Tasas y Tarifas",
  "Salud Pública",
  "Juegos y Entretenimientos",
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
]
const data =await classificationPipe(`
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
ORDENANZA Nº 60/2016.-`,labelsfor,{
        multi_label: true,
        hypothesis_template: "El documento legal trata sobre {}",
        temperature: 0.3  // Reduce aleatoriedad
    })
console.log(data);
//const sumary = await pipeline('summarization', MODEL_SUMMARY);
//const resumen =await sumary(data.sequence as any);
//console.log(resumen)
}
getSomethingDone()
interface Ordenanzas {
    id:string,
    title:string,
    original:string,
    sumary:string,
    classification:string
}
/*
const pg=knex({
  client: 'pg',
  connection: {

    host: "thecodersteam.com",
    port: 5432,
    user: "adrian",
    database: "ordenanzas",
    password: "!DarthHobbit%",
    ssl:  false ,
  },
})
async function AddRow (){
const data=await pg.table("ordenanzas").insert(
    {title:"Ordenanza N° 16/2025",
        original:"https://hcd.saladillo.gob.ar/ordenanza/ordenanza-n-16-2025/",
        sumary:"Texto de la ordenanza",
        classification:"General",id:v4()}).returning("*")
        console.log(data)
}
AddRow();
*/