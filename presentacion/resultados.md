RESULTADOS Y DISCUSIÓN 
4.1 INTRODUCCIÓN DEL CAPÍTULO  
Este capítulo documenta la verificación funcional del sistema educativo de análisis de ROM con 
cámara RGB y estimación de pose 2D. Se muestra evidencia fotográfica del montaje en aula, la 
operación de la interfaz en tiempo real, el protocolo de captura que estandariza encuadre y plano 
mediante una escala física (sticker) de alturas en el soporte de cámara, y los resultados 
cuantitativos de estabilidad intra-sesión y concordancia (cuando existan mediciones de referencia 
manual). Finalmente, se discuten los hallazgos frente a los objetivos y alcances del sistema (uso 
educativo, análisis monoplano, una persona en escena).  
Figura 4.1 Vista general del sistema en el aula. 
Fuente: Elaboración propia, 2025. 
Figura 4.2 Sistema de Biotrack siendo usado en el aula. 
Fuente: Elaboración propia, 2025. 
4.2 PRESENTACIÓN DE LOS RESULTADOS 
115 
4.2.1 SISTEMA ELECTRÓNICO (HARDWARE)    
Se documenta cómo la placa se integró y funcionó durante las sesiones, no su diseño interno. La 
placa (control local/remoto del sistema y enlace con la GUI) se alojó en un case rígido, con 
conectores rotulados y ruta de cables ordenada para evitar tirones y ruido eléctrico sobre el bus 
USB de la cámara. Durante las tomas, la placa permitió: establecer/monitorear el enlace Bluetooth 
y accionar periféricos auxiliares pan y nivelación. La evidencia en esta sección se centra en 
estabilidad y usabilidad. 
Figura 4.3 Placa PCB con los componentes. 
Fuente: Elaboración propia, 2025. 
Figura 4.4 Caja de componentes. 
Fuente: Elaboración propia, 2025. 
4.2.2 SISTEMA MECÁNICO   
116 
El sistema de captura se compone de una cámara RGB conectada por USB a un computador y 
montada sobre un trípode con escala física (sticker) para altura en eje Z. En resultados, su función 
se evidencia por la estandarización del encuadre: la altura Z se selecciona por segmento (hombro, 
codo, cadera, rodilla) y la distancia entre sujeto – cámara se fija con marcas en el piso, 
manteniendo el plano de medición (sagital o frontal) constante. La cámara opera a resolución y 
fps predefinidos (p. ej., 1280×720 a 30 fps), y la GUI muestra en tiempo real landmarks 2D, lectura 
angular, fps efectivo y estado de conexión. Con ello, el hardware aporta estabilidad geométrica 
(altura/distancia/pan) que reduce la variabilidad por perspectiva en métodos 2D, facilitando la 
repetibilidad de las mediciones de ROM. Los criterios de aceptación mecánica en sesión fueron: 
(i) encuadre completo del segmento, (ii) fps efectivo ≥ 25, (iii) ausencia de vibración del conjunto 
cámara–trípode, y (iv) ausencia de oclusiones generadas por el propio montaje. 
Figura 4.5 Soporte de cámara. 
Fuente: Elaboración propia, 2025. 
Figura 4.6 Estructura de soporte de cámara. 
117 
Fuente: Elaboración propia, 2025. 
Figura 4.7 Regla para medición perpendicular al segmento. 
Fuente: Elaboración propia, 2025. 
4.2.3 INTERFAZ DEL USUARIO 
A continuación, se presenta la pantalla de acceso del sistema, que constituye el punto de entrada 
a la plataforma de análisis biomecánico (Figura 4.8Error! Reference source not found.). El 
diseño muestra en la parte superior el ícono de “BioTrack”, seguido por una breve descripción de 
la finalidad del sistema. El formulario central incluye dos campos: “Usuario” y “Contraseña”. En la 
base del formulario se ubica el botón primario “Iniciar sesión” y un enlace auxiliar “¿Necesitas 
ayuda?” (Figura 4.9) destinado a soporte que agrupa el contenido en tres apartados: “¿Qué es 
BioTrack?”, “¿Necesitas Acceso?” y “Requisitos” condiciones mínimas para el correcto 
funcionamiento. 
Figura 4.8 Pantalla de Inicio de sesión del sistema BioTrack. 
118 
Fuente: Elaboración propia, 2025. 
Figura 4.9 Panel “Centro de ayuda” de la interfaz BioTrack. 
Fuente: Elaboración propia, 2025. 
Al completar la autenticación, el sistema redirige a la pestaña INICIO (Figura 4.10), donde se 
presenta una barra de navegación superior con las pestañas: Inicio, Segmentos/Ejercicios, Perfil, 
Reportes y el estado de sesión del usuario. Inicialmente, se ofrece dos acciones principales: “Ir a 
Articulaciones” y “Guía de Uso”. En la zona inferior se dispone un conjunto de tarjetas con 
indicadores clave del entorno (p. ej., número de segmentos disponibles, cantidad acumulada de 
análisis, modo de operación en tiempo real y tipo de detección 2D), lo que facilita una verificación 
rápida. 
En la misma vista, el bloque “Acceso Rápido” (Figura 4.11) prioriza la ejecución inmediata de 
ejercicios frecuentes mediante un atajo para articulaciones específicas (Hombro, Rodilla y Codo), 
119 
cada una con el botón “Analizar” que inicia el módulo de captura y cálculo de ángulos. Bajo este 
bloque se posee una acción “Ver Todos los Ejercicios” que conduce al catálogo completo de 
segmentos. 
Figura 4.10 Pestaña de inicio tras autenticación en BioTrack. 
Fuente: Elaboración propia, 2025. 
Figura 4.11 Acceso Rápido a ejercicios de análisis biomecánico. 
Fuente: Elaboración propia, 2025. 
En caso de que el usuario presione el botón “Guía de uso” (Figura 4.10), el sistema despliega 
una ventana modal titulada “Guía Rápida de Uso” (Figura 4.12), el contenido de ésta se organiza 
en una secuencia numerada de tres pasos con iconografía de apoyo:  
• Selección del segmento o articulación a analizar (Hombro, Codo, Cadera, Rodilla, Tobillo) 
• Preparación del encuadre de cámara con recomendaciones explícitas 
• Ejecución del movimiento con retroalimentación en tiempo real.  
Figura 4.12 Modal “Guía Rápida de Uso” con pasos operativos para el análisis. 
120 
Fuente: Elaboración propia, 2025. 
Si el usuario presiona "Ir a Articulaciones" o "Ver todos los Ejercicios" la vista que se muestra en 
pantalla es la de la Figura 4.13, donde se organiza las cinco opciones de los segmentos 
disponibles. En la franja superior se presentan información general dividido en tres bloques: 
preparación, lineamientos durante el análisis y recomendaciones generales. Cada segmento (p. 
ej., Hombro, Codo, Cadera) indica los movimientos disponibles (flexión/extensión y, según 
corresponda, abducción/aducción) e incorpora el botón “Ir a Ejercicios”, que navega directamente 
al módulo de captura de la articulación seleccionada. 
Figura 4.13 Pestaña de Segmentos/Ejercicios de BioTrack. 
Fuente: Elaboración propia, 2025. 
Al presionar “Ir a Ejercicios”, la pantalla presenta un encabezado con el nombre del segmento 
seleccionado, la descripción de los rangos evaluables (flexión, extensión y extensión sobre la 
cabeza) y un indicador de avance de ejercicios, que permite monitorear el cumplimiento del 
protocolo (Figura 4.14). En el bloque izquierdo se despliega el módulo “Altura de Cámara”, que 
121 
calcula y muestra la altura recomendada en función de la estatura registrada, con nota de 
referencia para asegurar la perpendicularidad del sensor respecto al segmento. En paralelo, el 
bloque “Control ESP32” habilita el ajuste de la altura de cámara mediante el actuador del soporte 
motorizado. 
Figura 4.14 Vista de segmento seleccionado (Codo). 
Fuente: Elaboración propia, 2025. 
Para la configuración del control del soporte se despliega una ventana emergente. Se ofrece al 
usuario dos opciones: “Desde esta PC”, que establece una conexión directa con el ESP32 
mediante Bluetooth y “Control Remoto», que permite gestionar el actuador desde cualquier 
dispositivo en la red (celular/tablet) a través del botón “Abrir Control Remoto” (Figura 4.15). 
Figura 4.15 Selector de modo de control del ESP32 (local y remoto). 
Fuente: Elaboración propia, 2025 
La vista “Desde esta PC” implementa el enlace directo con el microcontrolador mediante Web 
Serial API y puerto COM (Figura 4.16), integrando el procedimiento previo, el estado de conexión 
y el control básico del actuador. En la parte superior se listan los pasos de preparación, al centro 
122 
el indicador de estado (Desconectado/Conectado) y los botones de acción (Conectar ESP32, 
Desconectar). También se visualiza controles de paneo (izquierda–centro–derecha) y un área de 
“Estado” que registra eventos de la sesión, lo que permite verificar en tiempo real la apertura del 
puerto, el envío de órdenes y el diagnóstico de fallos de enlace. 
Figura 4.16 Control local del ESP32 vía Web Serial API y registro de eventos. 
Fuente: Elaboración propia, 2025. 
La vista “Control Remoto” presenta controles direccionales del soporte de cámara. La interfaz 
concentra los elementos esenciales botones grandes, disposición central, tarjeta con requisito de 
operación. 
Figura 4.17 Panel de control remoto del actuador de cámara (flujo con PC-puente). 
Fuente: Elaboración propia, 2025. 
123 
Al final de la pestaña se tiene un apartado denominado “Selecciona un ejercicio para análisis” 
que organiza los ejercicios disponibles de la articulación seleccionada, como plano de movimiento 
(sagital/frontal), duración estimada, rango angular objetivo y un bloque de instrucciones breves. 
Cada tarjeta integra un video ilustrativo para estandarizar la técnica, un indicador de dificultad y 
un porcentaje de avance. Además, se añaden tips de seguridad posturales en la parte inferior, 
orientadas a minimizar errores de ejecución y artefactos de seguimiento.  
Figura 4.18 Ejercicios según el segmento seleccionado con parámetros e instrucciones. 
Fuente: Elaboración propia, 2025. 
Al seleccionar “Ir a análisis” el sistema despliega la vista del ejercicio elegido. En la parte superior 
se muestra la posición inicial estandarizada, las instrucciones de ejecución separadas por 
“Movimiento” y una franja de advertencia postural que actúa como recordatorio. El botón “Iniciar 
Análisis” habilita el bucle de captura y cálculo de ángulos. También se ofrece dos áreas 
complementarias: “Historial de Análisis”, donde se listarán ejecuciones previas del mismo 
ejercicio y “Estadísticas” destinada al resumen cuantitativo posterior. 
124 
Figura 4.19 Pantalla previa al análisis: posición inicial, instrucciones y arranque del registro.  
Fuente: Elaboración propia, 2025. 
La interfaz dispone tanto en la esquina inferior derecha e izquierda controles utilitarios (Figura 
4.19). El botón izquierdo redirige a “Configuración de Cámara” abre una ventana emergente con 
estado actual y selección de dispositivo, tres preajustes, además de un modo para personalizar 
la resolución, tasa de cuadros y porcentaje de compresión (Figura 4.20). El botón derecho de 
audio actúa como interruptor para habilitar o silenciar la retroalimentación sonora del sistema 
durante el ejercicio. 
Figura 4.20 Configuración de cámara. 
Fuente: Elaboración propia, 2025. 
Al activar “Iniciar análisis” la interfaz cambia al modo de captura en tiempo real y en pantalla 
completa. Se dibujan los segmentos anatómicos de interés y se muestra junto a la articulación 
125 
analizada, el ángulo instantáneo calculado fotograma a fotograma. En el panel superior derecho 
se presenta el seguimiento ROM Tracking con el valor actual y el máximo alcanzado durante la 
ejecución, además del estado de actividad y un contador/temporizador para controlar la prueba. 
Esta visualización permite verificar técnica y rango mientras el sistema computa los ángulos y 
registra el pico articular para su posterior contraste con valores de referencia y reporte. 
Figura 4.21 Vista de análisis en tiempo real . 
Fuente: Elaboración propia, 2025. 
La pestaña de “Perfil” permite visualizar el desempeño individual con cuatro bloques funcionales 
(Figura 4.22). 
• A la izquierda: “Análisis por Articulación” resume el volumen y el grado de avance por 
segmento y presenta un progreso general en formato de barra, útil para verificar cobertura 
del protocolo y priorizar pendientes.  
• Abajo: “Actividad Reciente” lista cronológicamente las sesiones ejecutadas con metadatos 
clave facilitando trazabilidad del entrenamiento.  
• A la derecha: “Logros Desbloqueados” muestra insignias por completar ejercicios. 
• A la derecha: “Próximo Objetivo” explicita la meta activa con barra de progreso, contiene 
un botón “Continuar Progreso” que incentiva la adherencia. 
Figura 4.22 Pestaña “Perfil” con metadatos del usuario e indicadores de actividad.  
126 
Fuente: Elaboración propia, 2025. 
En la pestaña de “Reportes” se visualiza el historial completo de ejecuciones por segmento y 
ejercicio en una vista tabular. En el encabezado se indica el segmento seleccionado con el 
número de ejercicios disponibles. También, se visualiza el ejercicio activo junto con el conteo de 
sesiones registradas. La tabla organiza cada sesión por columnas operativas:  
• Fecha 
• ROM Máximo 
• Lado (izquierdo/derecho) 
• Clasificación (estado cualitativo del rango) 
• Duración (tiempo empleado en la captura) 
• Calidad (etiqueta de consistencia de la señal/procedimiento).  
Figura 4.23 Pestaña de “Reportes”.  
Fuente: Elaboración propia, 2025. 
4.3 PRUEBAS REALIZADAS AL SISTEMA 
127 
Se analizaron mediciones angulares de distintas articulaciones y movimientos obtenidas con el 
sistema BioTrack frente a un goniómetro manual (referencia clínica). El conjunto final incluye 135 
registros. Cada registro contiene: Articulación, Movimiento, Lado, medida real con goniómetro, 
medida del sistema y diferencias. El conjunto final con los datos que se obtuvo se puede ver en 
el Apéndice A3. 
4.3.1 PRUEBAS TÉCNICAS DE FUNCIONAMIENTO   
4.3.1.1 ANÁLISIS DE CORRRELACIÓN POR ARTICULACIÓN 
El análisis de correlación entre el sistema BioTrack y el goniómetro manual reveló resultados 
altamente satisfactorios para todas las articulaciones evaluadas. Se calcularon los coeficientes 
de determinación (R²) y los coeficientes de correlación de Pearson (R) para cada articulación, 
junto con sus correspondientes valores p, los cuales confirmaron la significancia estadística de 
las relaciones observadas. 
Los gráficos de dispersión individuales para cada articulación (Gráficos 4.1 a 4.6) mostraron una 
distribución de puntos cercana a la línea de igualdad perfecta (línea de 45° que representa 
concordancia absoluta entre métodos), indicando que las mediciones del sistema automatizado 
se aproximan consistentemente a los valores de referencia del goniómetro. Las líneas de 
regresión lineal ajustadas presentaron pendientes cercanas a 1 y ordenadas en el origen 
próximas a 0, características que confirman la ausencia de sesgos sistemáticos significativos en 
las mediciones del sistema. 
Articulación del Hombro (Gráfico 4.1): Presentó coeficientes de correlación robustos (R² > 
0.90), aunque con mayor dispersión en comparación con otras articulaciones. Esto puede 
atribuirse a la complejidad anatómica del hombro y su amplio rango de movimiento tridimensional, 
lo cual representa un desafío mayor para la detección precisa en análisis bidimensional. 
128 
Gráfico 4.1 Diagrama de dispersión de Comparación Sistema BioTrack vs Goniómetro - 
Hombro 
Fuente: Elaboración propia, 2025. 
Articulación del Codo (Gráfico 4.2): Exhibió resultados consistentes con R² en el rango de 0.92
0.96, confirmando la alta precisión del sistema para evaluar movimientos de flexo-extensión. La 
correlación observada es comparable con estudios previos que validan sistemas de análisis de 
movimiento basados en visión por computadora. 
Gráfico 4.2 Diagrama de dispersión de Comparación Sistema BioTrack vs Goniómetro – Codo. 
Fuente: Elaboración propia, 2025. 
129 
Articulación de la Cadera (Gráfico 4.3): Demostró una correlación excelente con valores de R² 
superiores a 0.95, indicando que más del 95% de la variabilidad en las mediciones del sistema 
BioTrack puede explicarse linealmente por las mediciones del goniómetro. Esta articulación 
presentó una de las mejores concordancias del estudio, probablemente debido a la amplitud de 
sus movimientos y la facilidad de detección de los puntos anatómicos de referencia. 
Gráfico 4.3 Diagrama de dispersión de Comparación Sistema BioTrack vs Goniómetro – 
Cadera. 
Fuente: Elaboración propia, 2025. 
Articulación de la Rodilla (Gráfico 4.4): Alcanzó valores de R² superiores a 0.93, confirmando 
la efectividad del sistema para evaluar movimientos de flexión y extensión en esta articulación de 
carga.  
130 
Gráfico 4.4 Diagrama de dispersión de Comparación Sistema BioTrack vs Goniómetro – 
Rodilla. 
Fuente: Elaboración propia, 2025. 
Articulación del Tobillo (Gráfico 4.5): Demostró una correlación sólida (R² > 0.91) para los 
movimientos de dorsiflexión y flexión plantar. Aunque presentó una dispersión ligeramente mayor 
en comparación con otras articulaciones, los resultados se mantienen dentro de rangos 
aceptable/consistente con validaciones de métodos RGB/RGB-D para evaluación biomecánica 
de bajo costo. 
Gráfico 4.5 Diagrama de dispersión de Comparación Sistema BioTrack vs Goniómetro – 
Tobillo. 
Fuente: Elaboración propia, 2025. 
131 
En síntesis, los diagramas de dispersión por articulación mostraron alta relación lineal entre 
ambos métodos, con pendientes cercanas a 1 y ordenadas próximas a 0. Se reportan R 
(Pearson), R² y p por articulación. 
• Hombro: R² > 0,90, con mayor dispersión relativa por la complejidad tridimensional del 
movimiento y la proyección 2D. 
• Codo: R² en 0,92–0,96 para flexo-extensión, patrón compacto. 
• Cadera: R² > 0,95, una de las mejores concordancias. 
• Rodilla: R² > 0,93 en flexo-extensión. 
• Tobillo: R² > 0,91, con dispersión mayor en dorsiflexión respecto de flexión plantar. 
4.3.1.2 ANÁLISIS DE CONCORDANCIA MEDIANTE BLAND-ALTMAN 
El análisis de Bland-Altman constituye el método de referencia para evaluar la concordancia entre 
dos técnicas de medición clínica. Este análisis permite identificar sesgos sistemáticos y evaluar 
los límites de acuerdo entre métodos. 
El gráfico de Bland-Altman (Gráfico 4.6) construido con todas las mediciones del estudio mostró 
una distribución simétrica de las diferencias alrededor de la media, indicando ausencia de sesgos 
sistemáticos pronunciados. La línea de sesgo (diferencia media) se ubicó cercana a cero, 
confirmando que, en promedio, el sistema BioTrack no tiende a sobreestimar ni subestimar los 
ángulos articulares de manera consistente. 
Gráfico 4.6 Gráfica Bland-Altman del Sistema BioTrack. 
132 
Fuente: Elaboración propia, 2025. 
Los límites de acuerdo del 95% (media ± 1.96 desviaciones estándar) delimitaron el rango dentro 
del cual se espera que caigan el 95% de las diferencias entre métodos. Estos límites resultaron 
ser aceptable/consistente con validaciones de métodos RGB/RGB-D para evaluación 
biomecánica de bajo costo, encontrándose dentro del rango de ±5°, valor tradicionalmente 
considerado como el error máximo aceptable en goniometría clínica según la literatura 
especializada. 
Un análisis detallado de la distribución de puntos en el gráfico de Bland-Altman no reveló patrones 
de heterocedasticidad significativos, es decir, la magnitud del error no mostró una tendencia 
sistemática a aumentar o disminuir en función del valor promedio de las mediciones. Esta 
característica es fundamental, ya que indica que la precisión del sistema BioTrack se mantiene 
consistente a lo largo de todo el rango de movimiento articular evaluado. 
La concentración de la mayoría de los puntos dentro de una banda estrecha alrededor de la línea 
de sesgo (Gráfico 4.6) sugiere una alta repetibilidad de las mediciones y una baja variabilidad 
inter-método. Solo un pequeño porcentaje de mediciones (menos del 5%, como es esperado 
estadísticamente) cayó fuera de los límites de acuerdo del 95%, confirmando la validez del 
modelo de distribución normal de los errores. 
4.3.1.3 ANÁLISIS DE ERROR ABSOLUTO POR ARTICULACIÓN 
El análisis comparativo del error absoluto promedio entre articulaciones (Gráfico 4.7) proporcionó 
información sobre el desempeño diferencial del sistema según la región anatómica evaluada. 
133 
Este análisis permitió identificar las articulaciones donde el sistema presenta mayor precisión, así 
como aquellas que podrían beneficiarse de optimizaciones futuras del algoritmo. 
Los resultados revelaron que el codo presentó los menores errores absolutos promedio, con 
valores inferiores a 3° (representados en verde en el Gráfico 4.7). Este excelente desempeño 
puede atribuirse a varios factores: la menor complejidad de los movimientos evaluados 
(predominantemente uniaxiales), la facilidad de posicionamiento perpendicular al plano de la 
cámara, y la mejor definición de los puntos anatómicos de referencia en estas regiones. 
Las articulaciones de mediano rango (rodilla y tobillo) mostraron errores absolutos en el rango de 
3-4° (representados en naranja en el Gráfico 4.7), valores que se mantienen dentro de los límites 
aceptables.  
Las articulaciones proximales y de mayor complejidad anatómica (hombro y cadera) exhibieron 
errores absolutos ligeramente superiores, en el rango de 4-5°, aunque aún dentro de los límites 
de aceptabilidad clínica. La mayor magnitud del error en estas articulaciones puede explicarse 
por factores como la mayor variabilidad en la colocación de puntos anatómicos de referencia, la 
influencia de tejidos blandos circundantes en la detección de landmarks, y la complejidad 
inherente de los movimientos tridimensionales que se proyectan en un plano bidimensional 
durante la captura por cámara. 
Gráfico 4.7 Grafico de Barras de error promedio por articulación. 
Fuente: Elaboración propia, 2025.  
134 
Es importante destacar que todas las articulaciones evaluadas presentaron errores promedio 
inferiores al umbral crítico de 5° (línea roja discontinua en el Gráfico 4.7), criterio establecido en 
la literatura como el error máximo aceptable para considerar un método de medición angular 
como clínicamente útil. Este resultado confirma que el sistema BioTrack alcanza estándares de 
precisión apropiados para su implementación en entornos clínicos reales. 
La codificación por colores utilizada en el gráfico de barras (verde para errores < 3°, naranja para 
3-5°, y rojo para > 5°) permite visualizar rápidamente el nivel de desempeño del sistema para 
cada articulación. La predominancia de colores verde y naranja en los resultados obtenidos 
refuerza la conclusión de que el sistema ha alcanzado niveles de precisión satisfactorios para 
aplicaciones biomecánicas. 
4.3.1.4 CARACTERIZACIÓN DE LA DISTRIBUCIÓN DE ERRORES DEL SISTEMA 
El análisis de la distribución de los errores de medición (diferencias entre sistema BioTrack y 
goniómetro) proporcionó información fundamental sobre las características estadísticas del error 
del sistema y su comportamiento probabilístico (Gráfico 4.8). 
El histograma de frecuencias de las diferencias mostró una distribución aproximadamente normal 
(gaussiana), con una concentración de la mayoría de las observaciones alrededor de la media y 
una disminución progresiva de la frecuencia hacia los valores extremos. Esta característica de 
normalidad fue confirmada visualmente mediante la superposición de la curva de distribución 
normal teórica (línea roja en el Gráfico 4.8) sobre el histograma empírico, observándose un ajuste 
satisfactorio entre ambas. 
La distribución normal de los errores es una característica deseable en sistemas de medición, ya 
que implica que los errores son predominantemente aleatorios en lugar de sistemáticos. Los 
errores aleatorios siguen un comportamiento probabilístico predecible y pueden minimizarse 
mediante técnicas de promediado o mediante múltiples mediciones repetidas, mientras que los 
errores sistemáticos requieren corrección mediante calibración o ajustes algorítmicos. 
Gráfico 4.8 Histograma de Distribución de errores. 
135 
Fuente: Elaboración propia, 2025. 
La media de las diferencias (μ) resultó ser muy cercana a cero (línea azul continua en la Gráfico 
4.8), confirmando la ausencia de sesgo sistemático significativo en las mediciones del sistema. 
Este resultado es consistente con los hallazgos del análisis de Bland-Altman y refuerza la 
conclusión de que el sistema BioTrack proporciona mediciones no sesgadas en comparación con 
el método de referencia. 
La desviación estándar (σ) de las diferencias, que cuantifica la dispersión típica de los errores 
alrededor de la media y se indica en el cuadro estadístico del Gráfico 4.8, presentó valores 
moderados que indican una precisión consistente del sistema. La relación entre la desviación 
estándar y los límites de aceptabilidad clínica confirma que la variabilidad inherente del sistema 
se encuentra dentro de rangos manejables y clínicamente apropiados. 
La línea vertical discontinua roja que marca el error cero (condición ideal de concordancia 
perfecta) en el histograma sirvió como referencia visual para evaluar la simetría de la distribución. 
La observación de una distribución simétrica alrededor de esta línea confirma que el sistema no 
presenta tendencias sistemáticas consistentes hacia la sobreestimación o subestimación de los 
ángulos articulares. 
Un aspecto importante del análisis es la ausencia de valores atípicos extremos (outliers) 
significativos en los extremos de la distribución, como puede apreciarse en el Gráfico 4.8. La 
presencia de muy pocas mediciones con errores superiores a ±10° sugiere que el sistema 
136 
mantiene un desempeño robusto incluso en condiciones potencialmente desafiantes, y que las 
mediciones con errores sustanciales son excepcionales en lugar de frecuentes. 
La forma unimodal de la distribución (con un solo pico central visible en el histograma) indica que 
no existen subpoblaciones de mediciones con comportamientos de error significativamente 
diferentes, lo cual sugiere que el sistema mantiene un desempeño consistente 
independientemente de factores como la articulación específica evaluada, el lado corporal, o el 
rango angular particular dentro del movimiento. 
4.3.1.5 DISCUSIÓN E INTERPRETACIÓN 
Los resultados mostraron una relación lineal alta entre las mediciones del sistema y el goniómetro 
(pendientes próximas a 1), pero la concordancia debe interpretarse con el análisis de Bland
Altman: el sesgo medio fue pequeño y los Límites de Acuerdo (LoA) ubicaron la mayor parte de 
las diferencias dentro de un rango acotado, coherente con lo reportado por validaciones de 
estimación angular basadas en seguimiento de pose con cámaras RGB/RGB-D cuando se 
controla la geometría de cámara y el plano de movimiento. En este marco, la tendencia global es 
adecuada para uso formativo y práctica supervisada en aula, sin extrapolar a decisiones clínicas 
finas. 
Por articulación, el error absoluto medio fue menor en codo y rodilla y mayor en tobillo. Este patrón 
es consistente con limitaciones de métodos 2D ante oclusiones de maléolos, escasa textura y 
mayor ambigüedad de profundidad en el pie, que degradan la estabilidad del cálculo angular en 
dorsiflexión/flexión plantar. En cambio, segmentos con ejes bien expuestos y mayor control del 
plano (codo/rodilla) concentran menor varianza. Estas observaciones orientan mejoras 
específicas en orientación y alineación del pie, apertura de cámara y verificación de plano antes 
de la captura. 
Las fuentes técnicas del sesgo y la dispersión observadas se explican por: (i) desalineación leve 
del plano de movimiento respecto del eje óptico, (ii) cambios de escala aparente por perspectiva 
(distancia efectiva cámara-sujeto), y (iii) fotogramas con landmarks de baja confianza u 
oclusiones por vestimenta/iluminación. Como mitigación inmediata se recomienda: (a) SOP 
explícitos de captura (distancia, altura y ángulo de cámara por ejercicio; marcas de suelo y control 
de plano), (b) filtro de calidad de pose (umbrales de confianza/oclusiones y descarte automático), 
137 
y (c) breve calibración por articulación para compensar offsets residuales. Estas acciones ya 
están sugeridas en el documento y son consistentes con la literatura de estimación de pose. 
En cuanto a la estrategia algorítmica, la incorporación de restricciones de rango fisiológico y de 
un modelo humanoide durante el cómputo angular es una vía concreta para reducir la 
ambigüedad en 2D, especialmente en segmentos distales. Se ha demostrado que penalizar 
rotaciones fuera de rango y/o inconsistencias centro-de-masa vs. soporte ayuda a resolver la 
ambigüedad de profundidad y estabiliza los ángulos estimados, con tiempos de ejecución 
compatibles con operación en tiempo real en hardware de bajo costo. Por ello, se prioriza explorar 
una etapa 2.5D ligera (regularización por ROM) en la siguiente iteración. 
Finalmente, desde la perspectiva del objetivo del proyecto (uso educativo y estandarización de la 
práctica de ROM), la combinación de sesgo pequeño, LoA acotados y errores medios reducidos 
en grandes articulaciones permite retroalimentación inmediata, comparación objetiva con rangos 
de referencia en aula y registro trazable para revisión diferida. Las limitaciones principales se 
vinculan al diseño monoplano 2D, al tamaño/distribución muestral y a la ausencia de métricas de 
fiabilidad intra/inter-observador (ICC), que se propone abordar con un subestudio de repetibilidad 
(10–15 repeticiones por articulación), SOP de captura y control de calidad de pose antes del 
cómputo final 
4.3.2 EXPERIENCIA DE USUARIO   
ENCUESTA AL ESPECIALISTA Y ANÁLISIS FODA  
En el marco del análisis de resultados del presente capítulo, se decidió realizar un análisis FODA 
cualitativo (Ver Figura 4.24). Con el objetivo de interpretar los hallazgos técnicos desde la 
práctica docente en Biomecánica, se aplicó una encuesta semiestructurada a la docente 
responsable de la asignatura. El instrumento completo (cuestionario, guion de entrevista y 
transcripción íntegra de respuestas) se documenta en el Apéndice A5; allí se consigna el 
contexto de aplicación (formulario digital), los ejes preguntados (uso pedagógico, condiciones de 
captura, usabilidad, registro de datos) y la trazabilidad de las respuestas. 
A partir de la codificación temática de la encuesta (ver Apéndice A5), emergieron cuatro 
categorías consistentes: 
138 
1. Retroalimentación y uso pedagógico. Se valora la retroalimentación en tiempo casi real 
y el registro estructurado de mediciones para seguimiento por estudiante/grupo. Se 
solicita una vista comparativa por práctica y exportación directa a CSV. 
2. Estandarización de captura. Se subraya la necesidad de un protocolo claro de cámara 
(distancia, altura, orientación, control del plano), marcas de posicionamiento del sujeto, y 
una referencia simple para ajustar la distancia en eje Z según el segmento evaluado. 
3. Robustez técnica. Se identifican como sensibles la iluminación, el fondo y la oclusión de 
puntos anatómicos (vestimenta/accesorios). Se sugiere una verificación previa de calidad 
de “pose” antes de iniciar el registro. 
4. Usabilidad. Se requiere interfaz con rotulado explícito, modo “asistido” (flujo guiado en 
pasos), y un “modo espejo docente–estudiante” (demostración y réplica) para prácticas 
supervisadas. 
En función de estas categorías, se elaboró un análisis FODA que sintetiza los factores internos 
del sistema y las condiciones externas del entorno de aula (Figura 4.24). El FODA no reemplaza 
los resultados cuantitativos; los integra y prioriza decisiones de ingeniería alcanzables en la 
siguiente iteración. 
Lectura del FODA y acciones derivadas (2–3 meses) 
• Fortalezas (F). Retroalimentación inmediata, registro estructurado y procedimiento 
estandarizado ya descrito. 
Acción: consolidar el motor de datos con exportación CSV y panel de comparación por 
estudiante/grupo. 
• Oportunidades (O). Mejora pedagógica mediante métricas objetivas y gestión de 
prácticas a escala. 
Acción FO: “modo espejo docente–estudiante” y dashboard de práctica (tiempo, ángulo, 
repetición), con filtros por articulación/movimiento. 
• Debilidades (D). Sensibilidad a perspectiva, dependencia de condiciones de captura, y 
necesidad de validación cuantitativa adicional. 
139 
Acción DO: SOP de captura (distancia fija, altura y oblicuidad ≤5°, marcas de suelo), 
regla de distancia Z integrada al soporte de cámara (marcas físicas), verificación 
automática de calidad de pose (umbral de confianza de landmarks) antes de iniciar. 
• Amenazas (A). Heterogeneidad de cámaras, variabilidad de iluminación/espacio y 
cambios de versión en librerías de pose. 
Acción DA: “kit de captura” (fondo neutro portátil, luz auxiliar, patrón de verificación A4), 
política de versiones (congelado de dependencias) y chequeo rápido de luz/fondo previo 
a la medición. 
Figura 4.24 Análisis FODA de la encuesta a la docente de la materia encargada de 
biomecánica. 
Fuente: Elaboración propia, 2025. 
Implicancias técnicas directas de la encuesta (resumen): 
(i) incorporar un paso de chequeo previo a la adquisición (calidad de pose e iluminación), (ii) 
guía física en el soporte de cámara (marcas de altura y regla Z para segmentos), (iii) flujo 
140 
asistido en la GUI con rotulado y ayuda contextual, y (iv) panel de datos con exportación y vistas 
comparativas para evaluación docente. La evidencia que respalda estas decisiones (respuestas 
textuales) se presenta en el Apéndice A4, junto con la matriz de codificación. 
ANÁLISIS EXPERIENCIA DE USUARIO – ESTUDIANTES 
En el primer gráfico (Gráfico 4.9) el 47,9% de los estudiantes percibió que BioTrack fue “mucho 
más fácil” que los métodos anteriores y el 37,5% indicó que fue “un poco más fácil”, mientras que 
el 14,6% lo consideró “igual de complejo”. En conjunto, el 85,4% reportó una mejora en la facilidad 
de uso, lo que sugiere que la interfaz y el flujo guiado del sistema reducen la carga operativa 
frente a los procedimientos tradicionales y favorecen la adopción en prácticas de aula. 
Gráfico 4.9 Comparando tu experiencia, ¿qué te pareció más fácil de usar? 
Fuente: Elaboración propia, 2025. 
En el segundo gráfico (Gráfico 4.10) el 54,2% afirmó que el sistema “ayudó a comprender 
claramente” el contenido, el 43,8% señaló una mejora “solo parcialmente” y el 2% no notó 
diferencias. Esto indica que el 98% percibió algún grado de mejora en la comprensión, con una 
mayoría que alcanzó claridad plena. Los resultados respaldan la utilidad pedagógica del feedback 
en tiempo real y de las métricas visuales para consolidar conceptos de rango articular durante la 
práctica. 
141 
Gráfico 4.10 La capacidad de ver tu movimiento y el ángulo en la pantalla al mismo tiempo, ¿te 
ayudó a entender la relación entre la estructura de tu cuerpo y su función? 
Fuente: Elaboración propia, 2025. 
En el Gráfico 4.11 se valora el grado de ayuda percibida del sistema durante la práctica, el 35,4% 
de los estudiantes indicó que “ayudó mucho” y el 50% que “ayudó un poco”; en contraste, un 
12,5% consideró que “ayudó muy poco” y ~2% que “no ayudó”. En conjunto, el 85,4% reportó 
algún nivel de apoyo, lo que sugiere que las funciones de guía y visualización aportan beneficios 
prácticos para la ejecución de los ejercicios, aunque persisten casos puntuales donde la 
asistencia no fue suficiente. 
Gráfico 4.11 ¿El sistema te ayudó a comprender mejor los movimientos dentro del rango 
normal de cada articulación y/o describir movimientos articulares de miembros superiores e 
inferiores? 
Fuente: Elaboración propia, 2025. 
Posteriormente se explora el cambio percibido tras usar el sistema (Gráfico 4.12), el 33,3% 
declaró que “aumentó mucho” y el 56,3% que “aumentó un poco”, mientras que el 8,3% no notó 
variación y ~2% reportó disminución. El 89,6% con aumento neto indica un efecto positivo 
142 
general, coherente con la retroalimentación en tiempo real y la estandarización del procedimiento; 
no obstante, la fracción sin mejora plantea la necesidad de ajustar la interfaz o el protocolo en 
grupos específicos. 
Gráfico 4.12 Después de usar Biotrack, ¿tu nivel de confianza en la precisión de las 
mediciones...? 
Fuente: Elaboración propia, 2025. 
Continuando con el análisis (Gráfico 4.13), el 50% de los estudiantes consideró que las prácticas 
fueron “mucho más motivadoras” con BioTrack y el 45,8% las percibió “un poco más 
motivadoras”; solo ~2% indicó que fueron “iguales que antes” y ~2% “menos motivadoras”. El 
95,8% con ganancia de motivación sugiere que el feedback en tiempo real y los indicadores 
visuales de desempeño sostienen la participación durante la tarea, aunque conviene revisar los 
casos minoritarios sin mejora para ajustar las instrucciones o la guía en pantalla. 
Gráfico 4.13 ¿El uso del sistema hizo que las prácticas fueran más interesantes y motivadoras? 
Fuente: Elaboración propia, 2025. 
143 
Para el Gráfico 4.14, el 81,3% manifestó que desea seguir usando el sistema, el 12,5% fue 
indiferente y ~6% expresó que no. La alta intención de uso respalda la continuidad del despliegue 
en aula y la integración con evaluaciones formativas; la fracción indiferente/negativa indica la 
necesidad de reforzar tutoriales breves y plantillas de práctica para reducir la curva inicial y 
aumentar la percepción de utilidad en todos los subgrupos. 
Gráfico 4.14 Si pudieras elegir, ¿preferirías seguir usando Biotrack en tus futuras prácticas de 
biomecánica? 
Fuente: Elaboración propia, 2025. 
El 56,3% de los estudiantes reportó que las instrucciones fueron “muy claras” y el 39,6% “algo 
claras”, mientras que una fracción minoritaria las percibió confusas o demasiado rápidas. Este 
patrón indica que la estructura de la guía es adecuada para la mayoría, pero aún requiere 
optimizar el ritmo de presentación y la persistencia de mensajes para asegurar comprensión total 
en los casos rezagados. 
Gráfico 4.15 Las instrucciones para realizar los ejercicios, ¿fueron claras?
Fuente: Elaboración propia, 2025. 
144 
En continuidad con lo anterior, el Gráfico 4.16 muestra la valoración de los indicadores visuales 
y el feedback: el 56,3% señaló que “ayudó mucho” y el 39,6% “ayudó un poco”, con un porcentaje 
reducido que no percibió utilidad. La consistencia entre ambas preguntas sugiere que, cuando 
las instrucciones se comprenden plenamente, los indicadores cumplen su función pedagógica; 
por tanto, la mejora prioritaria es alinear el módulo de ayudas (mensajes, ejemplos breves y 
confirmaciones paso a paso) con el despliegue de las métricas en vivo para maximizar su efecto 
formativo. 
Gráfico 4.16 Ver tus ángulos de movimiento en la pantalla en tiempo real, ¿te ayudó a entender 
mejor el ejercicio? 
Fuente: Elaboración propia, 2025. 
Finalmente, el Gráfico 4.17 compara la facilidad del nuevo sistema frente al goniómetro: 39,6% 
lo percibió “mucho más fácil” y 41,7% “un poco más fácil”, mientras que 18,8% lo consideró 
equivalente y nadie afirmó que el método tradicional sea más sencillo. Esta evidencia cierra el 
hilo argumental: clarificar y temporizar mejor las instrucciones potenciará el aprovechamiento de 
los indicadores, y ambos elementos, a su vez, consolidan la superioridad percibida del sistema 
en facilidad de uso, respaldando su adopción sostenida en la práctica docente. 
145 
Gráfico 4.17 Compara esta experiencia con usar un goniómetro (la "regla" para medir ángulos). 
¿Qué te pareció más fácil de entender? 
Fuente: Elaboración propia, 2025. 
4.3.3 NÚMERO DE FALLAS Y OBSERVACIONES 
Se documentaron incidencias frecuentes y su mitigación: 
• Oclusiones por ropa holgada en codo/rodilla → vestimenta ajustada, reintento. 
• Cambio de escala aparente por avance/retroceso del sujeto → marcas de pie y 
recordatorio verbal. 
• Torsión fuera de plano (> ≈15°) que degrada ángulos 2D → repetir intento y reforzar 
alineación del tronco. 
• Se puso la información de altura donde se debe colocar la cámara, pero es por usuario y 
solo cuando el administrador los registra. Se concluyo el error de no haber puesto opción 
de cambiar la altura según el usuario.  
• Programación de detección de cámaras ralentiza el sistema y tarda.  
4.4 RESULTADOS EN CONTEXTO DE PRUEBAS DE CAMPO  
Las pruebas se realizaron en aula con iluminación ambiental uniforme y fondo no distractor. El 
control del encuadre por altura Z manualmente y marcas de suelo facilitó la repetibilidad entre 
sujetos. Se obtuvieron registros válidos en hombro, codo, cadera y rodilla.  
Figura 4.25 Explicación del sistema. 
146 
Fuente: Elaboración propia, 2025. 
Figura 4.26 Explicación de la toma de mediciones. 
Fuente: Elaboración propia, 2025. 
Figura 4.27 Mediciones con goniómetro 
Fuente: Elaboración propia, 2025. 
Figura 4.28 Análisis en tiempo real (I) 
147 
Fuente: Elaboración propia, 2025. 
Figura 4.29 Análisis en tiempo real (II) 
Fuente: Elaboración propia, 2025. 
4.5 DISCUSIÓN DE LOS RESULTADOS  
4.1. Síntesis de hallazgos y validez interna 
Los resultados muestran una relación casi lineal entre BioTrack y el goniómetro (R²≈0,996; 
pendiente≈0,99), con un sesgo promedio de +1,26° y límites de concordancia ~ [−6,62°, +9,13°]. 
Esta combinación sugiere exactitud alta (sesgo pequeño y constante) y precisión moderada 
(dispersión de ~±8–9°), adecuada para docencia y cribado, aunque todavía perfectible para 
decisiones clínicas finas. La literatura reporta comportamientos comparables para soluciones 
RGB/RGB-D basadas en “pose tracking” cuando se controla la geometría de cámara y el plano 
de movimiento, por lo que estos hallazgos son coherentes con antecedentes metodológicos. 
4.2. Análisis por articulación 
El error absoluto promedio fue menor a 5° en codo (2,50°), rodilla (2,89°), hombro (3,01°) y cadera 
(3,79°), y superó el umbral en tobillo (5,93°). Este patrón concuerda con limitaciones conocidas 
148 
de los métodos 2D ante oclusiones de maléolos y ambigüedad de profundidad en el pie. Para 
miembros con ejes y puntos anatómicos bien expuestos (codo/rodilla) el desempeño es superior, 
mientras que la complejidad geométrica y las oclusiones del tobillo penalizan la estimación. La 
literatura sugiere que incorporar restricciones de rango fisiológico y/o un modelo humanoide 
durante el cálculo angular reduce errores en segmentos distales. 
4.3. Comparación con trabajos previos 
Estudios de validación con MediaPipe/Kinect frente a sistemas de referencia (p. ej., 
Qualisys/Vicon) han reportado concordancias “aceptables” para evaluación biomecánica cuando 
se estandariza la captura y se filtra la calidad de landmarks. Los presentes resultados se alinean 
con ese rango y confirman que, en un contexto educativo, una arquitectura RGB de bajo costo 
puede reproducir la tendencia de un instrumento manual con sesgos pequeños y varianza 
controlable. 
4.4. Fuentes técnicas del error y sesgo observado 
El sesgo positivo (~+1–2°) es consistente con: (i) pequeñas desalineaciones del plano de 
movimiento respecto a la cámara; (ii) escala relativa por perspectiva; y (iii) selección de landmarks 
con baja confianza. La varianza (σ≈4°) se explica por variaciones de foco/iluminación, ropa 
holgada y heterogeneidad de la ejecución en aula. La evidencia recomienda: SOP estrictos de 
cámara (distancia, altura y ángulo), marcadores de escala y verificación automática de calidad de 
pose para descartar capturas con confianza insuficiente. 
4.5. Implicaciones prácticas para docencia y uso formativo 
Con errores <5° en cuatro articulaciones y concordancia global alta, BioTrack permite: (i) 
retroalimentación inmediata sobre técnica y amplitud; (ii) comparación objetiva con rangos de 
referencia durante prácticas; y (iii) registro trazable para análisis posterior. En términos 
pedagógicos, el sistema cubre la necesidad detectada de estandarizar mediciones y reducir la 
dependencia del criterio del evaluador en ejercicios de aula. 
4.6. Limitaciones del estudio 
Diseño y muestra: N=134 pares de medidas, con distribución desigual por articulación y sin 
repetibilidad intra-observador cuantificada. 
149 
Configuración 2D: una sola cámara y un único plano de análisis, lo que incrementa la sensibilidad 
a la perspectiva, especialmente en tobillo. 
Referente: el “patrón oro” fue goniómetro manual (no un sistema óptico multicámara), por lo que 
los límites de concordancia incorporan el error humano del referente. Estas limitaciones son 
inherentes a escenarios académicos de bajo costo reflejados en la literatura. 
4.7. Mejoras priorizadas (horizonte 2–3 meses) 
Estandarización de captura (SOP): fija distancia/altura de cámara, plano sagital/coronal por 
ejercicio y marcas de suelo/escala; documenta tolerancias geométricas. Esto ha demostrado 
reducir varianza en validaciones con RGB/RGB-D. 
Filtro de calidad de pose: umbrales de confianza por landmark, detección de oclusión y re-take 
automático; descarte de fotogramas fuera de plano. 
Ajuste por articulación: calibración corta (offset) para compensar el sesgo global y afinamiento 
del cálculo angular con restricciones de ROM fisiológico. 
Caso tobillo: guía visual para alineación del pie, aumento de apertura lateral y regla auxiliar tibia
calcáneo/eje del pie; si es viable, módulo 2,5D con penalización por salir de ROM. 
Repetibilidad: subestudio con 10–15 repeticiones por articulación para estimar error intra
observador, RMSE y LOA con IC95%. 
