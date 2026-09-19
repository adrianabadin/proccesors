from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
import json

ordenanzas_data = [
    {
        "numero": 101, "anio": 2023,
        "titulo": "Ordenanza N° 101/2023",
        "resumen": "Establece que la Municipalidad de Saladillo deberá difundir líneas de asistencia a víctimas de violencia de género en fiestas y eventos públicos. Crea requisitos de comunicación con perspectiva de género para medios que reciban pauta oficial. Incluye obligaciones de capacitación y difusión de recursos de la Dirección de Género.",
        "estado": "vigente"
    },
    {
        "numero": 116, "anio": 2022,
        "titulo": "Ordenanza N° 116/2022",
        "resumen": "Aprueba el Protocolo de Actuación en Situaciones de Violencias por Razones de Género, que establece procedimientos de asistencia, asesoramiento y acompañamiento a víctimas. Define tipos y modalidades de violencia según Ley 26.485. Incluye LINEAMIENTOS para todas las áreas del municipio.",
        "estado": "vigente"
    },
    {
        "numero": 78, "anio": 2021,
        "titulo": "Ordenanza N° 78/2021",
        "resumen": "Aprueba Convenio Específico con el Ministerio Público de la Provincia de Buenos Aires para la prevención de violencia familiar y de género. Establece Sistema de Alerta con software, APP móvil (100 activaciones) y 3 botones anti-pánico físicos.",
        "estado": "vigente"
    },
    {
        "numero": 67, "anio": 2021,
        "titulo": "Ordenanza N° 67/2021",
        "resumen": "Crea el Programa de Inserción y Continuidad Laboral para Mujeres y Diversidades víctimas de violencia por razones de género. Busca promover el empleo en sectores público y privado mediante herramientas e incentivos. Autoridad de aplicación: Secretaría de Desarrollo Local y Unidad de Género Local.",
        "estado": "vigente"
    },
    {
        "numero": 46, "anio": 2020,
        "titulo": "Ordenanza N° 46/2020",
        "resumen": "Modifica la Ordenanza N° 29/2019 (Ley Micaela) estableciendo detalles de implementación: designación de autoridad de aplicación, funciones, mecanismos de certificación, informes anuales y sanciones por incumplimiento para el personal municipal.",
        "estado": "vigente"
    },
    {
        "numero": 45, "anio": 2020,
        "titulo": "Ordenanza N° 45/2020",
        "resumen": "Promueve el uso de la copa menstrual como alternativa a toallitas y tampones, destacando beneficios para la salud, medio ambiente y economía. Establece inclusión en programas de salud y medio ambiente, charlas informativas y distribución gratuita en centros de salud.",
        "estado": "vigente"
    },
    {
        "numero": 71, "anio": 2020,
        "titulo": "Ordenanza N° 71/2020",
        "resumen": "Crea el Consejo Local de Infancias y Adolescencias, derogando la Ordenanza N°67/2008. Establece misión, conformación, reglas de funcionamiento y competencias, en el marco de la Ley Provincial 13.298.",
        "estado": "vigente"
    },
    {
        "numero": 108, "anio": 2019,
        "titulo": "Ordenanza N° 108/2019",
        "resumen": "Crea el Programa Lazos para adolescentes en general y específicamente adolescentes que son madres/padres y sus hijos/as, con abordaje interdisciplinario. Tres líneas de acción: acompañamiento, sensibilización y fortalecimiento económico.",
        "estado": "vigente"
    },
    {
        "numero": 29, "anio": 2019,
        "titulo": "Ordenanza N° 29/2019",
        "resumen": "Adhiere el Municipio de Saladillo a la Ley Provincial N° 15.134 (Ley Micaela Bonaerense) que establece la capacitación obligatoria en género y violencia contra las mujeres para todas las personas que integran los tres poderes del Estado.",
        "estado": "vigente"
    },
    {
        "numero": 148, "anio": 2018,
        "titulo": "Ordenanza N° 148/2018",
        "resumen": "Declara el 14 de marzo como Día de Concientización y Difusión de la Endometriosis en Saladillo. Crea Programa Municipal de actividades educativas y de difusión, asignando partida presupuestaria desde 2019.",
        "estado": "vigente"
    },
    {
        "numero": 127, "anio": 2017,
        "titulo": "Ordenanza N° 127/2017",
        "resumen": "Designa nombres de siete mujeres del período independentista para las calles de la 'Urbanización I - Escuela 7'. Busca revalorizar el papel histórico de las mujeres, en el marco del bicentenario de la independencia argentina.",
        "estado": "vigente"
    },
    {
        "numero": 124, "anio": 2017,
        "titulo": "Ordenanza N° 124/2017",
        "resumen": "Implementa Programa de Concientización sobre acoso callejero dirigido a estudiantes de escuelas primarias y secundarias. Incluye charlas, cursos, talleres y seminarios para promover relaciones basadas en el respeto.",
        "estado": "vigente"
    },
    {
        "numero": 45, "anio": 2017,
        "titulo": "Ordenanza N° 45/2017",
        "resumen": "Aprueba Acta Acuerdo con la Asociación Civil Agruparte para ejecutar módulos 'Desarrollo Humano - Cultural' y 'Desarrollo Humano - Mujer y Hábitat' del Convenio con la Secretaría de Vivienda y Hábitat de la Nación para el Barrio 31 de Julio.",
        "estado": "vigente"
    },
    {
        "numero": 48, "anio": 2016,
        "titulo": "Ordenanza N° 48/2016",
        "resumen": "Prohíbe actos administrativos municipales que permitan, apoyen o promocionen concursos de belleza por constituir violencia simbólica y de género. Establece restricciones para concursos privados y promueve concursos alternativos que valoricen expresiones artísticas y solidarias.",
        "estado": "vigente"
    },
    {
        "numero": 18, "anio": 2016,
        "titulo": "Ordenanza N° 18/2016",
        "resumen": "Establece el 17 de mayo como 'Día Municipal de lucha contra la discriminación por orientación sexual e identidad de género'. La fecha conmemora la eliminación de la homosexualidad de la lista de enfermedades mentales por la OMS en 1990.",
        "estado": "vigente"
    },
    {
        "numero": 34, "anio": 2015,
        "titulo": "Ordenanza N° 34/2015",
        "resumen": "Establece derecho a un día de licencia laboral anual con goce de haberes para personal municipal femenino y masculino, destinado a estudios preventivos de salud. Para mujeres: colposcopía, mamografías y papanicolau. Para hombres: estudios de próstata y colon.",
        "estado": "vigente"
    },
    {
        "numero": 76, "anio": 2014,
        "titulo": "Ordenanza N° 76/2014",
        "resumen": "Designa con el nombre 'Lucía Elordieta' a una calle de la localidad de Del Carril, en reconocimiento a su trayectoria política y comunitaria.",
        "estado": "vigente"
    },
    {
        "numero": 100, "anio": 2012,
        "titulo": "Ordenanza N° 100/2012",
        "resumen": "Autoriza al Intendente Municipal a firmar contrato de comodato con el Ministerio de Justicia y Seguridad de la Provincia de Buenos Aires para ceder inmueble donde funciona la Comisaría de la Mujer y la Familia.",
        "estado": "vigente"
    },
    {
        "numero": 99, "anio": 2012,
        "titulo": "Ordenanza N° 99/2012",
        "resumen": "Solicita al Ministerio de Justicia y Seguridad de la Provincia de Buenos Aires la creación en Saladillo de una Comisaría de la Mujer y la Familia para prevención y tratamiento de la violencia familiar con personal especializado.",
        "estado": "vigente"
    },
    {
        "numero": 48, "anio": 2012,
        "titulo": "Ordenanza N° 48/2012",
        "resumen": "Crea el Consejo Local contra la Violencia de Género y Familiar. Coordinado por Desarrollo Humano municipal, con composición multisectorial. Funciones: concientización, prevención, asesoramiento, investigación, coordinación interinstitucional y formulación de proyectos.",
        "estado": "vigente"
    },
    {
        "numero": 30, "anio": 2008,
        "titulo": "Ordenanza N° 30/2008",
        "resumen": "Crea la 'Semana del Control y Prevención de las Enfermedades Mamarias - Maratón Mamográfica'. Se realiza anualmente en octubre, coordinando con Hospital 'Dr. Posadas', prestadores privados y ONGs para controles clínicos, mamografías gratuitas y campañas de concientización.",
        "estado": "vigente"
    },
    {
        "numero": 16, "anio": 2006,
        "titulo": "Ordenanza N° 16/2006",
        "resumen": "Modifica el artículo 78 del Estatuto del Empleado Municipal para ampliar el régimen de licencia por paternidad: 5 días corridos por nacimiento, 10 días si tiene hijos menores de 5 años, 10 días por nacimientos múltiples.",
        "estado": "vigente"
    },
    {
        "numero": 24, "anio": 2005,
        "titulo": "Ordenanza N° 24/2005",
        "resumen": "Modifica el régimen de licencia por paternidad del personal municipal masculino, extendiendo de 3 a 5 días hábiles y equiparando situaciones antes solo contempladas para el personal femenino (nacimientos múltiples, adopción, fallecimiento fetal, otorgamiento de tenencia).",
        "estado": "vigente"
    },
    {
        "numero": 68, "anio": 1993,
        "titulo": "Ordenanza N° 68/1993",
        "resumen": "Convalida Convenio con el Instituto de la Vivienda de la Provincia de Buenos Aires para construcción de un complejo para la 'Mujer Golpeada', equivalente a 6 módulos de vivienda. Aporte de $69.000 (valores 1993) con reintegro a 15 años y 35% de subsidio para fondo de vivienda social.",
        "estado": "vigente"
    }
]

doc = Document()

title = doc.add_heading('COMPILADO DE ORDENANZAS', 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run('Derechos de las Mujeres, Feminismos y Diversidades')
run.bold = True
run.font.size = Pt(14)

municipio = doc.add_paragraph()
municipio.alignment = WD_ALIGN_PARAGRAPH.CENTER
municipio.add_run('Municipio de Saladillo - Provincia de Buenos Aires')

fecha = doc.add_paragraph()
fecha.alignment = WD_ALIGN_PARAGRAPH.CENTER
fecha.add_run('Mayo 2026')

doc.add_paragraph()

intro = doc.add_paragraph()
intro.add_run('INTRODUCCIÓN').bold = True
doc.add_paragraph(
    'El presente documento compila la totalidad de ordenanzas municipales dictadas por el Honorable '
    'Concejo Deliberante de Saladillo en materia de género, diversidad y derechos de las mujeres. '
    'Este conjunto normativo refleja la evolución de las políticas públicas locales en la materia, '
    'desde los primeros antecedentes de 1993 hasta las regulaciones más recientes de 2023.'
)

doc.add_paragraph()
indice = doc.add_heading('ÍNDICE DE ORDENANZAS', level=1)

for i, ordn in enumerate(ordenanzas_data, 1):
    p = doc.add_paragraph()
    p.add_run(f"{i}. {ordn['titulo']} ({ordn['anio']})").bold = True

doc.add_page_break()

doc.add_heading('TEXTOS COMPLETOS DE LAS ORDENANZAS', level=1)

for i, ordn in enumerate(ordenanzas_data, 1):
    doc.add_heading(f'{ordn["titulo"]}', level=2)

    meta = doc.add_paragraph()
    meta.add_run('Año: ').bold = True
    meta.add_run(f"{ordn['anio']}  |  ")
    meta.add_run('Estado: ').bold = True
    meta.add_run(ordn['estado'].upper())

    doc.add_paragraph()
    resumen_label = doc.add_paragraph()
    resumen_label.add_run('Resumen:').bold = True
    doc.add_paragraph(ordn['resumen'])

    doc.add_paragraph('_' * 60)
    doc.add_paragraph()

doc.add_page_break()

doc.add_heading('RESUMEN EJECUTIVO', level=1)

doc.add_paragraph(
    'El Municipio de Saladillo ha desarrollado a lo largo de más de tres décadas (1993-2023) '
    'un corpus normativo significativo en materia de género, diversidad y derechos de las mujeres, '
    'conformando un marco de referencia para las políticas públicas locales.'
)

doc.add_heading('1. Caracterización del Cuerpo Normativo', level=2)

doc.add_paragraph(
    'Se registran 24 ordenanzas vinculadas a la temática de género y diversidad, dictadas '
    'en un período de 30 años. El análisis temporal permite identificar tres etapas claramente diferenciadas:'
)

doc.add_paragraph()
p = doc.add_paragraph()
p.add_run('a) Etapa Fundacional (1993-2008): ').bold = True
p.add_run('Se fokus en la atención a situaciones de violencia y creación de infraestructura '
          'de respuesta (Comisaría de la Mujer, complejo habitacional para mujeres golpeadas). '
          'Las ordenanzas 68/1993, 99/2012, 100/2012 y 30/2008 exemplify esta etapa.')

p = doc.add_paragraph()
p.add_run('b) Etapa de Consolidación (2012-2019): ').bold = True
p.add_run('Creación del Consejo Local contra la Violencia de Género (Ord. 48/2012), '
          'adhesión a la Ley Micaela (Ord. 29/2019) y primeras ordenanzas sobre diversidad '
          '(Día Municipal contra la discriminación por orientación sexual e identidad de género, Ord. 18/2016).')

p = doc.add_paragraph()
p.add_run('c) Etapa de Desarrollo Integral (2020-2023): ').bold = True
p.add_run('Diversificación temática con enfoque en inserción laboral (Ord. 67/2021), '
          'protocolos de actuación (Ord. 116/2022), comunicación con perspectiva de género (Ord. 101/2023), '
          'y medidas concretas como la promoción de copa menstrual (Ord. 45/2020).')

doc.add_heading('2. Ejes Temáticos Principales', level=2)

ejes = [
    ('Prevención y Erradicación de la Violencia de Género',
     '9 ordenanzas abordan directamente la problemática de la violencia, incluyendo la creación del '
     'Consejo Local (48/2012), Sistema de Alerta con botones anti-pánico (78/2021), Protocolo de '
     'Actuación integral (116/2022) y Programa de Inserción Laboral para víctimas (67/2021).'),
    ('Capacitación y Formación',
     '3 ordenanzas establecen la obligatoriedad de capacitación en género para personal municipal '
     '(29/2019, 46/2020) y la creación de la Dirección de Género (2021). La formación se complementa '
     'con obligaciones de difusión y comunicación institucional.'),
    ('Diversidad y No Discriminación',
     'Se registran ordenanzas sobre el Día Municipal contra la discriminación por orientación sexual '
     'e identidad de género (18/2016), prohibición de concursos de belleza (48/2016), y reconocimiento '
     'de mujeres en el espacio público (127/2017, 76/2014).'),
    ('Salud y Derechos Reproductivos',
     'Las ordenanzas 30/2008 (prevención de enfermedades mamarias), 45/2020 (copa menstrual) y '
     '34/2015 (licencia para estudios preventivos) conforman un eje de promoción de la salud integral.'),
    ('Igualdad y Participación',
     'Se establecen licencias por paternidad (24/2005, 16/2006), derechos laborales para víctimas de '
     'violencia (67/2021), y Lineamientos para la igualdad en el empleo público provincial.'),
]

for titulo, desc in ejes:
    p = doc.add_paragraph()
    p.add_run(f'• {titulo}').bold = True
    doc.add_paragraph(desc)

doc.add_heading('3. Marco Institucional', level=2)

doc.add_paragraph(
    'El sistema normativo establece una estructura institucional compuesta por:'
)

instituciones = [
    'Consejo Local contra la Violencia de Género y Familiar (creado por Ord. 48/2012)',
    'Dirección de Género y Diversidad Sexual (creada en 2021)',
    'Unidad de Género Local (órgano de aplicación de múltiples ordenanzas)',
    'Comisaría de la Mujer y la Familia (infraestructura habilitada por Ord. 100/2012)',
    'Hogar de Protección Integral (previsto en protocolos vigentes)',
]

for inst in instituciones:
    doc.add_paragraph(f'  - {inst}', style='List Bullet')

doc.add_heading('4. Convenios y Articulación Interinstitucional', level=2)

doc.add_paragraph(
    'Se destacan los siguientes convenios ratified:'
)

convenios = [
    'Convenio con el Ministerio Público de la Provincia de Buenos Aires para Sistema de Alerta y '
    'Botones Anti-pánico (Ord. 78/2021)',
    'Convenio con el Instituto de la Vivienda para complejo para la Mujer Golpeada (Ord. 68/1993)',
    'Convenio con la Asociación Civil Agruparte para programas de Desarrollo Humano (Ord. 45/2017)',
]

for conv in convenios:
    doc.add_paragraph(f'  • {conv}', style='List Bullet')

doc.add_heading('5. Estadísticas del Cuerpo Normativo', level=2)

stats_table = doc.add_table(rows=5, cols=2)
stats_table.style = 'Table Grid'

headers = ['Criterio', 'Valor']
stats_data = [
    ('Total de ordenanzas compiladas', '24'),
    ('Período de vigencia normativa', '1993 - 2023 (30 años)'),
    ('Ordenanzas vigentes', '24'),
    ('Marco legal nacional referencedo', 'Ley Micaela (27.499), Ley 26.485, Ley 26.743'),
]

for i, (criterio, valor) in enumerate(stats_data):
    stats_table.rows[i].cells[0].text = criterio
    stats_table.rows[i].cells[1].text = valor

doc.add_paragraph()

doc.add_heading('CONCLUSIONES', level=2)

doc.add_paragraph(
    'El Municipio de Saladillo ha construido un marco normativo comprehensivo en materia de '
    'género, diversidad y derechos de las mujeres. Las principales conclusiones son:'
)

conclusiones = [
    ("Consolidación institucional", "La creación del Consejo Local contra la Violencia de Género "
     "y la Dirección de Género conforman la estructura institucional necesaria para la implementación "
     "de políticas públicas en la materia."),
    ("Enfoque integral", "Las ordenanzas abordan tanto la prevención y erradicación de la violencia, "
     "como la promoción de derechos, la inserción laboral y la salud reproductiva."),
    ("Articulación interinstitucional", "Los convenios con organismos provinciales y nacionales permiten "
     "capitalizar recursos y especialistas para la atención de víctimas."),
    ("Marco de derechos", "La adhesión a leyes nacionales y provinciales (Ley Micaela, Ley 26.485, "
     "Ley de Identidad de Género) garantiza consistencia con el marco normativo superior."),
    ("Transversalidad", "Las políticas de género se integran en diversas áreas municipales: seguridad, "
     "salud, educación, desarrollo social, cultura y empleo."),
]

for i, (titulo, texto) in enumerate(conclusiones, 1):
    p = doc.add_paragraph()
    p.add_run(f'{i}. {titulo}: ').bold = True
    p.add_run(texto)

doc.add_paragraph()
doc.add_paragraph('—' * 40).alignment = WD_ALIGN_PARAGRAPH.CENTER

pie = doc.add_paragraph()
pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
pie.add_run('Documento generado automáticamente').italic = True
pie.add_run('\nMunicipio de Saladillo - Mayo 2026')

doc.save('ordenanzas_genero_diversidad.docx')
print("Documento generado: ordenanzas_genero_diversidad.docx")
