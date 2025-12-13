1. INTRODUCCIÓN. 
En los últimos años, el análisis biomecánico mediante visión artificial se ha consolidado como una 
alternativa viable y de bajo costo para evaluar el movimiento humano. Investigaciones recientes han 
explorado diversas implementaciones tecnológicas con este enfoque. Vargas Guevara et al. 2021 
(Vargas Guevara et al., 2021) desarrollaron un sistema embebido con Raspberry Pi y OpenCV para 
estimar posturas corporales en tiempo real mediante imágenes binarizadas, destacando su portabilidad, 
aunque limitado por la capacidad de procesamiento. Pillapa Llerena ((Pillapa Llerena, 2022)) diseñó un 
prototipo para el análisis de marcha utilizando MediaPipe, que permitió visualizar ángulos articulares, 
condicionado por factores como la iluminación y oclusiones. Aillón Orbe y Álvarez Riofrío (2024) 
implementaron un sistema óptico de captura con cámaras OptiTrack en un entorno académico, logrando 
alta precisión en la medición de rangos articulares, con restricciones de costo y espacio. Por su parte, 
Lafayette et al. 2023 (T. B. de G. Lafayette et al., 2023) validaron el uso de MediaPipe y Kinect V2 frente 
al sistema Qualisys, obteniendo resultados comparables a los de instrumentos clínicos, con limitaciones 
en la estimación de profundidad. 
El presente proyecto se desarrollará en la Universidad del Valle, en la ciudad de Cochabamba, dentro 
de la asignatura de Biomecánica de la carrera de Ingeniería Biomédica. Este espacio académico resulta 
adecuado para implementar herramientas tecnológicas que refuercen la comprensión de contenidos 
teóricos mediante experiencias prácticas. 
Durante el diagnóstico inicial, se identificó una dificultad en los estudiantes para comprender conceptos 
biomecánicos, especialmente los relacionados con los rangos de movimiento articular. Actualmente, se 
emplean herramientas como Kinovea, que si bien son accesibles, dependen de grabaciones previas y 
del uso de marcadores físicos, lo cual restringe la interacción en tiempo real y se limita a las habilidades 
del usuario. Esta situación afecta tanto la asimilación de la teoría como el desarrollo de habilidades 
prácticas, y reduce el interés de los estudiantes por vincular la biomecánica con otras áreas tecnológicas 
como la visión artificial o la robótica. 
Frente a esta situación, el proyecto propone el desarrollo de un sistema de análisis biomecánico de 
rangos de movimiento articular mediante visión artificial, con un enfoque pedagógico. Esta herramienta 
permitirá a los estudiantes observar, registrar y analizar sus movimientos articulares, facilitando el 
aprendizaje práctico y la retroalimentación individual. Asimismo, se busca fomentar el interés por 
tecnologías aplicadas en el área biomédica, promoviendo un aprendizaje contextualizado y 
participativo.  
2. PLANTEAMIENTO DEL PROBLEMA. 
En la carrera de Ingeniería Biomédica de la Universidad del Valle, ubicada en la ciudad de Cochabamba, 
se imparte la asignatura de Biomecánica con sesiones teóricas y prácticas contempladas en su 
programa analítico. Sin embargo, la materia no cuenta con un laboratorio específico, y las actividades 
prácticas se basan en el análisis manual de fotografías y videos, o que hace que los resultados 
dependan de las habilidades y criterios del usuario. 
Como consecuencia, no es posible obtener mediciones consistentes, debido a la falta de control sobre 
variables como la perspectiva o la posición de la cámara. En una entrevista semiestructurada orientada 
a la identificación de necesidades y limitaciones técnicas en la enseñanza práctica de biomecánica, la 
docente entrevistada manifestó que “el problema de esas herramientas es que, si no se coloca bien la 
cámara, los datos salen mal”, evidenciando la ausencia de procedimientos técnicos básicos 
estandarizados y la necesidad de herramientas replicables que favorezcan la consistencia en la 
observación de los rangos articulares. Esta situación repercute especialmente en las unidades 
centradas en la anatomía funcional, donde es necesario comprender de manera aplicada la relación 
entre estructura, movimiento y función. 
La falta de recursos interactivos para observar el comportamiento articular desde un enfoque práctico 
limita la comprensión de los conceptos biomecánicos, reduce la motivación y dificulta la vinculación 
entre teoría y práctica, impidiendo que los estudiantes se involucren de forma activa con su propio 
cuerpo como instrumento de estudio. 
2.1 FORMULACIÓN DEL PROBLEMA. 
¿Qué tipo de solución educativa basada en tecnologías de captura visual podría mejorar la comprensión 
práctica de los rangos articulares en la asignatura de Biomecánica en la Universidad del Valle? 
2.2 ÁRBOL DEL PROBLEMA. 
Figura 1. Árbol del problema 
Fuente: Elaboración propia, 2025. 
3. JUSTIFICACIÓN. 
3.1  JUSTIFICACIÓN TÉCNICA 
En el ámbito educativo de la biomecánica, es necesario contar con herramientas que permitan observar 
y analizar el movimiento humano de forma controlada y repetible, favoreciendo la comprensión de los 
conceptos teóricos. La implementación de tecnologías para la captura y el procesamiento de imágenes 
posibilita generar representaciones útiles para la enseñanza, reduciendo la dependencia de métodos 
altamente manuales. 
La viabilidad técnica del proyecto se sustenta en la disponibilidad de herramientas de código abierto 
para visión artificial, métodos de estimación angular aplicados en contextos académicos y componentes 
de bajo costo que pueden integrarse sin requerir infraestructura especializada. Estas condiciones 
permiten desarrollar soluciones adaptadas a entornos de enseñanza, con procedimientos replicables y 
de fácil implementación, lo que facilita la comprensión práctica de conceptos biomecánicos. 
3.2 JUSTIFICACIÓN ACADÉMICA 
El aprendizaje basado en la experiencia e interacción corporal favorece la asimilación de conceptos 
complejos como los rangos articulares y la dinámica del movimiento humano. Al analizar su propio 
cuerpo, el estudiante conecta la teoría con sensaciones y observaciones directas, integrando procesos 
cognitivos que fortalecen la comprensión y retención del conocimiento. Este enfoque pedagógico 
permite que la biomecánica deje de ser un concepto abstracto para ser una experiencia tangible.  
La documentación técnica generada podrá ser utilizada como referencia en investigaciones futuras 
relacionadas con tecnologías educativas y análisis biomecánico. Dado su carácter replicable y 
escalable, el sistema puede adaptarse a otros entornos académicos y evolucionar con mejoras 
posteriores, ampliando sus posibilidades de uso. 
3.3 JUSTIFICACIÓN ECONÓMICA 
La mayoría de los sistemas comerciales de captura de movimiento de alta precisión, como Vicon o 
Qualisys, requieren múltiples cámaras sincronizadas y licencias de software especializadas, lo que 
genera costos que suelen superar los 20.000 dólares para configuraciones estándar de 6 a 12 cámaras 
(Grebler, 2011; K. Lafayette et al., 2023). Sin embargo, existen sistemas con menor número de 
cámaras, como configuraciones con 2 a 4 cámaras Kinect o Intel RealSense, que reducen la inversión 
inicial a rangos entre 1.000 y 5.000 dólares aproximadamente, manteniendo una medición adecuada 
para análisis básicos y aplicaciones clínicas o deportivas (Salguero, 2018; K. Lafayette et al., 2023). 
Por otro lado, las soluciones de bajo costo se basan en una sola cámara convencional y software libre 
o económico, como Kinovea o MediaPipe, que permiten análisis en 2D o con estimación 3D limitada. 
Estos sistemas quitan la necesidad de licencias y múltiples dispositivos, ofreciendo costos usualmente 
por debajo de 500 dólares (incluyendo hardware básico) (K. Lafayette et al., 2023; Salguero, 2018).  
4. OBJETIVOS 
4.1 OBJETIVO GENERAL 
Desarrollar un sistema de análisis biomecánico en un plano, basado en visión artificial, para estimar 
rangos de movimiento articular con fines didácticos en la asignatura de Biomecánica de la carrera de 
Ingeniería Biomédica de la Universidad Privada del Valle. 
4.2 OBJETIVOS ESPECÍFICOS 
• Analizar los rangos articulares funcionales de miembros inferiores y superiores, así como las 
técnicas de visión artificial aplicables, con el fin de sustentar el diseño del sistema educativo 
orientado al análisis biomecánico. 
• Diseñar el modelo funcional del sistema, estructurando sus módulos de adquisición de datos, 
procesamiento de movimiento articular, visualización gráfica y soporte físico articulado,  orientado al uso en entornos de formación en biomecánica. 
• Desarrollar el algoritmo de estimación de ángulos articulares mediante triangulación de puntos 
anatómicos obtenidos por visión artificial, e integrar una interfaz interactiva para la visualización  en tiempo real del movimiento. 
• Comparar los valores angulares generados por el sistema con datos obtenidos por goniómetro 
manual, a fin de verificar su aplicabilidad en contextos educativos. 
• Realizar pruebas de campo en sesiones controladas de enseñanza práctica de biomecánica. 
5. Marco Teorico (en mi perfil pondre)
6. PROPUESTA. 
El diagrama de bloques representada en la Figura 3, muestra la arquitectura funcional de un sistema 
educativo orientado al análisis de rangos articulares. El proceso inicia con la captura de video mediante 
una cámara montada sobre un trípode motorizado, cuyo posicionamiento se ajusta automáticamente 
desde un microcontrolador. 
La señal de video es procesada en una unidad central, donde se detectan los puntos articulares, se 
calculan los ángulos y se determina el rango de movimiento. Estos datos se comparan con valores de 
referencia obtenidos de una base de datos para clasificar el desempeño del usuario. 
La interfaz facilita seleccionar la articulación a evaluar, visualizar ejemplos, controlar el trípode, capturar 
el movimiento y recibir retroalimentación. Finalmente, los resultados se almacenan junto con el historial 
del usuario, lo que permite seguimiento y repetibilidad en futuras sesiones. 
Figura 3. Diagrama de bloques 
Fuente: Elaboración propia, 2025. 
6.1 ALCANCES 
• Se desarrollará una interfaz funcional, en formato de aplicación de escritorio o plataforma web, 
que permita visualizar en tiempo real los ángulos articulares estimados mediante una cámara. 
• El sistema mostrará una representación 2D, identificando articulaciones y segmentos 
corporales, y calculará los ángulos articulares a partir de tres puntos anatómicos por articulación. 
• Se incluirá retroalimentación visual simple, mediante mensajes o indicadores de color, que 
informen si los ángulos registrados se encuentran dentro o fuera de los rangos de movimiento 
establecidos según literatura biomecánica. 
• El análisis se centrará en el rango de movimiento de hombro, codo, cadera, rodilla y tobillo, 
priorizando patrones básicos en un plano, como flexión, extensión, abducción y aducción. 
• Los datos angulares serán segmentados por articulación y organizados estructuradamente para 
su análisis comparativo con valores de referencia. 
• El sistema será probado con estudiantes sanos durante sesiones prácticas de la asignatura de 
biomecánica, en un entorno académico controlado. 
• Se analizarán de dos a tres ejercicios por segmento corporal, seleccionados por su utilidad 
pedagógica y viabilidad técnica para la detección con cámara. 
• Se incorporará un mecanismo motorizado de ajuste vertical que permitirá posicionar la cámara 
según el segmento a analizar. Las posiciones configuradas podrán guardarse para ser 
reutilizadas en futuras sesiones con el mismo ejercicio. 
6.2 LIMITACIONES 
• El sistema estará diseñado para operar con una única cámara convencional, ubicada en posición 
frontal, sin integración de cámaras de profundidad, sensores inerciales, ni hardware adicional. 
• La estimación de los ángulos articulares se realizará exclusivamente en dos dimensiones y por 
plano, sin análisis tridimensional ni evaluación de movimientos fuera del plano frontal o máximo 
sagital. 
• El sistema detectará y analizará el movimiento de una sola persona por sesión, sin soporte para 
usuarios múltiples ni seguimiento simultáneo. 
• El prototipo se ejecutará en una computadora personal sin requerimientos de procesamiento 
gráfico avanzado, limitando su uso a dispositivos de uso general. 
• El ajuste del encuadre de la cámara se restringirá al eje vertical, mediante un mecanismo 
motorizado de altura, sin control automatizado de rotación horizontal ni seguimiento dinámico. 
• El análisis se limitará a ejercicios simples en un único plano, como flexión, extensión, abducción 
y aducción, sin contemplar combinaciones complejas de movimiento ni análisis cinemático 
completo. 
18 
• El sistema estará destinado exclusivamente a fines educativos, por lo que no incluirá 
funcionalidades clínicas como análisis de compensaciones posturales, estimación de fuerzas ni 
reconstrucción tridimensional, y no será apto para diagnóstico o aplicación terapéutica. 
• La verificación se realizará únicamente mediante comparación con rangos articulares de 
referencia provenientes de literatura especializada y verificación con goniómetro manual, sin 
instrumentos clínicos de alta precisión. 
• Los valores utilizados no serán personalizados; se aplicarán rangos promedio, sin diferenciación 
por sexo, edad, morfología ni condición física. 
• La interfaz será de tipo académico, con diseño funcional básico, sin conexión a plataformas 
externas, ni servidores remotos. 
• El uso del sistema se limitará a entornos controlados como aulas o laboratorios universitarios, 
sin aplicabilidad en contextos clínicos, domiciliarios o deportivos. 
7. METODOLOGÍA. 
7.1 ENFOQUE DE INVESTIGACIÓN. 
El presente proyecto adopta un enfoque cuantitativo, al basarse en la recolección y análisis de datos 
numéricos sobre rangos de movimiento articular mediante técnicas de visión artificial. A partir de 
coordenadas articulares extraídas por el sistema, se calcularán ángulos que serán comparados con 
valores biomecánicos generales de referencia, con el propósito de evaluar de forma objetiva la 
movilidad funcional de los segmentos corporales para uso pedagógico. 
7.2 TIPO DE INVESTIGACIÓN. 
El presente proyecto adopta un tipo de investigación descriptivo y exploratorio. En su carácter 
descriptivo, se enfoca en detallar los componentes técnicos y computacionales del sistema 
educativo diseñado para el análisis de rangos articulares mediante visión artificial, incluyendo su 
estructura, algoritmos y forma de visualización de resultados. 
A nivel exploratorio, se aborda un campo poco desarrollado en el contexto universitario local: el uso 
de herramientas basadas en visión artificial con fines didácticos en biomecánica. Se evaluará la 
viabilidad técnica y el uso práctico del sistema en entornos reales de aula, así como su accesibilidad 
para estudiantes sin experiencia previa en programación o análisis del movimiento. 
7.3 MÉTODOS DE INVESTIGACIÓN. 
A lo largo del desarrollo del proyecto se integran diversos métodos de investigación que permiten 
abordar el análisis desde una perspectiva estructurada y práctica. En primer lugar, se emplea el 
método analítico para descomponer el sistema en sus componentes fundamentales, como el 
software, los algoritmos de estimación angular y los parámetros biomecánicos considerados. A partir 
de esta base, se recurre al método de modelación, mediante el cual se construye una representación 
funcional del proceso de medición articular, emulando de forma digital lo que convencionalmente se 
realiza con un goniómetro. Durante las pruebas implementadas en el entorno académico, se 
incorpora el método de observación, orientado a identificar posibles limitaciones técnicas o de 
usabilidad percibidas por los estudiantes. Finalmente, se aplica el método de medición para obtener 
y comparar los ángulos articulares generados por el sistema a partir de coordenadas espaciales, 
contrastándolos con rangos de referencia previamente establecidos. Esta combinación 
metodológica favorece una evaluación integral del sistema desde el diseño hasta su aplicación 
práctica. 
7.4 TÉCNICAS  
El proyecto recurre a una combinación de técnicas que permiten sustentar tanto el diseño como la 
funcionalidad del sistema propuesto. En primer lugar, se emplea la técnica documental, mediante 
una revisión de literatura especializada en biomecánica articular, rangos de movimiento y 
metodologías de estimación postural basadas en visión artificial, lo cual proporciona el respaldo 
teórico necesario. En una fase aplicada, se implementa la técnica de trabajo de campo, realizando 
pruebas experimentales en aula con estudiantes de la asignatura de Biomecánica, con el objetivo 
de evaluar el desempeño del sistema en un contexto educativo. Paralelamente, se incorpora la 
técnica de medición, a través de la cual se obtienen los datos angulares generados a partir de las 
coordenadas articulares detectadas por el sistema, los cuales son contrastados con valores de 
referencia. Finalmente, se aplica la técnica de cálculo, centrada en el desarrollo e implementación de algoritmos geométricos para la estimación automática de ángulos articulares dentro del software. 
7.5 POBLACIÓN 
La población del proyecto está conformada por estudiantes de Ingeniería Biomédica que cursan la asignatura de Biomecánica, en quienes se enfoca el desarrollo y aplicación del sistema educativo de análisis articular. 
7.6 MUESTRA 
La muestra fue determinada aplicando la fórmula para el cálculo de tamaño muestral en el caso de población finita, ya que se conoce el total de estudiantes inscritos en una de las clases de la asignatura de Biomecánica (N = 30). Se utilizaron los siguientes parámetros: 
• Nivel de confianza: 95 % (Z = 1.96) 
• Probabilidad de éxito: p = 0.5 
• Probabilidad de fracaso: q = 1−p = 0.5 
• Error máximo admisible: d = 0.06 
La fórmula utilizada fue: 
Sustituyendo los valores: 
n = 𝑁⋅𝑍2⋅𝑝⋅𝑞
𝑑2∗(𝑁−1)+𝑍2∗𝑝∗𝑞
𝑛 = 30⋅1.962⋅0.5⋅0.5
0.062∗(30−1)+1.962∗0.5∗0.5 = 28.32/1.0475 ≈27.06 
Por lo tanto, el tamaño de muestra calculado es de 27 estudiantes. 
7.7 MUESTREO 
El tipo de muestreo empleado fue no probabilístico por conveniencia, dado que los participantes serán seleccionados en función de su disponibilidad y participación en las sesiones prácticas de aula. 
7.8 FUENTES DE INVESTIGACIÓN. 
La investigación se apoya en fuentes primarias, secundarias y terciarias, de acuerdo con la naturaleza técnica y aplicada del proyecto. 
• Fuentes primarias: Comprenden libros enfocados en biomecánica y visión artificial, así como los datos generados directamente durante las pruebas del sistema con estudiantes en aula. 
• Fuentes secundarias: Incluyen artículos científicos, recursos digitales y documentos que sintetizan o analizan información sobre estimación posturaly algoritmos de detección articular. 
• Fuentes terciarias: Se utilizaron listados bibliográficos y bases de datos organizadas en gestores como Mendeley para ubicar y clasificar las referencias relevantes al proyecto.


#contenido de mi documento actual (que aun tengo que mejorar y actualizar con este sistema mas estable, pero la idea es la misma):
ÍNDICE DE CONTENIDO 
INTRODUCCIÓN 
CAPITULO I 
MARCO TEORICO 
1.1 FUNDAMENTOS DE LA BIOMECÁNICA Y MOVIMIENTO HUMANO .............1 
1.1.1 PLANOS Y EJES ANATÓMICOS ...................................................................2 
1.1.2 TIPOS DE ARTICULACIONES Y GRADOS DE LIBERTAD ...........................4 
1.1.3 RANGO DE MOVIMIENTO ARTICULAR Y SU EVALUACIÓN .......................5 
1.2 ANATOMÍA FUNCIONAL Y BIOMECÁNICA ARTICULAR ..............................6 
1.2.1 ARTICULACIÓN DEL HOMBRO ....................................................................6 
1.2.2 ARTICULACIÓN DEL CODO .........................................................................8 
1.2.3 ARTICULACIÓN DE LA CADERA ..................................................................9 
1.2.4 ARTICULACIÓN DE LA RODILLA ................................................................ 10 
1.2.5 ARTICULACIÓN DEL TOBILLO ................................................................... 11 
1.3 ALTERACIONES BIOMECÁNICAS FUNCIONALES COMUNES .................. 13 
1.3.1 PATRONES COMPENSATORIOS EN MIEMBROS SUPERIORES ............. 13 
1.3.2 PATRONES COMPENSATORIOS EN MIEMBROS INFERIORES .............. 14 
1.3.3 IMPLICANCIAS CLÍNICAS Y PEDAGÓGICAS............................................. 15 
1.4 ARQUITECTURA GENERAL DEL SISTEMA DE ANALISIS BIOMECANICO 
DEL ROM (BIOTRACK) ................................................................................................... 15 
1.4.1 Descripción general del sistema ................................................................... 16 
1.4.2 Diagrama funcional de referencia ................................................................. 17 
1.4.3 Comparación con proyectos similares .......................................................... 18 
1.4.4 Estado del arte didáctico en biomecánica ..................................................... 19 
1.5 VISIÓN ARTIFICIAL APLICADA AL ANÁLISIS DEL MOVIMIENTO .............. 20 
1.5.1 HISTORIA DE LA CAPTURA DE MOVIMIENTO .......................................... 21 
1.5.2 CLASIFICACIÓN DE LOS SISTEMAS DE CAPTURA DE MOVIMIENTO .... 21 
1.5.3 SISTEMAS DE BAJO COSTO Y ACCESIBILIDAD ...................................... 22 
1.6 MÉTODOS DE VALIDACIÓN DE ESTIMACIÓN ANGULAR .......................... 22 
1.6.1 COMPARACIÓN CON GONIOMETRÍA MANUAL ........................................ 23 
1.6.2 COMPARACIÓN CON SISTEMAS DE CAPTURA ÓPTICA DE REFERENCIA
 23 
1.6.3 CRITERIOS DE CONCORDANCIA Y ERROR ACEPTABLE ....................... 24 
1.7 Normativas técnicas y estándares aplicables ............................................. 24 
 
 
1.7.1 Normas de usabilidad e interacción .............................................................. 25 
1.7.2 Estándares de software educativo y accesibilidad ........................................ 25 
1.8 HARDWARE ................................................................................................... 25 
1.8.1 SoC ESP32 .................................................................................................. 25 
1.8.2 MÓDULO LM2596 ........................................................................................ 26 
1.8.3 SERVOMOTOR MG995 ............................................................................... 27 
1.8.4 MÓDULO MPU6050 ..................................................................................... 28 
1.8.5 CÁMARA WEB Shcngqio TWC29 ................................................................ 29 
1.8.6 MOTORREDUCTOR DC CQRobot serie CQR37D ...................................... 31 
1.9 SOFTWARE .................................................................................................... 32 
1.9.1 LENGUAJE DE PROGRAMACIÓN PYTHON............................................... 32 
1.9.2 BIBLIOTECA OPENCV ................................................................................ 32 
1.9.3 FRAMEWORK MEDIAPIPE .......................................................................... 33 
1.9.4 FRAMEWORK WEB FLASK ......................................................................... 35 
1.10 BASES DE DATOS ......................................................................................... 36 
1.10.1 MOTOR DE BASE DE DATOS SQLITE ................................................. 36 
CAPITULO II 
DIAGNÓSTICO SITUACIONAL 
2.1 INTRODUCCIÓN ............................................................................................. 39 
2.2 CONTEXTO DEL LUGAR O ENTIDAD ........................................................... 39 
2.2.1 IDENTIFICACIÓN GENERAL ....................................................................... 39 
2.2.2 ÁREA AFECTADA POR EL PROBLEMA ..................................................... 39 
2.2.3 RECURSOS ACTUALES ............................................................................. 40 
2.3 EVIDENCIAS DEL PROBLEMA ..................................................................... 41 
2.3.1 Observación directa ...................................................................................... 41 
2.3.2 Encuestas ..................................................................................................... 42 
2.3.3 Entrevista ..................................................................................................... 50 
2.3.4 Análisis crítico del diagnóstico ...................................................................... 50 
2.3.5 Conclusiones del diagnóstico ....................................................................... 51 
3.1 CARACTERÍSTICAS GENERALES DEL PROYECTO ................................... 53 
3.1.1 DESCRIPCIÓN GENERAL DEL FUNCIONAMIENTO DEL SISTEMA ......... 53 
3.2 SISTEMA MECÁNICO .................................................................................... 55 
3.2.1 SERVOMOTORES ....................................................................................... 56 
 
 
3.2.2 PIEZAS ESTRUCTURALES IMPRESAS EN 3D .......................................... 59 
3.2.3 SOPORTE UNIVERSAL DE CÁMARA ......................................................... 62 
3.2.4 ESTRUCTURA DE BASE METÁLICA .......................................................... 62 
3.2.5 SISTEMA DE DESPLAZAMIENTO VERTICAL MOTORIZADO ................... 62 
3.2.6 ESTRUCTURA, ALTURA, PESO Y MATERIALES ....................................... 67 
CAPITULO III 
INGENIERÍA DE PROYECTO 
3.3 DISEÑO DEL HARDWARE DEL PROYECTO ................................................ 69 
3.3.1 Diseño electrónico del módulo de control ..................................................... 69 
3.3.2 CÁMARA DE PROCESAMIENTO ................................................................ 75 
3.3.3 Accionamiento vertical motorizado ............................................................... 76 
3.3.4 FUENTE DE ALIMENTACIÓN ...................................................................... 77 
3.3.5 Cálculo de Autonomía Estimada ................................................................... 78 
3.4 FIRMWARE DEL SISTEMA ELECTRÓNICO DEL PROYECTO ..................... 79 
3.4.1 Ajuste y verificación del Sensor MPU6050 ................................................... 82 
3.4.2 Control de altura en el eje vertical ................................................................ 83 
3.5 DESARROLLO DE LA APLICACIÓN ............................................................. 86 
3.5.1 Descripción Y ARQUITECTURA General de la Aplicación ........................... 86 
3.5.2 Frameworks Backend ................................................................................... 88 
3.5.3 sistema de visión artificial del proyecto ......................................................... 89 
3.5.4 Enfoque de Interfaz de Usuario .................................................................... 90 
3.5.5 DESARROLLO DE LA APLICACIÓN DE USUARIO .................................... 91 
3.5.6 Interacción del Sistema ................................................................................ 92 
3.5.7 CASOS DE USO DE LA APLICACIÓN DE USUARIO .................................. 94 
3.5.8 Procesamiento de Video y Cálculos Biomecánicos ...................................... 99 
3.5.9 WIREFRAME PARA EL DISEÑO DE LA INTERFAZ GRAFICA ................. 101 
3.5.10 Decisiones Clave de Diseño UX ........................................................... 107 
3.5.11 Mapa de Navegación de la Aplicación Web BioTrack ........................... 108 
3.5.12 BASE DE DATOS................................................................................. 108 
3.6 COSTO DEL PROYECTO ............................................................................. 111 
CAPITULO IV 
RESULTADOS Y DISCUSIÓN 
4.1 INTRODUCCIÓN DEL CAPÍTULO ................................................................ 114 
 
 
4.2 PRESENTACIÓN DE LOS RESULTADOS ................................................... 115 
4.2.1 SISTEMA ELECTRÓNICO (HARDWARE) ................................................. 115 
4.2.2 SISTEMA MECÁNICO ................................................................................ 116 
4.2.3 INTERFAZ DEL USUARIO ......................................................................... 117 
4.3 PRUEBAS REALIZADAS AL SISTEMA ....................................................... 127 
4.3.1 PRUEBAS TÉCNICAS DE FUNCIONAMIENTO ........................................ 127 
4.3.2 EXPERIENCIA DE USUARIO .................................................................... 137 
4.3.3 NÚMERO DE FALLAS Y OBSERVACIONES ............................................ 145 
4.4 RESULTADOS EN CONTEXTO DE PRUEBAS DE CAMPO ....................... 145 
4.5 DISCUSIÓN DE LOS RESULTADOS ........................................................... 147 
CONCLUSIONES ........................................................................................................... 152 
RECOMENDACIONES ................................................................................................... 154 
REFERENCIAS BIBLIOGRÁFICAS ............................................................................... 156 
APÉNDICE ..................................................................................................................... 158 
ANEXOS ........................................................................................................................ 187


#Indices de lo que tengo en mi documento para que tengas idea que es lo que tengo y pensar y analizar que es lo mas importante que necesito presentar en mi presentacion?:
ÍNDICE DE FIGURAS 
Figura 1.1. Planos y ejes de movimiento ................................................................................2 
Figura 1.2. Medición del ROM con goniómetro manual. .........................................................5 
Figura 1.3. Articulación hombro. .............................................................................................7 
Figura 1.4. Articulación codo. .................................................................................................8 
Figura 1.5. Articulación cadera. ..............................................................................................9 
Figura 1.6. Articulación rodilla. ............................................................................................. 11 
Figura 1.7. Articulación tobillo ............................................................................................... 12 
Figura 1.8 Diagrama funcional de referencia para un sistema de análisis biomecánico basado 
en visión artificial. .................................................................................................................. 17 
Figura 1.9. Comparación del ROM con goniómetro manual vs visión Artificial ...................... 23 
Figura 1.10. ESP32-WROOM ............................................................................................... 26 
Figura 1.11. Módulo LM2596 ................................................................................................ 27 
Figura 1.12. Servomotor MG995 .......................................................................................... 28 
Figura 1.13. Módulo MPU6050 ............................................................................................. 29 
Figura 1.14. Cámara web Shcngqio TWC29......................................................................... 30 
Figura 1.15. Definición de puntos de referencia en MediaPipe Pose .................................... 33 
 
Figura 2.1 Vista general del aula donde se desarrollan actualmente las prácticas de 
Biomecánica.......................................................................................................................... 40 
Figura 2.2 Registro del desarrollo de una práctica de medición articular con Kinovea. ......... 40 
Figura 2.3 Registro manual de ángulos articulares en Kinovea durante una práctica de 
Biomecánica. ......................................................................................................................... 41 
Figura 2.4 Ejemplo de variación en la posición de cámara utilizada por los estudiantes durante 
la captura de movimiento. ..................................................................................................... 42 
 
Figura 3.1 Diagrama de bloques del sistema BioTrack ......................................................... 53 
Figura 3.2 Sistema de mecanismos y componentes diseñados ............................................ 56 
Figura 3.3 Análisis de tensiones de Von Mises del soporte del servomotor horizontal .......... 60 
Figura 3.4 Estudio de desplazamientos del soporte del servomotor horizontal ..................... 60 
Figura 3.5 Análisis de tensiones de Von Mises del soporte de componentes electrónicos. .. 60 
Figura 3.6 Estudio de desplazamientos del soporte de componentes electrónicos. .............. 61 
Figura 3.7 Análisis de tensiones de Von Mises de la plataforma de rotación ........................ 61 
Figura 3.8 Estudio de desplazamientos del soporte de la plataforma de rotación ................. 61 
 
 
Figura 3.9 Análisis de tensiones de Von Mises del soporte del sistema ............................... 65 
Figura 3.10 Estudio de desplazamientos del soporte del sistema ......................................... 65 
Figura 3.11 Análisis de tensiones de Von Mises de la estructura ......................................... 66 
Figura 3.12 Estudio de desplazamientos de la estructura ..................................................... 67 
Figura 3.13 Medidas Estructura Soporte Cámara ................................................................. 68 
Figura 3.14 Funcionamiento del Indicador de 4 Niveles........................................................ 72 
Figura 3.15 Divisor de Voltaje DC con funcionamiento bajo carga. ....................................... 73 
Figura 3.16 Diagrama esquemático control ESP32. ............................................................. 74 
Figura 3.17 Diseño de la placa PCB del módulo de control. ................................................. 75 
Figura 3.18 Diagrama de flujo del Firmware de control embebido para cámara.  ................. 80 
Figura 3.19 Diagrama de Secuencia de Comunicación entre Componentes del Firmware ... 81 
Figura 3.20 Diagrama de Arquitectura General del Sistema BioTrack. ................................. 87 
Figura 3.22 Diagrama Secuencial del Proceso de Análisis Biomecánico Completo. ............. 93 
Figura 3.23 Diagrama Secuencial: Estudiante Realiza Análisis Biomecánico ....................... 95 
Figura 3.24 Diagrama Secuencial: Administrador Crea Usuario ........................................... 96 
Figura 3.25 Diagrama Secuencial: Administrador Crea Usuario ........................................... 97 
Figura 3.26 Diagrama Secuencial: Consulta Global y Exportación de Análisis por 
Administrador ........................................................................................................................ 99 
Figura 3.27 Procesamiento de Frames para Estimación Articular. ...................................... 100 
Figura 3.28 Wireframe de inicio de sesión .......................................................................... 101 
Figura 3.29 Wireframe de pestaña de Inicio ....................................................................... 102 
Figura 3.30 Wireframe de pestaña de Segmentos/Ejercicios .............................................. 103 
Figura 3.31 Wireframe de segmento seleccionado ............................................................. 104 
Figura 3.32 Wireframe de ventana de inicio de análisis ...................................................... 104 
Figura 3.33 Wireframe de pestaña de Perfil........................................................................ 105 
Figura 3.34 Wireframe de pestaña de Reportes ................................................................. 106 
Figura 3.35 Wireframe de pestaña de Admin ...................................................................... 106 
Figura 3.36 Decisiones de Diseño UX y Justificación Técnico-Biomecánica por Pantalla del 
Sistema BioTrack  ............................................................................................................... 107 
Figura 3.37 Diagramo de Flujo de Navegación de la Aplicación Web ................................. 108 
Figura 3.38 Base de Datos - Modelo Entidad-Relación ...................................................... 110 
 
Figura 4.1 Vista general del sistema en el aula. ................................................................. 114 
Figura 4.2 Sistema de Biotrack siendo usado en el aula. ................................................... 114 
 
 
Figura 4.3 Placa PCB con los componentes. ...................................................................... 115 
Figura 4.4 Caja de componentes. ....................................................................................... 115 
Figura 4.5 Soporte de cámara. ........................................................................................... 116 
Figura 4.6 Estructura de soporte de cámara. ...................................................................... 116 
Figura 4.7 Regla para medición perpendicular al segmento. .............................................. 117 
Figura 4.8 Pantalla de Inicio de sesión del sistema BioTrack. ............................................ 118 
Figura 4.9 Panel “Centro de ayuda” de la interfaz BioTrack. ............................................... 118 
Figura 4.10 Pestaña de inicio tras autenticación en BioTrack. ............................................ 119 
Figura 4.11 Acceso Rápido a ejercicios de análisis biomecánico. ...................................... 119 
Figura 4.12 Modal “Guía Rápida de Uso” con pasos operativos para el análisis. ............... 120 
Figura 4.13 Pestaña de Segmentos/Ejercicios de BioTrack. ............................................... 120 
Figura 4.14 Vista de segmento seleccionado (Codo). ......................................................... 121 
Figura 4.15 Selector de modo de control del ESP32 (local y remoto). ................................ 121 
Figura 4.16 Control local del ESP32 vía Web Serial API y registro de eventos. .................. 122 
Figura 4.17 Panel de control remoto del actuador de cámara (flujo con PC-puente). ......... 122 
Figura 4.18 Ejercicios según el segmento seleccionado con parámetros e instrucciones. .. 123 
Figura 4.19 Pantalla previa al análisis: posición inicial, instrucciones y arranque del registro.
 ............................................................................................................................................ 124 
Figura 4.20 Configuración de cámara. ................................................................................ 124 
Figura 4.21 Vista de análisis en tiempo real . ..................................................................... 125 
Figura 4.22 Pestaña “Perfil” con metadatos del usuario e indicadores de actividad. ........... 126 
Figura 4.23 Pestaña de “Reportes”. .................................................................................... 126 
Figura 4.24 Análisis FODA de la encuesta a la docente de la materia encargada de 
biomecánica. ....................................................................................................................... 139 
Figura 4.25 Explicación del sistema. .................................................................................. 146 
Figura 4.26 Explicación de la toma de mediciones. ............................................................ 146 
Figura 4.27 Mediciones con goniómetro ............................................................................. 146 
Figura 4.28 Análisis en tiempo real (I) ................................................................................ 147 
Figura 4.29 Análisis en tiempo real (II) ............................................................................... 147 
 
  
 
 
ÍNDICE DE TABLAS 
Tabla 3.1 Comparativa de servomotores  ............................................................................. 57 
Tabla 3.2 Comparativa de placas de desarrollo.  .................................................................. 70 
Tabla 3.3 Comparativa de Reguladores de Voltaje para Sistema de Alimentación. .............. 71 
Tabla 3.4 Comparativa técnica entre sensores inerciales. .................................................... 72 
Tabla 3.5 Comparativa cámara de procesamiento.  .............................................................. 76 
Tabla 3.6 Comparativa de Baterías para Sistema de Alimentación Portátil. .......................... 78 
Tabla 3.7 Comparativa de Lenguajes de Programación para Firmware. ............................... 79 
Tabla 3.8 Resultados de Ajuste: Pitch (Inclinación Frontal) ................................................... 82 
Tabla 3.9 Comparativa de Frameworks Backend.  ................................................................ 89 
Tabla 3.10 Comparativa de Bibliotecas de Visión Artificial.  .................................................. 90 
Tabla 3.11 Comparativa de Frameworks Frontend.  ............................................................. 91 
Tabla 3.12 Costos directos ................................................................................................. 111 
Tabla 3.13 Costos indirectos ............................................................................................... 112 
  
 
 
 
 
 
 
 
 
  
 
 
ÍNDICE DE GRÁFICOS 
Gráfico 2.1 Método actual utilizado por los estudiantes para el análisis de movimientos 
articulares en las prácticas de biomecánica. ......................................................................... 43 
Gráfico 2.2 Nivel de confianza en la precisión de las mediciones realizadas con métodos 
actuales (escala de 1 a 5) ..................................................................................................... 43 
Gráfico 2.3 Importancia otorgada a la consistencia y replicabilidad de las mediciones en las 
prácticas ................................................................................................................................ 44 
Gráfico 2.4 Dificultad percibida para controlar la posición de cámara durante la captura de 
movimiento. ........................................................................................................................... 44 
Gráfico 2.5 Influencia percibida de la posición de cámara en la calidad de los datos obtenidos.
 .............................................................................................................................................. 45 
Gráfico 2.6 Percepción sobre la limitación de recursos interactivos en la comprensión de 
conceptos biomecánicos. ...................................................................................................... 45 
Gráfico 2.7 Efecto percibido de la falta de un laboratorio específico en el aprendizaje práctico.
 .............................................................................................................................................. 46 
Gráfico 2.8 Nivel de motivación frente a prácticas basadas en análisis manual. .................. 46 
Gráfico 2.9 Interés de los estudiantes en incorporar herramientas tecnológicas de análisis del 
ROM en tiempo real. ............................................................................................................. 47 
 
Gráfico 4.1 Diagrama de dispersión de Comparación Sistema BioTrack vs Goniómetro - 
Hombro ............................................................................................................................... 128 
Gráfico 4.2 Diagrama de dispersión de Comparación Sistema BioTrack vs Goniómetro - 
Hombro ............................................................................................................................... 128 
Gráfico 4.3 Diagrama de dispersión de Comparación Sistema BioTrack vs Goniómetro - 
Hombro ............................................................................................................................... 129 
Gráfico 4.4 Diagrama de dispersión de Comparación Sistema BioTrack vs Goniómetro - 
Hombro ............................................................................................................................... 130 
Gráfico 4.5 Diagrama de dispersión de Comparación Sistema BioTrack vs Goniómetro - 
Hombro ............................................................................................................................... 130 
Gráfico 4.6 Gráfica Bland-Altman del Sistema BioTrack. .................................................... 132 
Gráfico 4.7 Grafico de Barras de error promedio por articulación. ...................................... 133 
Gráfico 4.8 Histograma de Distribución de errores. ............................................................ 135 
Gráfico 4.9 Comparando tu experiencia, ¿qué te pareció más fácil de usar? ..................... 140 
 
 
Gráfico 4.10 La capacidad de ver tu movimiento y el ángulo en la pantalla al mismo tiempo, 
¿te ayudó a entender la relación entre la estructura de tu cuerpo y su función? ................. 141 
Gráfico 4.11 ¿El sistema te ayudó a comprender mejor los movimientos dentro del rango 
normal de cada articulación y/o describir movimientos articulares de miembros superiores e 
inferiores? ........................................................................................................................... 141 
Gráfico 4.12 Después de usar Biotrack, ¿tu nivel de confianza en la precisión de las 
mediciones...? ..................................................................................................................... 142 
Gráfico 4.13 ¿El uso del sistema hizo que las prácticas fueran más interesantes y 
motivadoras? ....................................................................................................................... 142 
Gráfico 4.14 Si pudieras elegir, ¿preferirías seguir usando Biotrack en tus futuras prácticas de 
biomecánica? ...................................................................................................................... 143 
Gráfico 4.15 Las instrucciones para realizar los ejercicios, ¿fueron claras? ....................... 143 
Gráfico 4.16 Ver tus ángulos de movimiento en la pantalla en tiempo real, ¿te ayudó a 
entender mejor el ejercicio? ................................................................................................ 144 
Gráfico 4.17 Compara esta experiencia con usar un goniómetro (la "regla" para medir 
ángulos). ¿Qué te pareció más fácil de entender? .............................................................. 145 
 
LISTA DE SIGLAS Y ABREVIATURAS 
AAOS: American Academy of Orthopaedic Surgeons. 
DoF: Degrees of Freedom (Ingl.); número de movimientos independientes de una articulación. 
ESP32: Microcontrolador de la familia ESP32. 
FPS: Frames Per Second; tasa de cuadros por segundo. 
GdL: Grados de Libertad. 
GN: Goniómetro; instrumento clínico de referencia para ángulos. 
GUI: Graphical User Interface; interfaz gráfica de usuario. 
HPE: Human Pose Estimation; estimación de pose humana por visión. 
ICC: Intraclass Correlation Coefficient; coeficiente de correlación intraclase. 
IMU: Inertial Measurement Unit; unidad inercial (acelerómetro/giroscopio). 
MCU: Microcontroller Unit; unidad microcontrolador. 
MPP: MediaPipe Pose; biblioteca para detección de 33 puntos anatómicos. 
RGB: Red-Green-Blue; formato de imagen en cámara. 
RMSE: Root Mean Square Error; raíz del error cuadrático medio. 
ROM: Range of Motion; rango de movimiento articular. 
SQLite: Motor de base de datos relacional embebido.