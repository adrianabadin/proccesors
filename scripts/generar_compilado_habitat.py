"""
Genera documento Word: Compilado Hábitat, Vivienda y Desarrollo Urbano
Municipalidad de Saladillo
"""

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
import datetime

# ── Datos de ordenanzas (obtenidos via MCP) ──────────────────────────────────

SECCIONES = [
    {
        "titulo": "Sección 1: Marco Normativo General",
        "ordenanzas": [
            {
                "numero": "38/2015", "anio": 2015,
                "titulo": "Adhesión a la Ley Provincial 14.449 de Acceso Justo al Hábitat",
                "estado": "vigente",
                "resumen": "Adhiere a la Ley Provincial 14.449 de Acceso Justo al Hábitat, incorporando su marco normativo al ordenamiento jurídico municipal.",
                "articulos": [
                    {"nro": "1", "texto": "Adhiérase a la Ley Provincial N° 14.449 de Acceso Justo al Hábitat."},
                    {"nro": "2", "texto": "Publíquese el texto completo de la Ley Provincial N° 14.449 en el Boletín Oficial Municipal."},
                    {"nro": "3", "texto": "Archívese copia de la presente Ordenanza y de la Ley Provincial N° 14.449 en las dependencias municipales correspondientes."},
                    {"nro": "4", "texto": "Comuníquese, publíquese, dése al Registro Municipal y archívese."},
                ],
            },
            {
                "numero": "97/2019", "anio": 2019,
                "titulo": "Código de Ordenamiento Urbano",
                "estado": "vigente",
                "resumen": "Aprueba el Código de Ordenamiento Urbano de la ciudad de Saladillo, estableciendo la normativa integral para la regulación del desarrollo urbano, uso del suelo, subdivisión, morfología, infraestructura y condiciones ambientales.",
                "articulos": [
                    {"nro": "1", "texto": "Apruébase el Código de Ordenamiento Urbano de la ciudad de Saladillo, que consta de Cuerpo Normativo, Anexo de Zonificación y Anexo de Planos, los que forman parte integrante de la presente Ordenanza."},
                ],
            },
            {
                "numero": "19/2019", "anio": 2019,
                "titulo": "Parcelamiento y apertura de calles",
                "estado": "vigente",
                "resumen": "Establece el procedimiento y las condiciones para la aprobación de operaciones de parcelamiento y apertura de calles en el partido de Saladillo.",
                "articulos": [
                    {"nro": "1", "texto": "Establécese el siguiente procedimiento y condiciones para la aprobación de operaciones de parcelamiento y apertura de calles en el partido de Saladillo."},
                ],
            },
        ],
    },
    {
        "titulo": "Sección 2: Institucionalidad y Fondos",
        "ordenanzas": [
            {
                "numero": "19/2007", "anio": 2007,
                "titulo": "Creación del Consejo Municipal de la Vivienda",
                "estado": "vigente",
                "resumen": "Crea el Consejo Municipal de la Vivienda como ámbito de participación para abordar la problemática habitacional, con representación del gobierno, concejales, entidades profesionales, gremiales y cooperativas.",
                "articulos": [
                    {"nro": "1", "texto": "Créase en el Partido de Saladillo el CONSEJO MUNICIPAL DE LA VIVIENDA.-"},
                    {"nro": "2", "texto": "El Consejo Municipal de la Vivienda estará integrado de la siguiente forma: a) Intendente Municipal o quien lo represente que haga las veces de presidente.-b) Un funcionario de la Secretaría de Obras y Servicios Públicos.-c) Un Concejal por cada Bloque Político del Honorable Concejo Deliberante de Saladillo.-d) Un funcionario del área de Presupuesto y Hacienda.-e) Un representante de la Cámara de Comercio, Propiedad e Industria de Saladillo.-f) Un representante de la C.G.T. local.-g) Un representante por cada Cooperativa de Viviendas de constitución formal, en funcionamiento en el Distrito de Saladillo.-h) Un representante del Colegio de Arquitectos, un representante del Colegio de Ingenieros y un representante del Colegio de Martilleros.-"},
                    {"nro": "3", "texto": "Serán funciones del Consejo Municipal de la Vivienda: a) Evaluar y proyectar el crecimiento urbanístico de la ciudad de Saladillo y de las localidades del interior del Partido de Saladillo.-b) En función del planeamiento efectuado proponer la creación del Banco de Tierra para la construcción de la vivienda única, permanente familiar en el distrito de Saladillo, de acuerdo al presupuesto asignado por el Ejecutivo Municipal.-c) Colaborará con el Ejecutivo con la confección de un censo para producir un correcto dictamen de la situación habitacional en el Partido de Saladillo.-d) Evaluar y dar a conocer a la población los planes de viviendas nacionales, provinciales y municipales en vigencia.-e) Seleccionar de acuerdo a las posibilidades económico sociales de los distintos grupos solicitantes los planes acordes a cada sector.-f) Asesorar a los grupos de vecinos sobre los planes más convenientes.-g) Promocionar por todos los medios públicos y privados planes, programas y licitaciones.-h) Evaluar y orientar en las formas de ejecución de las obras.-i) Evaluar los procesos licitatorios y orientar en sus ajustes.-j) Evaluar y orientar en los procesos adjudicatarios a las familias, grupos corporativos, gremios, cámaras.-k) Realizar informes evaluativos y elevar a las autoridades competentes nacionales, provinciales y municipales.-l) Realizar el seguimiento del proceso de construcción de los distintos planes y programas.-m) Promover el relevamiento y regularización en los distintos barrios existentes construidos por el estado.-n) Promover la organización de consorcio de copropietarios para mantener la habitabilidad, la salubridad y el confort.-"},
                    {"nro": "4", "texto": "El presente Consejo se dictará su propio Estatuto de Funcionamiento de acuerdo con las leyes nacionales, provinciales y municipales.-"},
                    {"nro": "5", "texto": "Comuníquese al Departamento Ejecutivo, dése al Registro Oficial, cúmplase, publíquese y archívese.-"},
                ],
            },
            {
                "numero": "39/1990", "anio": 1990,
                "titulo": "Creación del Fondo Municipal de la Vivienda",
                "estado": "vigente",
                "resumen": "Autoriza la creación del Fondo Municipal de la Vivienda, integrado por las recaudaciones de los planes de vivienda ejecutados en el partido donde la Municipalidad asume el cobro. El fondo se destinará a la concreción de nuevos planes de vivienda social.",
                "articulos": [
                    {"nro": "1", "texto": "Autorízase al Departamento Ejecutivo a crear el Fondo Municipal de la Vivienda, que estará integrado por las recaudaciones de los diferentes planes de viviendas ejecutadas en el Partido de Saladillo, en donde la Municipalidad local asume el compromiso del cobro de las mismas.-"},
                    {"nro": "2", "texto": "Autorízase al Departamento Ejecutivo a utilizar dichos fondos para la concreción de nuevos Planes de Viviendas de interés social, los que a su vez pasarán a formar parte del Fondo Municipal de la Vivienda.-"},
                    {"nro": "3", "texto": "Comuníquese al Departamento Ejecutivo, dése al Registro Oficial, cúmplase, publíquese y archívese.-"},
                ],
            },
            {
                "numero": "1/2014", "anio": 2014,
                "titulo": "Creación del Fondo Solidario de Tierras e Infraestructura Urbana",
                "estado": "vigente",
                "resumen": "Crea el Fondo Solidario de Tierras e Infraestructura Urbana, destinado a financiar la generación de suelo urbano e infraestructura para vivienda social. Establece un Ente Supervisor y Regulador.",
                "articulos": [
                    {"nro": "1", "texto": "Créase el Fondo Solidario de Tierras e Infraestructura Urbana, el cual se conformará con el producido de la venta de los inmuebles fiscales, fondos nacionales, provinciales y/o municipales y donaciones de terceros, cuyo destino sea únicamente a la generación de suelo urbano e infraestructura, para el destino de vivienda única, familiar, social y permanente.-"},
                    {"nro": "2", "texto": "Créase un Ente Supervisor y Regulador del Fondo Solidario de Tierras e Infraestructura Urbana, el cual estará integrado por un miembro de cada Bloque Político que compone el Honorable Concejo Deliberante, el Presidente del Cuerpo y dos Representantes del Departamento Ejecutivo Municipal pertenecientes a las áreas de Desarrollo Humano y de Obras y Servicios Públicos con injerencia en planificación urbana.-"},
                    {"nro": "3", "texto": "El dinero que se recaude por el Fondo Solidario de Tierras e Infraestructura Urbana será administrado por el Departamento Ejecutivo Municipal y el Ente Supervisor y Regulador del Fondo Solidario de Tierras e Infraestructura Urbana.-"},
                    {"nro": "4", "texto": "Facúltese al Ente Supervisor y Regulador del Fondo Solidario de Tierras e Infraestructura Urbana, a definir el porcentaje de suelo urbano destinado a planes de vivienda única, familiar, social y permanente con recupero y que porcentaje se destinará a otros planes.-"},
                    {"nro": "5", "texto": "Comuníquese al Departamento Ejecutivo, dése al Registro Oficial, cúmplase, publíquese y archívese.-"},
                ],
            },
            {
                "numero": "124/2022", "anio": 2022,
                "titulo": "Contribución Obligatoria sobre la Valorización Inmobiliaria (COVI)",
                "estado": "vigente",
                "resumen": "Regula la participación municipal en las valorizaciones inmobiliarias generadas por acciones del Estado, en el marco de la Ley 14.449. Establece la COVI como instrumento de captación de plusvalías para financiar el desarrollo urbano.",
                "articulos": [
                    {"nro": "1", "texto": "Se entiende por valorización inmobiliaria a todo incremento del valor de un inmueble generado por acciones del Estado, ajenas a las intervenciones del propietario y, por lo tanto, susceptibles de ser recuperados públicamente."},
                    {"nro": "2", "texto": "Las contribuciones obligatorias son las imposiciones tributarias establecidas a fin de recuperar las valorizaciones inmobiliarias generadas, o partes de ellas. Las mismas son de carácter complementario a otras exigencias urbanísticas, y por lo tanto adicionales a las cesiones establecidas en el art. 56° del DL 8912/77."},
                    {"nro": "5", "texto": "Se designa como Autoridad de Aplicación a la Dirección de Planeamiento, Tierra y Vivienda, quien llevará adelante el procedimiento administrativo de determinación de la COVI."},
                    {"nro": "9", "texto": "Las parcelas o unidades edificadas que reciba el municipio como contribución serán asignadas al Banco Municipal de Tierras. Cuando no exista la posibilidad de compensación material, la contribución económica será asignada al Fondo Municipal de Desarrollo Urbano."},
                ],
            },
            {
                "numero": "52/2024", "anio": 2024,
                "titulo": "Programa FO.MU.VI.DU. - Fondo Municipal de Vivienda y Desarrollo Urbano",
                "estado": "vigente",
                "resumen": "Crea el Programa de Promoción y Recupero por la Construcción de Viviendas Sociales, Entrega de Lotes de Terrenos y Mejoramiento Habitacional, y el Fondo Municipal de Vivienda y Desarrollo Urbano (FO.MU.VI.D.U.). Deroga la Ordenanza 39/1990.",
                "articulos": [
                    {"nro": "1", "texto": "Crear el Programa de Promoción y Recupero por la Construcción de Viviendas Sociales, Entrega de Lotes de Terrenos y Mejoramiento Habitacional, construido, financiado y/o administrado por la Municipalidad de Saladillo."},
                    {"nro": "2", "texto": "Crear el Fondo Municipal de Vivienda y Desarrollo Urbano (FO.MU.VI.D.U.), cuyo objetivo prioritario será el diseño, la definición e implementación de políticas y estrategias tendientes al mejoramiento de la situación habitacional de la ciudad."},
                    {"nro": "5", "texto": "Todas las viviendas que se financien a través del FO.MU.VI.D.U. deberán estar destinadas exclusivamente al uso de vivienda única, estable y permanente del grupo familiar."},
                    {"nro": "9", "texto": "Crear el Banco Municipal de Tierras que estará integrado por los inmuebles que actualmente son propiedad municipal y aquellos que se reciban o adquieran con el objeto de construir una reserva de tierras destinadas a los fines del FO.MU.VI.D.U."},
                    {"nro": "14", "texto": "Derogar la Ordenanza N° 39/1990, su Decreto Reglamentario 890/2011 y toda norma que se oponga a la presente."},
                ],
            },
        ],
    },
    {
        "titulo": "Sección 3: Planes y Programas de Vivienda",
        "ordenanzas": [
            {
                "numero": "1/2007", "anio": 2007,
                "titulo": "Plan Federal de Viviendas (146 viviendas) y Sindicato de Salud (20 viviendas)",
                "estado": "vigente",
                "resumen": "Declara de interés municipal la construcción de 146 viviendas del Plan Federal del Gobierno Nacional y 20 viviendas del Sindicato de Salud Pública en distintas localidades del partido. Establece indicadores urbanísticos y servicios básicos.",
                "articulos": [
                    {"nro": "1", "texto": "Declárese de Interés Municipal la construcción de 146 viviendas en el Partido de Saladillo en el marco del Plan Federal de Construcción de Viviendas del Gobierno Nacional según el siguiente detalle: a) 90 viviendas en la ciudad de Saladillo; b) 44 viviendas en Del Carril; c) 8 viviendas en Polvaredas; d) 4 viviendas en Alvarez de Toledo."},
                    {"nro": "2", "texto": "Declárese de Interés Municipal la construcción de 20 viviendas en la ciudad de Saladillo a través del Sindicato de Salud Pública de la Provincia de Buenos Aires en terrenos donados por el Municipio."},
                    {"nro": "3", "texto": "Considérese a los barrios mencionados como CONJUNTOS INTEGRALES DE VIVIENDAS en el marco de lo establecido en el artículo 52 de la ley 8912."},
                    {"nro": "4", "texto": "Defínanse para estos barrios los siguientes indicadores urbanísticos: Plan Federal Saladillo: Densidad=150 hab/hect, FOS=0.5, FOT=0.8, Frente mínimo=12 mts, Superficie=300 m2 mínimo. Del Carril: Densidad=130, FOS=0.5, FOT=0.8, Frente=10 mts, Sup=400 m2. Polvaredas: Densidad=60, FOS=0.5, FOT=0.8, Frente=15 mts, Sup=250 m2. Alvarez de Toledo: Densidad=60, FOS=0.5, FOT=0.8, Frente=15 mts, Sup=500 m2. Sindicato de Salud: Densidad=150, FOS=0.5, FOT=0.8, Frente=13 mts, Sup=300 m2."},
                    {"nro": "5", "texto": "Establécese los servicios: Saladillo y Sindicato: Agua Corriente, Energía Eléctrica, Red Cloacal y Alumbrado Público. Del Carril: Agua Corriente, Energía Eléctrica y Alumbrado Público. Polvaredas y Alvarez de Toledo: Agua Potable, Energía Eléctrica y Alumbrado Público."},
                ],
            },
            {
                "numero": "68/1986", "anio": 1986,
                "titulo": "Conjunto habitacional multifamiliar",
                "estado": "vigente",
                "resumen": "Destina un sector a la implantación de un conjunto habitacional multifamiliar con indicadores urbanísticos específicos.",
                "articulos": [
                    {"nro": "2", "texto": "El mencionado sector se destinará a la implantación de un conjunto habitacional con los siguientes indicadores urbanísticos: a) Usos: Residencial multifamiliar y complementarios.-b) Densidad neta: 500 hab/ha.-c) FOS: 0.5.-d) FOT: 0.8.-e) Servicios esenciales: agua corriente, cloacas, pavimento energía domiciliaria y alumbrado público.-"},
                ],
            },
            {
                "numero": "49/1994", "anio": 1994,
                "titulo": "Plan Integral de Viviendas - Cooperativa Esperanza (200 viviendas)",
                "estado": "vigente",
                "resumen": "Desafecta una parcela del área complementaria y la incorpora al área urbana para permitir la construcción de 200 viviendas del Plan Solidaridad por la Cooperativa de Viviendas 'Esperanza'.",
                "articulos": [
                    {"nro": "1", "texto": "Desaféctase del área complementaria de Saladillo la fracción de Terreno denominada catastralmente como Circunscripción I; Sección M; Chacra: 335; Fracción I; Parcela: 1.-"},
                    {"nro": "2", "texto": "Incorpórase al área urbana de Saladillo los bienes mencionados en el artículo 1º.-"},
                    {"nro": "3", "texto": "Las tierras desafectadas integran el SASU con los indicadores urbanísticos del mismo: Densidad 150 habitantes por hectáreas – F.O.S. 0,5 – F.O.T.: 0,8. Las dimensiones mínimas de las parcelas contemplarán lo establecido por el artículo 54º de la Ley 8912, por tratarse de un Plan Integral de Viviendas.-"},
                    {"nro": "4", "texto": "Establécese como servicios esenciales para el sector: 1.- Agua Corriente.- 2.- Energía Eléctrica.-"},
                ],
            },
            {
                "numero": "4/2022", "anio": 2022,
                "titulo": "Convenio Instituto de Vivienda - 13 viviendas",
                "estado": "vigente",
                "resumen": "Aprueba el convenio con el Instituto de Vivienda de la Provincia de Buenos Aires para asistencia financiera de $68.036.468,88 para la construcción de 13 viviendas.",
                "articulos": [
                    {"nro": "1", "texto": "Aprobar el Convenio suscripto entre el Instituto de la Vivienda de la Provincia de Buenos Aires y la Municipalidad de Saladillo con fecha 9 de febrero de 2022, sobre asistencia financiera para la construcción de 13 viviendas por un monto total de $68.036.468,88 (723.968,23 UVLs)."},
                    {"nro": "2", "texto": "Autorizar al Departamento Ejecutivo Municipal a suscribir Anexos, Actas y/o Acuerdos Complementarios que fueran necesarias para cumplir con el objeto del convenio."},
                ],
            },
            {
                "numero": "71/1986", "anio": 1986,
                "titulo": "Convenio autoconstrucción - 20 viviendas en Cazón y Del Carril",
                "estado": "vigente",
                "resumen": "Autoriza la suscripción de un convenio con el Instituto Provincial de la Vivienda para construir 20 viviendas por el sistema de autoconstrucción en Cazón y Del Carril.",
                "articulos": [
                    {"nro": "1", "texto": "Autorízase al Departamento Ejecutivo la suscripción de un Convenio con el Instituto Provincial de la Vivienda a los efectos de construir veinte unidades de viviendas por el Sistema de auto construcción, a erigirse en las localidades de Cazón y Del Carril, en un todo de acuerdo a la Resolución 1519/85 del citado Instituto."},
                ],
            },
        ],
    },
    {
        "titulo": "Sección 4: Consorcios Urbanísticos",
        "ordenanzas": [
            {
                "numero": "93/2021", "anio": 2021,
                "titulo": "Consorcio Urbanístico La Nueva Era / La Unión",
                "estado": "vigente",
                "resumen": "Aprueba el Convenio de Consorcio Urbanístico con los fideicomisos inmobiliarios 'La Nueva Era' y 'La Unión' para un proyecto de urbanización en dos inmuebles, en el marco de la Ley 14.449.",
                "articulos": [
                    {"nro": "1", "texto": "Aprobar el Convenio de Consorcio Urbanístico suscripto con fecha 13 de septiembre de 2021, en el marco de la Ley N° 14.449, entre la Municipalidad de Saladillo y Los Fideicomisos Inmobiliarios 'La Nueva Era' y 'La Unión', para la ejecución de un proyecto de urbanización en Circunscripción I, Sección E, Chacra 102."},
                ],
            },
            {
                "numero": "146/2017", "anio": 2017,
                "titulo": "Consorcio Urbanístico Paglione",
                "estado": "vigente",
                "resumen": "Aprueba el Convenio de Consorcio Urbanístico con Juan Ramón Paglione para un proyecto de urbanización en Av. Dellatorre, en el marco de la Ley 14.449.",
                "articulos": [
                    {"nro": "1", "texto": "Apruébase el Convenio de Consorcio Urbanístico suscripto con fecha 23 de agosto de 2017, en el marco de la Ley Nº14.449, entre la Municipalidad de Saladillo y el Señor Juan Ramón Paglione, para la ejecución de un proyecto de urbanización en el inmueble sito en Av. J. C. Dellatorre entre las calles Armendáriz y calle vecinal."},
                ],
            },
            {
                "numero": "10/2016", "anio": 2016,
                "titulo": "Sector de Urbanización Especial - Barrio Los Troncos",
                "estado": "vigente",
                "resumen": "Crea un Sector de Urbanización Especial (SUE) en el área Complementaria para regular la subdivisión de parcelas irregulares en el Barrio Los Troncos.",
                "articulos": [
                    {"nro": "1", "texto": "Créase el Sector de Urbanización Especial -SUE- en el área Complementaria de la ciudad de Saladillo, en el Barrio Los Troncos."},
                    {"nro": "2", "texto": "Establécese para el mencionado sector las siguientes dimensiones mínimas parcelarias: Ancho mínimo: 12 m. Superficie mínima: 300 m2."},
                    {"nro": "3", "texto": "Establécese para el mencionado sector los siguientes indicadores urbanísticos: a – Usos: Residencial. b – Densidad neta: 150 hab/há. c – FOS: 0.5 d – FOT: 0.8 e – IP: 0.3 f – Altura máxima: 6 m."},
                ],
            },
        ],
    },
    {
        "titulo": "Sección 5: Regularización de Obras y Transferencias",
        "ordenanzas": [
            {
                "numero": "91/1990", "anio": 1990,
                "titulo": "Regularización de viviendas y obras sin planos",
                "estado": "vigente",
                "resumen": "Establece un régimen de regularización para viviendas y obras en construcción sin planos aprobados, con exenciones de pago y procedimientos simplificados.",
                "articulos": [
                    {"nro": "1", "texto": "Exímase durante todo el año 1991 del pago de derecho de Construcción y de la multa correspondiente a todos aquellos empadronamientos aprobados en dicho período."},
                    {"nro": "5", "texto": "Para las obras en construcción sin planos, se podrá empadronar el porcentaje de obra ejecutado, realizándose proyecto y dirección de la obra faltante."},
                    {"nro": "7", "texto": "Serán consideradas obras terminadas a empadronar todas aquellas que sean mínimamente habitadas o que superen el 80% ejecutado según planilla tipo."},
                    {"nro": "11", "texto": "Para los casos de viviendas única propiedad cuya superficie edificada exceda los cien metros cuadrados y donde el estudio social determine la falta de capacidad de pago, la Secretaría de Obras podrá confeccionarle los planos. El propietario abonará el 0.5% del valor de la obra en hasta seis cuotas."},
                ],
            },
            {
                "numero": "5/1992", "anio": 1992,
                "titulo": "Regularización de obras clandestinas",
                "estado": "vigente",
                "resumen": "Establece el régimen de regularización de obras clandestinas, definiendo procedimientos para detección, paralización, empadronamiento y liquidación de derechos diferenciados.",
                "articulos": [
                    {"nro": "1", "texto": "Será considerada 'Obra Clandestina' aquella obra en ejecución o ejecutada que no cumpla con lo establecido en el Código de Construcción en lo referente a tramitaciones para obtener los permisos correspondientes."},
                    {"nro": "5", "texto": "Serán considerados obras a empadronar aquellas obras ejecutadas o en ejecución que están en condiciones mínimas de habitabilidad y/o que superen el 80% ejecutado según planilla tipo."},
                    {"nro": "9", "texto": "Para viviendas única propiedad de hasta 100 m2 donde el estudio social determine falta de capacidad de pago, la Dirección de Obras podrá confeccionarle los planos. El propietario abonará el 0.5% del valor de la obra en hasta seis cuotas. Los indigentes podrán solicitar el plano sin cargo."},
                    {"nro": "14", "texto": "Derechos diferenciados: Obras a construir: 50%. Detectadas por D.O.P.: 100%. Presentación espontánea: 100%. Detectadas sin presentación: 200%. Obras con más de 10 años: eximidas."},
                ],
            },
            {
                "numero": "99/2021", "anio": 2021,
                "titulo": "Venta Plan Familia Propietaria (ejemplo)",
                "estado": "vigente",
                "resumen": "Aprueba la venta de un inmueble municipal a Juan Carlos Fredes en el marco del Plan Familia Propietaria. Declara de interés social la escrituración.",
                "articulos": [
                    {"nro": "1", "texto": "Aprobar la venta del inmueble designado catastralmente como Circunscripción I, Sección M, Chacra 336, Manzana 336g, Parcela 02, efectuada por la Municipalidad de Saladillo en el marco del Plan Familia Propietaria a favor de Juan Carlos Fredes."},
                    {"nro": "2", "texto": "Declarar de interés social la escrituración del inmueble a favor de Juan Carlos Fredes, requiriendo la intervención de la Escribanía General de Gobierno de la Provincia de Buenos Aires."},
                ],
            },
        ],
    },
]


def generar_documento():
    doc = Document()

    # ── Estilos ──────────────────────────────────────────────────────────
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(11)

    # ── Portada ──────────────────────────────────────────────────────────
    for _ in range(6):
        doc.add_paragraph()

    titulo = doc.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = titulo.add_run("COMPILADO DE ORDENANZAS MUNICIPALES")
    run.bold = True
    run.font.size = Pt(24)
    run.font.color.rgb = RGBColor(0, 51, 102)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sub.add_run("Hábitat, Vivienda y Desarrollo Urbano")
    run.bold = True
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(0, 102, 153)

    doc.add_paragraph()

    mun = doc.add_paragraph()
    mun.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = mun.add_run("Municipalidad de Saladillo")
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(100, 100, 100)

    prov = doc.add_paragraph()
    prov.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = prov.add_run("Provincia de Buenos Aires - Argentina")
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(100, 100, 100)

    doc.add_paragraph()

    fecha = doc.add_paragraph()
    fecha.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fecha.add_run(f"Mayo 2026")
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(100, 100, 100)

    doc.add_page_break()

    # ── Nota metodológica ────────────────────────────────────────────────
    doc.add_heading("Nota Metodológica", level=1)
    nota = doc.add_paragraph()
    nota.add_run(
        "El presente compilado reúne ordenanzas municipales del Partido de Saladillo "
        "relacionadas con hábitat, vivienda y desarrollo urbano. Las ordenanzas fueron "
        "identificadas mediante búsquedas semánticas, full-text y por categoría en la "
        "base de datos del proyecto de sistematización de ordenanzas municipales."
    )
    doc.add_paragraph()
    nota2 = doc.add_paragraph()
    nota2.add_run(
        "Criterio de inclusión: ").bold = True
    nota2.add_run(
        "Solo se incluyen ordenanzas con estado 'vigente' o 'modificada' según "
        "el registro municipal. Se priorizó el marco normativo/programático sobre "
        "las transferencias individuales de inmuebles, incluyendo estas últimas "
        "solo a modo de ejemplo representativo."
    )
    doc.add_paragraph()
    nota3 = doc.add_paragraph()
    nota3.add_run(
        "Fuentes: ").bold = True
    nota3.add_run(
        "MCP Ordenanzas Saladillo (búsqueda semántica con embeddings text-embedding-3-large, "
        "búsqueda full-text PostgreSQL, filtrado por categoría). "
        "Ordenanzas obtenidas vía herramienta get_ordenanza con validación de vigencia."
    )

    doc.add_page_break()

    # ── Índice de Ordenanzas ─────────────────────────────────────────────
    doc.add_heading("Índice de Ordenanzas", level=1)

    # Contar total
    total = sum(len(s["ordenanzas"]) for s in SECCIONES)

    # Tabla índice
    table = doc.add_table(rows=1, cols=5)
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    hdr = table.rows[0].cells
    hdr[0].text = "N°"
    hdr[1].text = "Ordenanza"
    hdr[2].text = "Año"
    hdr[3].text = "Título"
    hdr[4].text = "Estado"

    for cell in hdr:
        for p in cell.paragraphs:
            p.runs[0].bold = True
            p.runs[0].font.size = Pt(9)

    idx = 1
    for seccion in SECCIONES:
        for ord_data in seccion["ordenanzas"]:
            row = table.add_row().cells
            row[0].text = str(idx)
            row[1].text = f"N° {ord_data['numero']}"
            row[2].text = str(ord_data["anio"])
            row[3].text = ord_data["titulo"]
            row[4].text = ord_data["estado"].capitalize()
            for cell in row:
                for p in cell.paragraphs:
                    for r in p.runs:
                        r.font.size = Pt(8)
            idx += 1

    doc.add_paragraph()
    resumen_idx = doc.add_paragraph()
    resumen_idx.add_run(f"Total de ordenanzas compiladas: {total}").bold = True

    doc.add_page_break()

    # ── Secciones con artículos ──────────────────────────────────────────
    for seccion in SECCIONES:
        doc.add_heading(seccion["titulo"], level=1)

        for ord_data in seccion["ordenanzas"]:
            # Encabezado ordenanza
            h2 = doc.add_heading(
                f"Ordenanza N° {ord_data['numero']} ({ord_data['anio']})", level=2
            )

            # Título
            p_tit = doc.add_paragraph()
            run_tit = p_tit.add_run(ord_data["titulo"])
            run_tit.bold = True
            run_tit.font.size = Pt(12)

            # Estado
            p_est = doc.add_paragraph()
            run_est = p_est.add_run(f"Estado: {ord_data['estado'].capitalize()}")
            run_est.font.color.rgb = RGBColor(0, 128, 0) if ord_data["estado"] == "vigente" else RGBColor(200, 150, 0)
            run_est.bold = True

            # Resumen
            p_res = doc.add_paragraph()
            p_res.add_run("Resumen: ").bold = True
            p_res.add_run(ord_data["resumen"])

            doc.add_paragraph()

            # Artículos
            doc.add_heading("Artículos", level=3)
            for art in ord_data["articulos"]:
                p_art = doc.add_paragraph()
                p_art.paragraph_format.left_indent = Cm(1)
                run_nro = p_art.add_run(f"Artículo {art['nro']}: ")
                run_nro.bold = True
                run_nro.font.size = Pt(10)
                run_txt = p_art.add_run(art["texto"])
                run_txt.font.size = Pt(10)

            doc.add_paragraph()
            # Separador
            p_sep = doc.add_paragraph()
            p_sep.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run_sep = p_sep.add_run("— ◆ —")
            run_sep.font.color.rgb = RGBColor(180, 180, 180)
            doc.add_paragraph()

    # ── Anexo ────────────────────────────────────────────────────────────
    doc.add_page_break()
    doc.add_heading("Anexo: Fuentes y Metodología", level=1)

    p1 = doc.add_paragraph()
    p1.add_run("Base de datos: ").bold = True
    p1.add_run("Proyecto de sistematización de ordenanzas municipales de Saladillo.")

    p2 = doc.add_paragraph()
    p2.add_run("Búsquedas realizadas:\n").bold = True
    p2.add_run("• Semantic search: 'hábitat vivienda desarrollo urbano planes de vivienda'\n")
    p2.add_run("• Full-text search: 'hábitat vivienda desarrollo urbano'\n")
    p2.add_run("• Category search: 'vivienda-social', 'urbanismo-suelo'")

    p3 = doc.add_paragraph()
    p3.add_run("Modelo de embeddings: ").bold = True
    p3.add_run("text-embedding-3-large (OpenAI)")

    p4 = doc.add_paragraph()
    p4.add_run("Herramientas MCP utilizadas:\n").bold = True
    p4.add_run("• ordenanzas-saladillo_full_semantic_search\n")
    p4.add_run("• ordenanzas-saladillo_search_ordenanzas\n")
    p4.add_run("• ordenanzas-saladillo_search_by_category\n")
    p4.add_run("• ordenanzas-saladillo_get_ordenanza")

    p5 = doc.add_paragraph()
    p5.add_run("Fecha de generación: ").bold = True
    p5.add_run(datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))

    p6 = doc.add_paragraph()
    p6.add_run("Generado con: ").bold = True
    p6.add_run("Python + python-docx")

    # ── Guardar ──────────────────────────────────────────────────────────
    output = "Compilado_Habitat_Vivienda_Desarrollo_Urbano.docx"
    doc.save(output)
    print(f"Documento generado: {output}")
    print(f"Total ordenanzas: {total}")


if __name__ == "__main__":
    generar_documento()
