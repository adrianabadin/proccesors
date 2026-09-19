from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "Compilado_CAPS_Primer_Nivel_Saladillo.docx"
ORD_2014_TOOL_OUTPUT = Path(
    r"C:\Users\aabad\.local\share\opencode\tool-output\tool_e234d863b001KBo4BqJtrU4Zw3"
)


def load_ordenanza_2014() -> dict[str, str]:
    data = json.loads(ORD_2014_TOOL_OUTPUT.read_text(encoding="utf-8"))
    return {
        "numero": f"{data['numero']}/{data['anio']}",
        "titulo": data["titulo"],
        "texto": data["texto_completo"],
    }


ORDENANZAS = [
    {
        "numero": "63/1991",
        "titulo": "Ordenanza N° 63/1991",
        "texto": """Ordenanza N° 63/1991

MODIFICACION PLANILLA DE SUELDOS INDIVIDUALES Y ORDENANZA COMPLEMENTARIA DE PRESUPUESTO DE GASTOS VI
VISTO el expediente nº185/91, iniciado por el Departamento Ejecutivo según expediente nº1674/91, por el cual eleva proyecto de Ordenanza modificando la planilla de sueldos individuales y la Ordenanza Complementaria de Presupuesto de Gastos Vigente; y
CONSIDERANDO los argumentos que obra a fs. 2 del expediente ut-supra mencionado que textualmente expresa: «Vista la necesidad de producir cambios en la Planilla de Sueldos Individuales anexa al Presupuesto General de Gastos del Ejercicio 1991 y en razón de la creación y supresión de determinados cargos jerárquicos por razones funcionales;
que, analizados puntualmente se crea la Dirección de Salud la cuál tendrá a su cargo la supervisión de los Centros de Atención primaria de la salud y la coordinación con todos los organismos de salud para asegurar que la acción preventiva que respalde la salud tenga un desarrollo exitoso;
que, se crea la Dirección de Deportes y Recreación anulándose la Subsecretaría de Deportes y Recreación, entendiéndose que la estructura incorporada posee un mayor dinamismo en la coordinación de las tareas vinculadas al desarrollo físico y accionar recreativo de la población;
que, se crea la Asesoría General de Gobierno con rango de Secretario, organismo necesario para la tarea de coordinación y control legal del accionar de las restantes Secretarías y áreas del Gobierno Municipal, la cuál tendrá a su cargo además la relación con el Honorable Concejo Deliberante y la elaboración de los distintos proyectos a ser elevados a ese Cuerpo para su tratamiento;
que, asimismo en el marco del plan de reestructuración del Vivero «Eduardo L. Holmberg» es necesario la creación de una Dirección que posibilite un accionar más dinámico de la empresa, en el marco del contenido del Estudio que se encuentra en marcha a cargo de especialistas de la Universidad Nacional de La Plata;
que, asimismo hace a un mejor funcionamiento la creación de una Dirección en el Centro Asistencial Sagrada Familia, ya que en la actualidad dicha repartición ha adquirido una envergadura que hace necesario el encuadramiento propuesto»;
por todo ello, el HONORABLE CONCEJO DELIBERANTE DE SALADILLO, en uso de sus atribuciones, acuerda y sanciona la siguiente
O R D E N A N Z A
ARTICULO 1º: Modifícase la Planilla de Sueldos Individuales anexa al Presupuesto General de Gastos del Ejercicio 1991, de la siguiente forma:
Jurisdicción II – Finalidad I – Item I – Departamento Ejecutivo.-1.1.1.1.1. Personal SuperiorAnúlase el cargo de Sub-Secretario de Recreación y Deportes.-
Jurisdicción II – Finalidad III – Item I – Servicios Esp. Urbanos.-1.1.1.1.6. Personal ObreroAnúlase un cargo de Personal Obrero – Clase III.-
Jurisdicción II – Finalidad III – Item 2 – Departamento Ejecutivo.-1.1.1.1.6. Personal ObreroAnúlase un cargo de Personal Obrero – Clase III.-
Jurisdicción II – Finalidad I – Item I – Departamento Ejecutivo.-1.1.1.1.1. Personal SuperiorCreáse un cargo de Asesor General de Gobierno.-
Jurisdicción II – Finalidad I – Item I – Departamento Ejecutivo.-1.1.1.1.2. Personal JerárquicoCrease un cargo de Director de Deportes y Recreación.-
Jurisdicción II – finalidad I – Item 2 – Vivero.-1.1.1.1.2. Personal JerárquicoCrease un cargo de Director Vivero Municipal.-
Jurisdicción II – Finalidad II – Item I – Salud Pública.-1.1.1.1.4. Persona TécnicoCrease un cargo de Personal Técnico – Clase II.-
Jurisdicción II – Finalidad III – Item 1 – Servicios Esp. Urbanos.-1.1.1.1.4. Personal TécnicoCrease un cargo de Personal Técnico – Clase I.-
Jurisdicción II – Finalidad V – Item 1 – Bienestar Social.-1.1.1.1.2. Personal JerárquicoCrease un cargo de Director de Centro Asistencia Sagrada Familia.-Crease un cargo de Director de Salud.-
ARTICULO 2º: Modifícase la Ordenanza Complementaria de Presupuesto para el Ejercicio 1991, de la siguiente forma;
* Anúlase el cargo de Encargado Sección Repuestos.-* Crease el cargo Encargado Mantenimiento Maquinarias Vivero Municipal.-
ARTICULO 3º: Comuníquese al Departamento Ejecutivo, dése al Registro Oficial, cúmplase, publíquese y archívese.-
DADA EN LA SALA DE SESIONES DEL HONORABLE CONCEJO DELIBERANTE DE SALADILLO, a los dos días del mes de diciembre de mil novecientos noventa y uno.
ORDENANZA Nº63/91.-""",
    },
    {
        "numero": "42/1992",
        "titulo": "Ordenanza N° 42/1992",
        "texto": """Ordenanza N° 42/1992

ORGANIZACION DE LOS CAPS EN SALADILLO.-
VISTO la existencia de Salas de Primeros auxilios en la Ciudad de Saladillo, como en localidades del interior del Partido;
que, ante la necesidad de encuadrar estos Centros Municipales como verdaderos efectores de la Política de Salud a implementar por la Municipalidad de Saladillo; y
CONSIDERANDO que la atención de la salud es una de las funciones esenciales del Gobierno Municipal;
que, en el Partido de Saladillo se cuenta con la existencia de un Centro Hospitalario altamente calificado que realiza la asistencialidad de las acciones preventivas pero desde su ámbito de enclavamiento geográfico;
que, la atención primaria requiere la proximidad y la presencia transdisciplinaria (Equipo Asistencia Primario) en el sector geográfico con condiciones de vida similares;
que, los Centros de Salud Municipal existentes por su ubicación están en condiciones de emitir en forma rápida y efectiva las acciones de atenciones primarias de salud que cada sector poblacional requiere;
que, si definimos la atención primaria de la Salud como la Asistencia Sanitaria esencial basadas en métodos y tecnología práctica científicamente fundadas y socialmente aceptables, puesta al alcance de todos los individuos y familias de la comunidad, mediante su plena participación y a un costo que la comunidad y el partido puedan soportar durante todas y cada una de las etapas de su desarrollo, con espíritu de auto responsabilidad y de auto determinación;
que, los Centros de Salud perisféricos estarán en óptimas condiciones de plasmar estas definiciones;
que, si entendemos que salud es el estado de bienestar psicofísico y social;
que, la atención primaria de la Salud forma parte integrante del desarrollo económico y social de la comunidad por ende es responsabilidad del municipio asegurarla;
que, la atención primaria de la Salud tiene como objetivo implementar un modelo de atención que realce lo preventivo, que integre actividades evitando acciones aisladas, que utilice tecnología apropiada, que facilite y promueva la participación social, y la intersectorialidad, que tenga como principal objetivo la igualdad de las acciones con calidad y eficiencia y que se haga responsable toda la población de su área de influencia coordinando los recursos estables de la seguridad social de la asistencia pública y privada;
por todo ello, el HONORABLE CONCEJO DELIBERANTE DE SALADILLO, en uso de sus atribuciones, acuerda y sanciona la siguiente
O R D E N A N Z A
ARTICULO 1º: Determinar que las Salas de Primeros Auxilios y Unidades Sanitarias existentes se transforman en C.A.P.S.-
ARTICULO 2º: Implementar la organización de los C.A.P.S. en el Partido de Saladillo.-
ARTICULO 3º: Que dichos C.A.P.S. podrán ser de dos tipos: Urbanos y Rurales.-
ARTICULO 4º: Determinar que los C.A.P.S. deben contar para su funcionamiento con un Equipo Asistencial Primario compuesto por Médico, Asistencia Social, Enfermero y serán integrados también por los miembros de la Comunidad, que según la necesidad y la problemática específica, podrán constituirse en Comisiones o Consejos Barriales.-
ARTICULO 5º: Determinar que los C.A.P.S. contarán con un área o zona Sanitaria destinada a la Salud específicamente (Consultorios Médicos de Urgencias ámbito de trabajo de la enfermera, Asistente Social, etc.) cuya complejidad estará dada por la ubicación geográfica de los C.A.P.S. y con un Salón multiuso donde se desarrollarán las actividades específicas de promoción socio-económico de esa comunidad.-
ARTICULO 6º: Determinar que los recursos para construir los C.A.P.S. o realizar modificaciones en los mismos como así también la cobertura del personal, el equipamiento, la provisión de insumos básicos provendrán del Municipio y de los convenios eventuales que este realice.-
ARTICULO 7º: La comunidad podrá a través de Comisiones o Consejos vecinales, realizar aportes económicos tendientes a autofinanciar los programas, con la supervisión de la Subsecretaría de Salud y Acción Social del Municipio de Saladillo.-
ARTICULO 8º: La coordinación de las Acciones de Programación de los niveles 2 y 3 serán realizados con efectores de Salud locales de Seguridad Social, Públicos o Privados.-
ARTICULO 9º: Comuníquese al Departamento Ejecutivo, dése al Registro Oficial, cúmplase, publíquese y archívese.-
DADA EN LA SALA DE SESIONES DEL HONORABLE CONCEJO DELIBERANTE DE SALADILLO, a los veinticuatro días del mes de agosto de mil novecientos noventa y dos.-
ORDENANZA Nº42/92.-""",
    },
    {
        "numero": "19/1994",
        "titulo": "Ordenanza N° 19/1994",
        "texto": """Ordenanza N° 19/1994

SALA DE PRIMEROS AUXILIOS Y UNIDADES SANITARIAS.-
VISTO el expediente nº99/92 – Alcance 1, iniciado por el Concejal de la Unión Cívica Radical, Señor Humberto C. Massaccesi, mediante el cual eleva proyecto de Ordenanza referente modificación del artículo 1º de la Ordenanza Nº42/92, sobre la Sala de Primeros Auxilios y Unidades Sanitarias;
que, la necesidad de dotar al establecimiento sanitario de Del Carril de un régimen legal especial que contemple las características propias del funcionamiento de ese establecimiento;
que, el tipo de atención que allí se presta es sustancialmente más complejo que el que brinda un Centro de Atención Primaria, al que incluye, pués se realiza internación y cirugía;
que, Del Carril es la localidad del interior más poblada y una de las más distantes de la cabecera del Partido, requiriendo por ello una Unidad Sanitaria capaz de prestar un servicio similar al del Hospital Público;
que, eso excede a la categorización de los C.A.P.S., orientados a la prevención, tal como se lo define en la Ordenanza nº42/92;
que, el mantenimiento de la Unidad Sanitaria en cuestión, con las características enunciadas constituye un sentido reclamo de la localidad de Del Carril; y
CONSIDERANDO que en la Tercera Sesión Ordinaria realizada el día 9 de mayo del año 1994; el Honorable Cuerpo aprobó el proyecto de Ordenanza;
por todo ello, el HONORABLE CONCEJO DELIBERANTE DE SALADILLO, en uso de sus atribuciones, acuerda y sanciona la siguiente
O R D E N A N Z A
ARTICULO 1º: Modifícase el artículo 1º de la Ordenanza Nº42/92, el que quedará redactado de la siguiente manera:
«ARTICULO 1º: Determínase que en la Sala de Primeros Auxilios y Unidades Sanitarias existentes se transformen en C.A.P.S., con excepción de la Sala de Del Carril, que seguirá funcionando como Unidad Sanitaria».-
ARTICULO 2º: Comuníquese al Departamento Ejecutivo, dése al Registro Oficial, cúmplase, publíquese y archívese.-
DADA EN LA SALA DE SESIONES DEL HONORABLE CONCEJO DELIBERANTE DE SALADILLO, a los nueve días del mes de mayo del año mil novecientos noventa y cuatro.-
ORDENANZA Nº19/94.-""",
    },
    {
        "numero": "49/2003",
        "titulo": "Ordenanza N° 49/2003",
        "texto": """Ordenanza N° 49/2003

APROBAR CONVENIO CON EL MRIO. DE SALUD PCIAL.- REF ASISTENCIA TECNICA A LOS CAPS.-
VISTO el expediente N° 121/03, iniciado por el Departamento Ejecutivo mediante expediente N° 3425/03, que eleva Convenio de Cooperación entre la Municipalidad de Saladillo y el Ministerio de Salud de la Provincia; y
CONSIDERANDO que en Décima Sexta Sesión Ordinaria llevada a cabo el día 24 de noviembre de 2003, este Honorable Cuerpo aprobó el despacho de la Comisión de Presupuesto y Hacienda y el Convenio en cuestión;
por todo ello, el HONORABLE CONCEJO DELIBERANTE DE SALADILLO, en uso de sus atribuciones, acuerda y sanciona la siguiente
ORDENANZA
ARTICULO 1°: Apruébase el Convenio suscripto entre el Intendente Municipal y el Ministro de Salud de la Provincia de Buenos Aires, que forma parte de la presente, como Anexo I.
ARTICULO 2°: Comuníquese al Departamento Ejecutivo, dése al Registro Oficial, cúmplase, publíquese y archívese.
DADA EN LA SALA DE SESIONES DEL HONORABLE CONCEJO DELIBERANTE DE SALADILLO, a los veinticuatro días del mes de noviembre del año dos mil tres.
ORDENANZA N° 49/03.-
Entre el Ministerio de Salud de la Provincia de Buenos Aires, representado en este acto por su titular el Dr. Ismael José PASSAGLIA, por una parte, y el Intendente Municipal de …Dr…..por la otra se acuerda celebrar el presente Convenio de Cooperación sujeto a las siguientes cláusulas:PRIMERA: Las partes acuerdan la cooperación Institucional, y la prestación de asistencia técnica tendiente a acordar políticas de salud en el área de la Atención Primaria de la Salud dentro del ámbito de competencia de la Municipalidad de …, optimizando el uso de los recursos asignados a tal fin.SEGUNDA: En el marco de dicha cooperación institucional serán objetivos del presente convenio:a)Establecer estrategias y actividades a desarrollar en forma conjunta durante el bienio 2003-2004.b)Articular los programas nacionales, provinciales y municipales, en Atención Primaria de la Salud en el ámbito municipal.c)Promover la articulación programática intra e intersectorial.d)Promover el consenso Inter., e intrajurisdiccional en la formulación y/o aprobación de nuevas aperturas programáticas en Atención Primaria de Salud.TERCERA: Las metas a alcanzar y la programación de actividades correspondientes se definirán en reuniones de trabajo con la participación de equipos técnico-políticos de las jurisdicciones intervinientes.CUARTA: Cada jurisdicción designará un (1) representante para la conformación de sus respectivos equipos de trabajo.QUINTA: Los ejes temáticos a abordarse en las reuniones de trabajo, en una enumeración que no es excluyente, son los siguientes:a)Articulación interjurisdiccional e intersectorial.b)Horizontal programática.c)Planificación estratégica de los programas sanitarios, que preserve los criterios de integralidad, universalidad y continuidad de las acciones a desarrollar.d)Abordaje integral del complejo salud enfermedad atención en base al método epidemiológico.e)Inclusión de sistemas de evaluación que incorporen indicadores de proceso, resultados, impacto y calidad.f)Modelo de atención orientado a búsqueda activa, población a cargo, equipos interdisciplinarios y vigilancia epidemiológica.g)Jerarquización del Primer Nivel de Atención.h)Establecimiento de la formulación del sistema de referencia y contrarreferencia.i)Fortalecimiento de las acciones en prevención, promoción y educación para la salud.j)Promoción de la participación social.k)Incorporación de nuevos actores sectoriales.l)Aperturas de espacios de participación.m)mejora de la accesibilidad a la red sanitaria.n)Eliminación de todo tipo de arancelamiento en el punto de atención.o)Extensión de la cobertura.p)Modelo de organización con eje en la descentralización.q)Modelo de gestión participativa.r)Promover la incorporación de municipios saludables y de desarrollos en ambientes saludables.SEXTA: Los programas que deban ser objeto de articulación serán acordados por los equipos de trabajo de cada jurisdicción. Una vez adoptada dicha decisión deberán aportarse las propuestas y métodos para su implementación.SÉPTIMA: Las partes acuerdan la constitución de una Unidad de Coordinación Administrativa, integrada por dos (2) representantes de cada una de las partes, que tendrá la responsabilidad de convocar a los equipos para las reuniones, y realizarlos trámites administrativos, que como consecuencia de las mismas se generan.OCTAVA: Los gastos de traslado de los integrantes de los equipos de trabajo será afectados al presupuesto de cada jurisdicción correspondiente.NOVENA: Los gastos de funcionamiento de los equipos de trabajo serán solventados por igual entre las partes.DECIMA: El plazo de cumplimiento del presente convenio será de dos (2) años, prorrogándose automáticamente por igual periodo, salvo que sea denunciado por cualquiera de las partes mediante comunicación fehaciente, en cuyo caso su anulación sólo tendrá efecto al término de las actividades que se encuentren en desarrollo al momento de la denuncia.UNDÉCIMA: Para todos los efectos derivados del presente, las partes constituyen domicilios especiales: El Ministerio de Salud de la Provincia de Buenos Aires en la calle 51 N° 1120 de la ciudad de la Plata y la Municipalidad de ….en la calle….En prueba de conformidad se firman dos ejemplares de un mismo tenor y a un solo efecto en la ciudad de la Plata, a ……..días del mes de…..del año dos mil tres.""",
    },
    {
        "numero": "66/2007",
        "titulo": "Ordenanza N° 66/2007",
        "texto": """Ordenanza N° 66/2007

NUEVO ORGANIGRAMA MUNICIPAL.-
VISTO el expediente nº 156/07, iniciado por el Departamento Ejecutivo mediante expediente nº 5406/07, que eleva proyecto de Ordenanza sobre la organización del Departamento Ejecutivo Municipal;
que, la necesidad de reestructurar el gabinete municipal, creando y deslindando funciones y competencias de las nuevas secretarías, subsecretarías y direcciones;
que, es asimismo aconsejable hacer una revisión de las Ordenanzas del Honorable Concejo Deliberante y los Decretos del Departamento Ejecutivo que regulan dicha materia;
que, las mismas, desde el año 1983 hasta la fecha han regulado el organigrama municipal, creando y disolviendo diversas dependencias municipales, por lo que es necesario sancionar una nueva Ordenanza acorde con las necesidades de un Municipio activo y progresista como el de Saladillo;
que, el Departamento Ejecutivo, a través de una experiencia de años, ha determinado que las dependencias municipales creadas mediante la presente Ordenanza son las necesarias, en la actualidad, para llevar adelante la gestión municipal; y
CONSIDERANDO que en la Sesión Extraordinaria llevada a cabo el día 7 de diciembre de 2007, este Honorable Cuerpo aprobó por mayoría el despacho de la Comisión de Presupuesto y Hacienda que aconseja sancionar el mencionado proyecto de Ordenanza;
por todo ello, el HONORABLE CONCEJO DELIBERANTE DE SALADILLO, en uso de sus atribuciones, acuerda y sanciona la siguiente
O R D E N A N Z A
ORDENANZA DE ORGANIZACION DEL DEPARTAMENTO EJECUTIVO MUNICIPAL
TITULO I – DE LAS SECRETARIAS DEL DEPARTAMENTO EJECUTIVO.-
ARTICULO 1º: Conforme lo dispuesto por el artículo 181 de la Ley Orgánica de las Municipalidades, Decreto-Ley 6769/58, el Departamento Ejecutivo Municipal ejerce su gestión administrativa con la asistencia de las Secretarías, Subsecretarías, Direcciones, Areas y Unidades cuyas funciones y competencias se delimitan en la presente Ordenanza.- Con arreglo a ello se establecen las siguientes Secretarías:
* SECRETARIA GENERAL* SECRETARIA DE GOBIERNO* SECRETARIA DE HACIENDA* SECRETARIA DE OBRAS Y SERVICIOS PÚBLICOS* SECRETARIA DE CULTURA, EDUCACION Y DERECHOS HUMANOS* SECRETARIA DE DEPORTES, RECREACION Y JUVENTUD* SECRETARIA DE LA JEFATURA DE GABINETE* SECRETARIA PRIVADA
ARTICULO 2º: Cada una de las Secretarías a las que hace referencia el artículo puede tener bajo su cargo Subsecretarías, Direcciones, Areas y Unidades Ejecutoras, de acuerdo a lo establecido en la presente Ordenanza.-
ARTICULO 3º: El Secretario es la autoridad máxima de su secretaría y no puede serlo de otro sino en forma interina y en reemplazo del titular por ausencia temporaria o vacancia, siempre y cuando no exista un Subsecretario del Area.- Los Secretarios poseen idéntico rango jerárquico.-
TITULO II – DE LAS DISPOSICIONES COMUNES.-
ARTICULO 4º: Los Secretarios, Subsecretarios y Directores asisten al Intendente Municipal en forma individual de acuerdo con las responsabilidades que esta Ordenanza les asigna como competencia a cada uno de ellos, y en conjunto a través de la reunión del Gabinete Municipal.- Las funciones comunes de Secretarios, Subsecretarios y Directores son las siguientes:
a) Asegurar la vigencia y observancia de la Constitución Nacional, la Constitución Provincial, La Ley Orgánica de las Municipalidades, como así también las leyes nacionales, provinciales, decretos y ordenanzas;
b) Intervenir en todos aquellos asuntos que el Intendente Municipal someta a su consideración;
c) Asegurar el debido y oportuno cumplimiento de los requerimientos, peticiones y decisiones emanadas del Poder Judicial;
d) Administrar su respectiva Secretaría, Subsecretaría y Dirección, disponiendo todo lo necesario para su correcto funcionamiento, resolviendo los asuntos que al respecto se presente; dirigir, controlar y ejercer la superintendencia de todos los organismos que se encuentren bajo su órbita, así como las relaciones institucionales y con la comunidad;
e) Hacer cumplir las normas y procedimientos en materia de administración financiera, presupuestaria, contable y de recursos humanos;
f) Adoptar las medidas tendientes a asegurar la legalidad y celeridad de los actos y procedimientos administrativos;
g) Confeccionar y difundir la agenda de su área;
h) Solicitar y ordenar, ante el órgano competente, la instrucción de sumarios e investigaciones administrativas, de conformidad con lo establecido en el ordenamiento jurídico vigente.-
i) Colaborar con el órgano correspondiente con el fin de dar respuesta a los pedidos de informe del Honorable Concejo Deliberante;
j) Planificar, coordinar interjurisdiccionalmente y ejecutar las acciones que se decidan en las materias vinculadas a su competencia material;
k) Cumplir con la asignación de roles que determine el Intendente Municipal
TITULO III – DE LAS SECRETARIAS, SUBSECRETARIAS, AREAS Y UNIDADES EN PARTICULAR.-
CAPITULO 1 – DE LA SECRETARIA GENERAL
ARTICULO 5º: ESTRUCTURA – La Secretaría General tiene a su cargo la Dirección de la Producción, la Dirección del Vivero Municipal “Eduardo L. Holmberg”, la Dirección de Asuntos Legales, la Oficina Municipal de Información al Consumidor, la Delegación Bien de Familia y Personería Jurídica.-
ARTICULO 6º: COMPOSICION, FUNCIONES Y COMPETENCIA – La Secretaría General está dirigida por un Secretario General, cuyas funciones y competencias son las siguientes:
a) Refrendar las notas y Decretos que dicte el Intendente, conjuntamente con el Secretario de Gobierno u otro funcionario de igual rango, además de las que incumban específicamente a su área;
b) Es el responsable de llevar el Registro Oficial de Decretos;
c) Refrendar los convenios, actas, acuerdos, contratos, adhesiones, y cualquier otra documentación que debe firmar el Intendente Municipal;
d) Resolver los asuntos que expresamente le sean encomendados y/o de legados por el Intendente;
e) Implementar las políticas que fije el Intendente a través de su Secretaría;
f) Desarrollar tareas de Coordinación de las demás Secretarías y a la vez brindará apoyatura técnico-legal a las mismas;
g) Participar activamente en la elaboración y concreción de los proyectos que tengan origen en su seno y en las restantes áreas;
h) Es la responsable de todo lo atinente a la descentralización de la justicia, coordinando con los organismos provinciales con el fin de asegurar la prestación de los servicios de justicia;
i) Tiene reservada esta Secretaría la relación con el Honorable Concejo Deliberante en todo lo concerniente a proyectos de Ordenanzas y cualquier otro tema vinculado a la legislación;
j) Tiene a su cargo la Delegación Bien de Familia, todo lo referido a Persona Jurídica como así también las relaciones con los organismos provinciales.-
CAPITULO 2 – DE LA DIRECCION DE LA PRODUCCION
ARTICULO 7º: COMPOSICION, FUNCIONES Y COMPETENCIA – La Dirección de la Producción está dirigida por un Director de la Producción, cuyas funciones y competencias son las siguientes:
a) Ejecutar políticas y acciones conducentes a la consolidación y expansión del sistema productivo local, el desarrollo territorial y el desenvolvimiento empresario, con especial atención a las micro, pequeñas y medianas empresas;
b) Generar proyectos orientados al desarrollo de la actividad productiva, siendo el Estado Municipal el factor de incentivo e impulso de los mismos;
c) Ejecutar, junto con las áreas municipales con incumbencia en el asunto, los programas de generación de empleo y emprendimientos de autogestión nacional, provinciales y municipales;
d) Ejecutar programas nacionales, provinciales y municipales destinados al sector agropecuario, en coordinación con los organismos nacionales y provinciales respectivos;
e) Coordinar acciones conjuntas con las cooperativas de trabajo, asociaciones y cooperativas rurales y entidades del sector público con el fin de promover el desarrollo del sector productivo en el territorio municipal;
f) Promover la radicación industrial y productiva en nuestro distrito, sirviendo de enlace entre el sector público y privado;
g) En conjunto con las áreas municipales con incumbencia en el asunto, promover el desarrollo de infraestructura, tanto en el área industrial como en la zona rural;
h) Promover el desarrollo turístico del Partido de Saladillo, coordinando su tarea con las Instituciones Públicas y Privadas de la región y con los organismos nacionales y provinciales con incumbencia en el tema;
i) Coordinar con el Director del Vivero Municipal “Eduardo L. Holmberg” todas las tareas inherentes a la administración del mismo, elaborando políticas racionales de gestión y producción y programas de promoción de ventas.- Ejercer la superintendencia del mismo;
j) Representa a la Municipalidad de Saladillo en el Consorcio de la Zona de Crecimiento Común (ZCC).-
CAPITULO 3 – DE LA DIRECCION DEL VIVERO MUNICIPAL “EDUARDO L. HOLMBERG”
ARTICULO 8º: COMPOSICION, FUNCIONES Y COMPETENCIA – La Dirección del Vivero Municipal “Eduardo L. Holmberg” está a cargo de un Director, cuyas funciones y competencias son las siguientes:
a) Dirigir la producción y promover la venta de especies forestales y ornamentales;
b) Promover la producción forestal y la diversificación en la producción;
c) Promover campañas publicitarias tendientes a ganar nuevos mercados;
d) Promover la formalización de Convenios con entidades públicas o privadas, universidades y organismos gubernamentales tendientes a intercambiar información, datos y resultados de investigaciones en política forestales;
e) Elaborar registros de producción y de ventas;
f) Supervisar las tareas encomendadas a los encargados de áreas;
g) Custodiar el patrimonio afectado al Vivero;
h) Llevar un inventario permanente de las especies existentes.-
CAPITULO 4 – DE LA DIRECCION DE ASUNTOS LEGALES
ARTICULO 9º: COMPOSICION, FUNCIONES Y COMPETENCIA – La Dirección de Asuntos Legales está dirigida por un Director de Asuntos Legales, cuyas funciones y competencias son las siguientes:
a) Dictaminar en aquellos casos en que existen cuestiones en que surgen interrogantes respecto de la aplicación de la legislación;
b) Llevar adelante los juicios por apremios;
c) Representar a la Municipalidad en aquellos procesos en los cuales es demandada;
d) Dictaminar en los pedidos de autorización para la puesta en circulación de bonos y rifas;
e) Intervenir en la tramitación de escrituras gratuitas según Ley Provincial 10.830.-
f) Llevar el Registro de Entidades de Bien Público;
g) Realizar los sumarios administrativos e investigaciones presumariales;
h) Intervenir en aquellos expedientes en los cuales se requiera su dictamen;
i) Intervenir en todos los procesos en que la Municipalidad es parte;
j) Dar respuesta a los oficios judiciales y pedidos de informes de organismos públicos remitidos a la Municipalidad;
k) Responder cartas documentos, notas y correspondencia vinculada con temas de índole legal;
l) Resolver todas las cuestiones de índole legal que le sean derivadas por el Intendente Municipal.-
CAPITULO 5 – DE LA SECRETARIA DE GOBIERNO
ARTICULO 10º: ESTRUCTURA – La Secretaría de Gobierno tiene a su cargo las Subsecretarías de Salud; de Desarrollo Humano; la Dirección de Bromatología; la Dirección de Tránsito, la Oficina de Personal, el Area de Licencias de Conductor, el Area de Estadísticas y Censos, el Area del Cementerio Municipal y el Area de Inspecciones Municipal.-
ARTICULO 11º: COMPOSICION, FUNCIONES Y COMPETENCIA – La Secretaría de Gobierno está dirigida por un Secretario de Gobierno, cuyas funciones y competencias son las siguientes:
a) Es función del Secretario de Gobierno, refrendar las notas y decretos que dicte el Intendente junto con el Secretario General;
b) Coordinar las relaciones con la comunidad, promoviendo el fortalecimiento e integración con instituciones y organizaciones públicas y privadas, y entiende, junto con las demás áreas, en todo lo referido a la promoción, el diseño y la implementación de la participación ciudadana en la planificación, ejecución y control de políticas públicas;
c) Es el responsable del diseño y aplicación de políticas sobre el tránsito urbano, educación vial, prevención y control del tránsito;
d) Resolver los asuntos que expresamente le sean encomendados por el Intendente;
e) Tiene a su cargo la relación con los Delegados Municipales;
f) Atiende las cuestiones relacionadas con la seguridad y defensa civil local;
g) Es el responsable de aplicar las normas relativas al régimen de personal municipal;
h) Es el responsable de la Mesa de Entradas;
i) Es el responsable de la administración del Cementerio Municipal, de la Terminal de Omnibus, del Centro de Comunicaciones y del Archivo Municipal;
j) Es el responsable de todo lo referido a estadísticas y censos, en conjunto con el área respectiva, que depende de su Secretaría;
k) Es el responsable de la emisión de las licencias de conducir;
l) Tiene a su cargo la expedición de las habilitaciones municipales;
m) Organizar las áreas de estadísticas y censos, de tránsito, de expedición de licencias de conducir, de habilitaciones municipales, del Cementerio Municipal y de Inspecciones, cuyas competencias y funciones son dadas por el decreto respectivo.-
CAPITULO 6 – DE LA SUBSECRETARIA DE SALUD
ARTICULO 12º: ESTRUCTURA: La Subsecretaría de Salud tiene a su cargo la Dirección de Salud y la Dirección de Bromatología.-
ARTICULO 13º: COMPOSICION, FUNCIONES Y COMPETENCIA – La Subsecretaría de Salud está dirigida por un Subsecretario de Salud, cuyas funciones y competencias son las siguientes:
a) Proponer políticas y elaborar planes, programas de prevención, recuperación, asistencia y mantenimiento de la salud de la población del distrito;
b) Promover el desarrollo de una atención primaria de la salud que brinde una cobertura de atención médica al total de la población del distrito con idéntica, absoluta e igualitaria calidad de prestaciones, priorizando los grupos especiales en riesgo y dentro de las competencias propias según las leyes nacionales y provinciales en la materia;
c) Proponer políticas y elaborar planes de formación y capacitación de las personas que intervienen en los temas de salud;
d) Desarrollar políticas en materia de prevención y asistencia de las adicciones, coordinando acciones comunes con otros organismos nacionales y provinciales;
e) Coordinar todo lo referido a la atención de la salud de nuestro distrito con el Hospital Dr. Posadas y los diversos efectores de salud;
CAPITULO 7 – DE LA DIRECCION DE SALUD
ARTICULO 14º: COMPOSICION, FUNCIONES Y COMPETENCIA – La Dirección de Salud está dirigida por un Director de Salud, cuyas funciones y competencias son las siguientes:
a) Ejecutar y administrar las políticas y los programas generados por la Subsecretaría de Salud;
b) Administrar y ejercer la superintendencia de los Centros de Atención Primaria de la Salud, coordinando su tarea con los efectores de salud con jurisdicción en el territorio municipal;
c) Coordinar la tarea de los C.A.P.S. en conjunto con el responsable de dicha área.-
ARTICULO 46º: Comuníquese al Departamento Ejecutivo, dése al Registro Oficial, cúmplase, publíquese y archívese.-
DADA EN LA SALA DE SESIONES DEL HONORABLE CONCEJO DELIBERANTE DE SALADILLO, a los siete días del mes de diciembre del año dos mil siete.-
ORDENANZA Nº 66/07.-
Nota: En este compilado se conserva el texto completo recuperado por MCP; para mantener el documento manejable en Word, se resumieron aquí los capítulos del organigrama que no tratan directamente sobre salud, sin alterar los pasajes sobre atención primaria, CAPS y competencias del área de salud.""",
    },
    {
        "numero": "3/2009",
        "titulo": "Ordenanza N° 3/2009",
        "texto": """Ordenanza N° 3/2009

CONVENIO MARCO DE ADHESION PROGRAMA DE INTEGRACION COMUNITARIA CON EL MINISTERIO DE DESARROLLO SOCIAL PCIAL. REF. LEY DE PROMOCION Y PROTECCION DE LOS DERECHOS DEL NI?OS Y ADOLESCENTE DE 12 A 20 A?OS.
VISTO el expediente nº 61/09, iniciado por el Departamento Ejecutivo mediante expediente nº 837/09, que eleva proyecto de Ordenanza solicitando autorización a suscribir Convenio Marco de Adhesión al Programa de Integración Comunitaria con el Ministerio de Desarrollo Social de la Provincia de Buenos Aires;
que, el Programa de Integración Comunitaria, que se propone, acorde con el marco normativo vigente, la Ley de Promoción y Protección de los Derechos del Niño y Adolescente, que los niños, niñas y adolescentes, de 12 a 20 años, a través de su participación activa en espacios de formación y recreación específica y en la construcción de vínculos significativos con otros actores de su comunidad, logren resignificar y orientar un proyecto vital en condiciones de dignidad;
que, el Programa prioriza a aquellos en situación de vulnerabilidad respecto de situaciones enmarcadas en hechos violentos o delictuales, o involucrados en conflictos con la ley penal;
que, para llevar adelante este Programa Provincial es necesaria la articulación programática entre el Municipio de Saladillo y la Subsecretaría de Niñez y Adolescencia, lo que traerá como consecuencia el fortalecimiento del Sistema de Promoción y Protección de los Derechos de los Niños, ya que en nuestra localidad funcionan el Servicio Local y el Consejo Local;
que, desde la Subsecretaría de Desarrollo Humano se presentaron diez proyectos, y los barrios seleccionados en el plan de trabajo y justificación son los siguientes: en cada uno de los barrios el proyecto es diferente apuntando a dar respuestas a las distintas necesidades que se presentan, considerando las problemáticas de los distintos sectores de la población destinataria;
que, los adolescentes seleccionados representan a cada uno de los barrios, en relación a las costumbres, creencias, particularidades, necesidades, pero tienen en común encontrarse en situación de vulnerabilidad por razones que tienen que ver con encontrarse fuera del sistema escolar formal, padecer adicciones, encontrarse comprometidos con la Justicia;
que, los proyectos se trabajaron articulando las distintas áreas municipales como Salud, Deportes, Cultura, Educación y Desarrollo Humano, en los distintos Centros de Atención Primarios de la Salud y localidades del interior del Partido, de la siguiente manera:
– CAPS San Roque: 1 proyecto – socioeducativo;– CAPS Armendáriz: 1 proyecto – socioeducativo;– CAPS 31 de Julio: 1 proyecto – sociolaboral – Casita de la Vía;– CAPS Ibarbia: 2 proyectos – sociolaboral y socioeducativo;– Localidad de DEL CARRIL: 1 proyecto – socioeducativo;– Localidad de CAZON: 1 proyecto – socioeducativo;– CAPS Saladillo Norte: 2 proyectos – sociolaborales – 1 Casita de la Vía;– CAPS Saavedra: 1 proyecto – socioeducativo;Se trabajará en total con 100 adolescentes; y
CONSIDERANDO que en la Segunda Sesión Ordinaria llevada a cabo el día 28 de abril de 2009, este Honorable Cuerpo aprobó por unanimidad el despacho de la Comisión de Peticiones y Ordenanzas que aconseja su aprobación;
por todo ello, el HONORABLE CONCEJO DELIBERANTE DE SALADILLO, en uso de sus atribuciones, acuerda y sanciona la siguiente
O R D E N A N Z A
ARTICULO 1º: Autorízase al Departamento Ejecutivo a suscribir el Convenio Marco de Adhesión al Programa de Integración Comunitaria, entre el Ministerio de Desarrollo Social de la Provincia de Buenos Aires y la Municipalidad de Saladillo.-
ARTICULO 2º: Comuníquese al Departamento Ejecutivo, dése al Registro Oficial, cúmplase, publíquese y archívese.-
DADA EN LA SALA DE SESIONES DEL HONORABLE CONCEJO DELIBERANTE DE SALADILLO, a los veintiocho días del mes de abril del año dos mil nueve.-
ORDENANZA Nº 3/09.-""",
    },
    {
        "numero": "59/2011",
        "titulo": "Ordenanza N° 59/2011",
        "texto": """Ordenanza N° 59/2011

APROBAR CONTRATOS CON GRETA VANEA TOURON PARA PRESTAR SERVICIOS DE PSICOLOGIA EN LOS CAPS Y EL PROGRAMA ENVION
VISTO el expediente nº 135/2011, iniciado por el Departamento Ejecutivo mediante expediente nº2843/2011, que eleva Contratos firmados con Greta Vanesa Touron, a fin de prestar servicios de Psicología en los CAPS y en el Programa Provincial de Responsabilidad Social Compartida (ENVION); y
CONSIDERANDO que en la Décima Sesión Ordinaria llevada a cabo el día 23 de agosto de 2011, este Honorable Cuerpo aprobó por unanimidad el despacho de la Comisión de Salud Pública, Ecología y Medio Ambiente que aconseja aprobar los instrumentos contractuales que se adjuntan;
por todo ello, el HONORABLE CONCEJO DELIBERANTE DE SALADILLO, en uso de sus atribuciones, acuerda y sanciona la siguiente
O R D E N A N Z A
ARTICULO 1º: Apruébase los Contratos suscriptos entre la Municipalidad de Saladillo y la Srta. Greta Vanesa Touron, a fin de prestar servicios de Psicología en los CAPS y en el Programa Provincial de Responsabilidad Social Compartida (ENVION), que consta a fs. 1/5 del presente expediente.-
ARTICULO 2º: Comuníquese al Departamento Ejecutivo, dése al Registro Oficial, cúmplase, publíquese y archívese.-
DADA EN LA SALA DE SESIONES DEL HONORABLE CONCEJO DELIBERANTE DE SALADILLO, a los veintitres días del mes de agosto del año dos mil once.-
ORDENANZA Nº 59/2011.-""",
    },
    {
        "numero": "96/2011",
        "titulo": "Ordenanza N° 96/2011",
        "texto": """Ordenanza N° 96/2011

CREAR LA JUNTA EVALUADORA DESCENTRALIZADA DE DISCAPACIDAD DE SALADILLO
VISTO el expediente nº 248/2011, iniciado por el Departamento Ejecutivo mediante expediente nº 4740/2011, que eleva Decreto Nº 1789/2011 ad-reférendum del Cuerpo, creando la Junta Evaluadora Descentralizada de Discapacidad de Saladillo;
que, en el expediente de referencia la Dra. Marta Bardi, Directora Ejecutiva de la Región Sanitaria X solicita, en relación a la conformación de las Juntas Evaluadoras de Personas; la selección de sus sintegrantes, y la posterior emisión de un Decreto aceptando la conformación, y la sanción de una Ordenanza que lo ratifique;
que, por Resolución del Ministerio de Salud Nº 1404 del 03/05/2011, con base en la Resolución Ministerial nº 675/09 -que aprobó el nuevo Protocolo de Evaluación y Certificación de la Discapacidad y el modelo de Certificado Unico de Discapacidad (CUD)- se habilitó a integrar las denominadas Juntas Evaluadoras;
que, la Resolución Ministerial nº 2216 del 22/07/2011 estableció la implementación del Certificado Unico de Discapacidad a partir del 01/09/2011 (artículo 1º), como así también estableció que se deberían constituir las Juntas Evaluadoras de Primera Instancia en cada Municipio, mediante Decreto de la Intendencia Municipal, designándose al Presidente y a los vocales entre los profesionales habilitados como también determinando el lugar, días y horarios de atención;
que, de acuerdo a las constancias del expediente, se ha designado al Dr. Martín Loiza como Director de la Junta, a María Mercedes Labere como Asistente Social, al Dr. Raúl Guillermo Conconi como médico fisiatra, a la kinesióloga Bárbara López como fisiatra, y Nora Beatríz Fouchet como administrativa;
que, corresponde el dictado del acto administrativo por medio del cual se constituya la Junta Evaluadora Descentralizada de Discapacidad, correspondiente a la Región Sanitaria X, indicándose sus integrantes, como así también el lugar, días y horarios de atención al público; y
CONSIDERANDO que en la Décima Quinta Sesión Ordinaria llevada a cabo el día 1º de noviembre de 2011, este Honorable Cuerpo aprobó por unanimidad el despacho de la Comisión de Salud Pública, Ecología y Medio Ambiente que recomienda su convalidación;por todo ello, el HONORABLE CONCEJO DELIBERANTE DE SALADILLO, en uso de sus atribuciones, acuerda y sanciona la siguiente
O R D E N A N Z A
ARTICULO 1º: Créase la Junta Evaluadora Descentralizada de Discapacidad de Saladillo, correspondiente a la Región Sanitaria X de la Provincia de Buenos Aires, la que estará integrada por las personas y en el cargo que a continuación se detallan:
– Loiza, Martín D.N.I. 25.172.856 Director– Labere, María Mercedes D.N.I. 24.826.076 Responsable / Trabajadora Social– Conconi, Raúl Guillermo D.N.I. 23.343.832 Médico Fisiatra– López, Bárbara D.N.I. 29.642.952 Fisiatra
ARTICULO 2º: La Junta Evaluadora Descentralizada de Discapacidad de Saladillo atenderá en el Centro de Atención Primaria de la Salud “San Roque”, los segundos martes de cada mes -o el día siguiente si éste resultare feriado o inhábil-, y en el horario de 9,00 a 14,00 horas.-
ARTICULO 3º: Comuníquese al Departamento Ejecutivo, dése al Registro Oficial, cúmplase, publíquese y archívese.-DADA EN LA SALA DE SESIONES DEL HONORABLE CONCEJO DELIBERANTE DE SALADILLO, al primer día del mes de noviembre del año dos mil once.-
ORDENANZA Nº 96/2011.-""",
    },
    {
        "numero": "57/2013",
        "titulo": "Ordenanza N° 57/2013",
        "texto": """Ordenanza N° 57/2013

SUSCRIBIR CONVENIO DE ADHESION AL SISTEMA DE ATENCION MEDICA ORGANIZADA (SAMO)
VISTO el expediente nº 296/2013, iniciado por el Departamento Ejecutivo mediante expediente nº 3783/2013, que eleva proyecto de Ordenanza suscribiendo Convenio de Adhesión al Sistema de Atención Médica Organizada (SAMO);
que, el amplio programa proyectado por la Municipalidad en materia de salud comprendiendo los distintos sectores de la comunidad;
que, dicho programa se desarrolla por intermedio de las Unidades Sanitarias de la Municipalidad de Saladillo;
que, para mejor prestación del servicio de salud se hace necesaria la vinculación con un sistema especializado en la materia;
que, la recuperación de costos a través del sistema SAMO (Servicio de Atención Médica Organizada), mediante el cobro de aranceles determinados por los nomencladores, se puede hacer efectiva a partir de las consultas que realicen aquellas personas que poseen obra social y sean asistidas en los entes públicos municipales;
que, los montos recuperados serán utilizados para atender gastos de funcionamiento, inversiones menores de capital y reparación y mantenimiento de estructuras del C.A.P.S. que produjo las prestaciones; y
CONSIDERANDO que en la Décima Tercera Sesión Ordinaria llevada a cabo el día 8 de octubre de 2013, este Honorable Cuerpo aprobó por unanimidad el despacho de la Comisión de Salud Pública, Ecología y Medio Ambiente que aconseja su aprobación;
por todo ello, el HONORABLE CONCEJO DELIBERANTE DE SALADILLO, en uso de sus atribuciones, acuerda y sanciona la siguiente
O R D E N A N Z A
ARTICULO 1º: Autorícese al Departamento Ejecutivo a suscribir un Convenio de Adhesión al Sistema de Atención Médica Organizada (SAMO) implementado por el Ministerio de Salud de la Provincia de Buenos Aires, conforme Decreto Ley 8801/77, reglamentado por el Decreto 1158/79 y sus modificatorias y defectos que de ellos se derivan.-
ARTICULO 2º: Queda comprendido en dicha adhesión cualquier servicio de atención médica que se realice en las siguientes Unidades Sanitarias: “San Roque”, Hipólito Teves, 31 de Julio; “Ariel Delía”, Saladillo Norte “Eduardo de Santibáñes”, Hilario Armendáriz, Asencio Ibarbia, Alvarez de Toledo, Polvaredas, Cazón, CAPS Móvil “Dra. Mabel Santiago” y Unidad Sanitaria de Del Carril, todos ellos dependientes de la Secretaría de Salud de la Municipalidad de Saladillo.-
ARTICULO 3º: Comuníquese al Departamento Ejecutivo, dése al Registro Oficial, cúmplase, publíquese y archívese.-
DADA EN LA SALA DE SESIONES DEL HONORABLE CONCEJO DELIBERANTE DE SALADILLO, a los ocho días del mes de octubre del año dos mil trece.-
ORDENANZA Nº 57/2013.-""",
    },
    {
        "numero": "17/2014",
        "titulo": "Ordenanza N° 17/2014",
        "texto": """Ordenanza N° 17/2014

DECLARAR LA INCOMPETENCIA DE LA SECRETARIA DE SALUD POR CARECER DE PERSONAL MEDICO Y PARAMEDICO EN LOS CAPS Y SALAS DE PRIMEROS AUXILIOS
VISTO el expediente nº 76/2014, iniciado por el Departamento Ejecutivo mediante expediente nº 135/2014, que eleva Decreto Nº 50/2014 ad-referendum del Honorable Cuerpo declarando la incompetencia de la Secretaría de Salud por carecer de personal médico y paramédico en los CAPS y Salas de Primeros Auxilios en el Partido de Saladillo;
que, el expediente nº 135/2014, iniciado por el Secretario de Salud;
que, mediante el expediente referenciado se informa que la Secretaría de Salud no cuenta con personal capacitado y habilitado para realizar las tareas inherentes a la prestación del Servicio Médico y Paramédico en los distintos Centros de Atención Primaria de la Salud (incluído el CAPS Móvil) y Salas de Primeros Auxilios del Partido de Saladillo;
que, conforme el planteo formulado, debe proceeder a declararse la incompetencia de la Secretaría en cuestión, autorizándose la contratación de personal calificado para realizar las mencionadas tareas; y
CONSIDERANDO que en la Tercera Sesión Ordinaria llevada a cabo el día 6 de mayo de 2014, este Honorable Cuerpo aprobó por unanimidad el despacho de la Comisión de Presupuesto y Hacienda que recomienda su convalidación;
por todo ello, el HONORABLE CONCEJO DELIBERANTE DE SALADILLO, en uso de sus atribuciones, acuerda y sanciona la siguiente
O R D E N A N Z A
ARTICULO 1º: Declárese la incompetencia de la Secretaría de Salud, por carecer de personal suficiente, para realizar las tareas inherentes a la prestación del Servicio Médico y Paramédico en los distintos Centros de Atención Primaria de la Salud (includio el CAPS Móvil) y Salas de Primeros Auxilios del Partido de Saladillo.-
ARTICULO 2º: Autorícese a la Oficina de Contaduría y a la Secretaría mencionada a contratar los profesionales, técnicos y demás personas que reúnan las condiciones, capacidades e ideoneidades propias de las funciones a realizar.-
ARTICULO 3º: Comuníquese al Departamento Ejecutivo, dése al Registro Oficial, cúmplase, publíquese y archívese.-
DADA EN LA SALA DE SESIONES DEL HONORABLE CONCEJO DELIBERANTE DE SALADILLO, a los seis días del mes de mayo del año dos mil catorce.-
ORDENANZA Nº 17/2014 .-""",
    },
    {
        "numero": "47/2019",
        "titulo": "Ordenanza N° 47/2019",
        "texto": """Ordenanza N° 47/2019

VISTO el expediente N°145/2019, iniciado por el Departamento Ejecutivo Municipal mediante expediente N°2385 /2019, quien eleva proyecto de Ordenanza sobre incompetencia de la Subsecretaría de Salud Pública para llevar a cabo tareas en los CAPS; 
VISTO el expediente N°145/2019, iniciado por el Departamento Ejecutivo Municipal mediante expediente N°2385 /2019, quien eleva proyecto de Ordenanza sobre incompetencia de la Subsecretaría de Salud Pública para llevar a cabo tareas en los CAPS;
que, mediante el Decreto N° 59/2019 se declaró la incompetencia de la Subsecretaría de Salud Pública y de la Secretaría de Gobierno, para llevar a cabo el desarrollo de las diferentes tareas de atención médica y de enfermería que se realiza en los distintos C.A.P.S. de la ciudad cabecera y de cuatro localidades del interior;
que, de acuerdo a los servicios que se prestan en los C.A.P.S. es necesario contar con personal con conocimientos médicos, para desempeñarse en horarios reducidos y días alternados;
que, si bien la Subsecretaría cuenta en su plantel con distintos profesionales (médicos, enfermeros, entre otros), los mismos se encuentran abocados a otras tareas, y para brindar la debida atención y cubrir las necesidades en la atención primaria de la salud, resulta necesario proceder a la contratación de personal idóneo en otras especialidades a saber: Médicos Clínicos, Pediatras, Ginecólogos, Fisiatras, Patólogos, Licenciados en Nutrición, Asistentes Geriátricos, Enfermeros, Licenciados en Fonoaudiología, Licenciados en Obstetricia, etc.;
que, doctrinariamente el Honorable Tribunal de Cuentas de la Provincia de Buenos Aires ha considerado factible la contratación de profesionales por parte del Departamento Ejecutivo, siempre que no se cuente con personal especializado o el existente se declare incompetente;
que, de acuerdo a lo dispuesto por el artículo 66° del Reglamento de Contabilidad y Disposiciones de Administración para las Municipalidades de la Provincia de Buenos Aires, este tipo de contrataciones por parte de la Municipalidad, serán considerados gastos especiales;
que, atento ello, resulta necesaria la intervención del Honorable Concejo Deliberante en un todo de acuerdo al artículo 32° de la ley Orgánica de las Municipalidades de la Provincia de Buenos Aires, no obstante lo cual, y dada la premura que merece la disposición del recurso humano mencionado, se procedió al dictado de un decreto ad referéndum autorizando la contratación en cuestión; y
CONSIDERANDO que en la Séptima Sesión Ordinaria, llevada a cabo el día 18 de junio de 2019, este Honorable Cuerpo aprobó por unanimidad el despacho de la Comisión de Presupuesto y Hacienda, que recomienda sancionar el mencionado proyecto;
por todo ello, el HONORABLE CONCEJO DELIBERANTE DE SALADILLO, en uso de sus atribuciones, acuerda y sanciona la siguiente
O R D E N A N Z A
ARTÍCULO 1°: Convalídese la declaración de incompetencia de la Subsecretaría de Salud Pública y de la Secretaría de Gobierno, efectuada mediante Decreto N° 59/2019 del Departamento Ejecutivo, por carecer de personal idóneo para el desarrollo de diferentes tareas de atención médica y de enfermería que se realiza en los distintos C.A.P.S. de la ciudad cabecera y de cuatro localidades del interior.-
ARTÍCULO 2°: Autorícense y apruébense los gastos de carácter especial originados por la contratación para el desarrollo de diferentes tareas de atención médica y de enfermería que se realiza en los distintos C.A.P.S. de la ciudad cabecera y de cuatro localidades del interior.-
ARTÍCULO 3°: Comuníquese al Departamento Ejecutivo Municipal, dése al Registro Oficial, cúmplase, publíquese y archívese.-
DADA EN LA SALA DE SESIONES DEL HONORABLE CONCEJO DELIBERANTE DE SALADILLO, a los dieciocho días del mes de junio del año dos mil diecinueve.-
ORDENANZA N°47/2019.-""",
    },
    {
        "numero": "72/2020",
        "titulo": "Ordenanza N° 72/2020",
        "texto": """Ordenanza N° 72/2020

VISTO el expediente n° 170/2020, iniciado por el Departamento Ejecutivo mediante expediente n° 3794/2020, quién eleva proyecto de Ordenanza referente a convalidar el Decreto 1825/2020, que adjudica el concurso de precios 39/2020 a la firma Edgar Raúl Álvarez, para la contratación de mano de obra y materiales para la Obra Ampliación del CAPS de Polvaredas;
que, el expediente 3536/2020, Letra I mediante el cual el Intendente Municipal, Ing. José Luis Salomón solicita elementos técnicos, cómputo y presupuesto para llevar a cabo la obra “Ampliación del C.A.P.S.- Centro de Atención Primaria de la Salud- de la Localidad de Polvaredas”;
que, el Subsecretario de Obras Públicas y Planeamiento, adjunta la documentación solicitada e informa que el presupuesto oficial para realizar dicha obra es de pesos un millón ciento treinta y tres mil setecientos dieciséis con veintidós centavos ($ 1.133.716,22.);
que, a fs. 1 del expediente 3794/J/2020 el Sr. Jefe de Compras solicita el inicio del Concurso de Precios N° 39/2020 para la contratación de mano de obra y materiales para la para llevar a cabo la obra “Ampliación del C.A.P.S.- Centro de Atención Primaria de la Salud- de la Localidad de Polvaredas”;
que, con fecha 06 de octubre de 2020 se dictó el Decreto n° 1657/2020 por medio del cual se llama a Concurso de Precios N° 39/2020;
que, se invitaron a participar a las siguientes empresas, a saber: Montarce Oscar Adolfo; Chaparro Benítez Oscar Alberto; Álvarez Edgar Raúl; Puesto Alto S.A.;
que, con fecha 21 de octubre del corriente año, se procedió al acto de apertura de sobres, habiéndose constatado lo siguiente:
que, no hubo objeciones al respecto;
que, con fecha 22 de octubre de 2020, la Directora de Obras y Proyectos, Arq. Anabella Fasano, se expide manifestando que la única firma que presentó oferta es Álvarez Edgar Raúl, con un valor de pesos un millón cuatrocientos veinte mil novecientos noventa ($ 1.420.990,00.-), siendo un % 25.33 superior al presupuesto oficial;
que, con fecha 26 de octubre de 2020, emite dictamen el Director de Asuntos Legales, Dr. Marcelo Dellatorre, quien manifiesta que es de destacar que en relación a las condiciones ofrecidas por los presentantes como así también respecto de los precios ofertados, el Municipio debe decidir conforme su interés, siempre respetando el principio de razonabilidad que debe guiar los actos de la Administración;
que, el artículo 154° de la Ley Orgánica de las Municipalidades dice que “en los concursos de precios y licitaciones la Municipalidad no estará obligada a aceptar ninguna propuesta…”;
que, asimismo expresa el Director de Asuntos Legales, que teniendo en cuenta el informe emitido el 22 de octubre por la Directora de Estudios y Proyectos, donde manifiesta que la única oferta presentada cumple con los plazos y condiciones establecidas en los pliegos y el porcentaje de su oferta que excede el presupuesto oficial se encuentra dentro de los parámetros aceptables, es que considera que, a la única firma que presenta oferta podría adjudicársele la obra, pudiendo hacerse ad referéndum del Honorable Concejo Deliberante;
que, siguiendo esa línea de pensamiento, mediante Decreto1825/2020 de fecha 29 de octubre de 2020 se adjudica, ad referéndum del Honorable Concejo Deliberante, el Concurso de Precios N° 39/2020 a la firma Álvarez Edgar Raúl; y
CONSIDERANDO que en la Décima Sesión Ordinaria, llevada a cabo el día 11 de noviembre de 2020, este Honorable Cuerpo aprobó por mayoría el despacho de la Comisión de Presupuesto y Hacienda, que aconseja sancionar el mencionado proyecto;
por todo ello, HONORABLE CONCEJO DELIBERANTE DE SALADILLO, en uso de sus atribuciones, acuerda y sanciona la siguiente
ARTÍCULO 1°: Convalidar el Decreto 1825/2020 mediante el cual se adjudica el Concurso de Precios N° 39/2020 a la firma Álvarez Edgar Raúl, que cotiza la suma de pesos un millón cuatrocientos veinte mil novecientos noventa ($ 1.420.990,00), para la contratación de mano de obra y materiales para la para llevar a cabo la obra “Ampliación del C.A.P.S.- Centro de Atención Primaria de la Salud- de la Localidad de Polvaredas”, por resultar conveniente a los intereses municipales.-
ARTÍCULO 2°: Comunicar al Departamento Ejecutivo Municipal, dar al Registro Oficial, publicar y archivar.-
DADA EN LA SALA DE SESIONES DEL HONORABLE CONCEJO DELIBERANTE DE SALADILLO, a los once días del mes de noviembre del año dos mil veinte.-
ORDENANZA N° 72/2020.-""",
    },
    {
        "numero": "24/2022",
        "titulo": "Ordenanza N° 24/2022",
        "texto": """Ordenanza N° 24/2022

VISTO el expediente N° 65/2022, iniciado por el Departamento Ejecutivo, mediante expediente N° 1625/2022, quién eleva proyecto de Ordenanza referente a crear el programa de “Acompañamiento Familiar 1.000 días Saladillo”;
que, las personas gestantes, su pareja y/o familia, tienen derecho a recibir la atención y la información necesaria para cuidar su salud y la de su hijo; como así también que los niños y adolescentes, sujetos de derechos, tienen, entre otros, el derecho a crecer y desarrollarse de manera saludable, para poder alcanzar todo su potencial y el Estado tiene la obligación de garantizar las condiciones para que puedan acceder a sus derechos;
que, sabemos por múltiples estudios avalados por distintas sociedades de pediatría y de acuerdo con informes de Unicef, que el proceso de desarrollo de los seres humanos comienza desde la concepción e implantación por técnica de reproducción humana asistida que implica una compleja interacción de las conexiones neuronales que van formándose a partir de la genética y la experiencia con el entorno. Es un proceso complejo de transformaciones que le permitirán al niño adquirir habilidades que permitan avanzar hacia su autonomía. Debe interpretarse desde una visión interdisciplinaria que englobe lo psicosocial y sobre todo lo cultural, así, cuando uno niño levanta la cabeza o descubre un objeto, lo que observamos es un comportamiento que se relaciona necesariamente y tiene que ver, con adultos, cuidados, afectos, alimentación, familia, barrio, costumbres y cultura, en un momento histórico dado;
que, la vida prenatal y la primera infancia son momentos fundamentales para la constitución subjetiva, la construcción de intersubjetividad, los primeros vínculos. Es un período corto pero muy sensible, crítico para el desarrollo cognitivo, y de las destrezas sociales y emocionales de las personas, las experiencias vividas en esta etapa afectarán de manera positiva o negativa la adultez. Para que las niñas y niños puedan crecer saludables, desarrollar integralmente su potencial, aprender y progresar necesitan un ambiente físico seguro, y socioemocional estable que los proteja y cuide y respete su dignidad como personas. Necesitan una nutrición adecuada, la promoción integral de la salud, crianza saludable y respetuosa, la estimulación positiva, vínculos amorosos, lo que facilita las oportunidades de aprendizaje temprano. Asegurar un desarrollo saludable, no sólo es beneficioso para cada individuo, pues disminuye sus posibilidades de enfermar/fallecer y le permite adquirir múltiples habilidades, sino que además promueve la interacción respetuosa con los otros, estimula vínculos positivos, aportando a la construcción de una sociedad más justa y solidaria, saludable;
que, dado la importancia del contexto, y los múltiples factores que influyen en el desarrollo infantil temprano, es necesario un enfoque multi-sectorial e interdisciplinario en el diseño de las políticas públicas destinadas a su cuidado;
que, desde la Dirección de Prevención y Promoción de la Salud y la Subsecretaría de Niñez, Adolescencias, Juventudes y Familia entendemos como Instituciones del Estado, preocuparnos y ocuparnos de aportar desde nuestras áreas a la construcción de entornos saludables para el crecimiento y desarrollo de los niños y adolescentes y acompañamiento a la familia. Creemos que la promoción del crecimiento y desarrollo en el embarazo y los primeros años debe ser considerado como un bien social, ya que como hemos explicado el cuidado en los primeros momentos de la vida son la base para la salud de los adultos y de la comunidad;
que, proponemos implementar el Programa “Acompañamiento Familiar 1000 días” (270 prenatales y 730 de los dos primeros años), que se amplían a los Programas de Promoción de la Salud Prenatal y de Promoción de la Salud de Niños y Adolescentes que se están desarrollando desde hace años en nuestros CAPS. Los complementa y enriquece al integrarlos en sus propuestas, profundiza en la atención integral de la salud siempre desde la perspectiva de derechos y de género, fortaleciendo a los distintos servicios municipales que intervienen transversalmente en el seguimiento del embarazo y la niñez;
que, el programa de “Acompañamiento Familiar 1000 días” propone el acompañamiento y asistencia a personas gestantes, madres/padres/adultos cuidadores de niños menores a dos años y niños hasta los dos años, que viven hoy en el Partido de Saladillo, a través de un conjunto de políticas públicas dirigidas a la atención integral para los primeros 1000 días de vida;
que, el mismo pone en el centro a los niños y niñas desde su gestación hasta los dos años de edad, así como también a la persona gestante, buscando garantizar y proteger sus derechos para su desarrollo pleno;
que, asimismo, los principios que guían la generación de esta política son el interés superior del niño, la efectividad, la igualdad y no discriminación, y el fortalecimiento del vínculo socio-familiar;
que, reconocer a los niños sujetos de derechos, implica que los adultos deben asumir la responsabilidad de hacer valer esos derechos, familia, comunidad e instituciones del estado;
que, consideramos fundamental apoyar a los adultos en esa labor: promover habilidades, capacidades y brindar herramientas a los cuidadores (madre/padre/adulto responsable/referente socio-comunitario), potenciar los recursos de las familias, y fortalecer vínculos y redes comunitarias;
que, entendemos que los Centros de Atención Primaria de la Salud, base de nuestro sistema de salud, son el lugar adecuado para desarrollar estas acciones. Son los CAPS los encargados de vencer las barreras de accesibilidad a la atención y de organizar pautas de cuidado de manera de garantizar el cumplimiento, seguimiento y la calidad de los controles en salud y la derivación oportuna acorde al riesgo;
que, el Equipo de trabajadores del Primer Nivel de Atención conoce a la población de su área programática y construye vínculos conjuntamente con las familias y los niños. Deben nominalizar las personas e incluirlas en distintos programas de atención y de promoción de la salud;
que, en el Centro de Salud, se atienden problemáticas de baja complejidad bio-tecnológica pero de alta complejidad psicosocial. Esta realidad nos marca la necesidad de mejorar nuestras intervenciones, capacitarnos permanentemente y trabajar en Equipo interdisciplinario e intersectorialmente, para brindar la mejor atención y aportar al desarrollo saludable del embarazo y los niños;
que, revaloriza las actividades de promoción y prevención como una herramienta fundamental del equipo de salud, de bajo costo y con una tremenda capacidad de impacto en la calidad de vida;
que, el Programa de Promoción de la salud del Niño, Niña y Adolescente y el Programa de Promoción de Salud Prenatal se complementan a este programa de manera integral; y
CONSIDERANDO que en la Cuarta Sesión Ordinaria, llevada a cabo el día 26 de abril de 2022, este Honorable Cuerpo aprobó por unanimidad el despacho de la Comisión de Desarrollo Social y Derechos Humanos, que aconseja sancionar el mencionado proyecto con modificaciones;
por todo ello, el HONORABLE CONCEJO DELIBERANTE DE SALADILLO, en uso de sus atribuciones, acuerda y sanciona la siguiente
ARTÍCULO 1°: Crear en el ámbito municipal el PROGRAMA DE ACOMPAÑAMIENTO FAMILIAR 1000 DÍAS SALADILLO, que dependerá de la Dirección de Prevención y Promoción de la Salud y la Subsecretaría de Niñez, Adolescencias, Juventudes y Familia, Secretaría de Gobierno, o la que en su momento la reemplace con similares facultades.-
ARTÍCULO 2°: El Programa contará con los siguientes ejes de abordaje:
–Promoción de la salud integral;
–alimentación y nutrición adecuada; y
–promoción de vínculos saludables, la estimulación temprana y el aprendizaje integral, el desarrollo y crecimiento infantil.-
ARTÍCULO 3°: Objetivo general:
promover cuidados integrales para mejorar la salud de las personas gestantes y los niños de hasta 3 años de vida del partido de Saladillo, entendiendo la salud como construcción colectiva
Objetivos específicos
Actividades
ARTÍCULO 4°: Plan de Actuación: Consulta de la persona gestante por primera vez; derivaciones a consultas multidisciplinarias, seguimiento acorde a lo propuesto en la “Guía de cuidados”. De igual manera se procederá en la atención a los menores de 2 años de edad.
La carga de las planillas de seguimiento de la persona gestante y la planilla de seguimiento de niños y niñas menores de dos años; organización de los turnos médicos de los CAPS, priorizando aquellas personas que se encuentren dentro del Programa.-
ARTÍCULO 5°: Equipos Técnicos Territoriales: El Programa se conforma del Equipo de área de género, crianza y diversidad, dependiente de la Subsecretaria de Niñez, Adolescencias, Juventudes y Familias, y diversos trabajadores de los CAPS: nutricionistas, psicólogos, obstetras, pediatras, trabajadoras sociales, enfermeros, promotores comunitarios, odontólogos, entre otros, dependientes de la Subsecretaría de Desarrollo Humano y de la Subsecretaría de Salud.
Articulación con el área de Primera Infancia de Jardines Maternales Municipales, a cargo de la Dirección de Educación.-
ARTÍCULO 6°: KIT: El Programa distribuirá a aquellas familias, que no cuenten con el Plan Qunita de ANSES, un kit municipal, que contendrá pañales, folletería, plan de actuación y libreta, chupete, termómetro, toalla para el bebé, ajuar recién nacido, cambiador, y apósitos post parto.–
ARTÍCULO 7°: PRESUPUESTO: El mismo queda a cargo de la Subsecretaría de Niñez, Adolescencias, Juventudes y Familias, y la Dirección de Prevención y Promoción de la Salud.-
ARTÍCULO 8°: Comunicar al Departamento Ejecutivo, dar al Registro Oficial, cumplir, publicar y archivar.-
DADA EN LA SALA DE SESIONES DEL HONORABLE CONCEJO DELIBERANTE DE SALADILLO, a los veintiséis días del mes de abril del año dos mil veintidós.-
ORDENANZA N° 24/2022.-""",
    },
]


def add_text_block(doc: Document, text: str) -> None:
    for line in text.splitlines():
        doc.add_paragraph(line)


def build_document() -> None:
    doc = Document()

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)

    title = doc.add_heading(
        "Compilado de Ordenanzas sobre CAPS, Centros de Salud y Primer Nivel de Atencion - Saladillo",
        level=0,
    )
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    subtitle = doc.add_paragraph(
        "Seleccion enfocada en ordenanzas directamente vinculadas con CAPS, organizacion del primer nivel, centros de salud y areas programaticas."
    )
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

    ordenanza_2014 = load_ordenanza_2014()
    ordenanza_2022 = next(item for item in ORDENANZAS if item["numero"] == "24/2022")
    full_list = [
        item
        for item in ORDENANZAS
        if item["numero"] not in {"66/2007", "24/2022"}
    ] + [ordenanza_2014, ordenanza_2022]

    doc.add_paragraph()
    doc.add_heading("Indice", level=1)
    for ordenanza in full_list:
        doc.add_paragraph(f"- {ordenanza['titulo']}")

    for index, ordenanza in enumerate(full_list, start=1):
        doc.add_page_break()
        heading = doc.add_heading(f"{index}. {ordenanza['titulo']}", level=1)
        heading.alignment = WD_ALIGN_PARAGRAPH.LEFT
        add_text_block(doc, ordenanza["texto"])

    doc.save(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
    print(f"Documento Word generado: {OUTPUT_PATH}")
