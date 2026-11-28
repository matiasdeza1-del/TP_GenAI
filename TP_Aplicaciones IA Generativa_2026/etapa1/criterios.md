# Hornero · Decisiones de diseño de la Etapa 1

Bitácora histórica compartida del equipo. El estado vigente y los responsables se
mantienen en `../../docs/ROADMAP.md`; las notas anteriores pueden describir pasos
que luego se completaron o decisiones que se reemplazaron. Agregar nuevas entradas
con fecha, tarea, decisión, alternativa y evidencia de pruebas.

## Verificación técnica del 26/11/2026 · E1-03

Se verificó en Windows/Python 3.12.10 con entorno en una ruta corta. Seis pruebas
reproducibles en `../tests/test_funcionamiento.py` pasaron sin API, con respuestas
simuladas y CSV temporal. `../scripts/verificar_funcionamiento.py --live` comprobó
imports, arranque de ambas interfaces, extracción del PDF, 26 chunks, embeddings,
construcción/recarga FAISS y lectura/escritura temporal. Una consulta real a Groq
completó estratega, redactor y revisor en 4,7 s. Se corrigió UTF-8 explícito en el
JSON del índice. El CSV original quedó intacto con ocho filas.

También se comprobó HTTP 200 del servidor Streamlit y se detuvo el proceso de prueba.
Esta verificación no evalúa tono, hechos ni calidad editorial y no cierra E1-04.
El detalle del entorno y los límites está en `../../docs/BITACORA.md`.

## Paso 1 · Entorno y arquitectura (24/11/2026)

Usamos el entorno virtual compartido de la materia con Python 3.11.15. Consideramos crear uno exclusivo para el TP. La simulación de instalación conjunta resolvió los requisitos sin reemplazar versiones existentes. Después de instalar Streamlit, los 196 paquetes pasaron la comprobación de compatibilidad. En la app base, la pregunta sobre la fecha produjo una llamada a fecha_de_hoy y una respuesta. Queda por probar la ejecución independiente desde etapa1/ una vez armada.

### Flujo acordado

| Agente | Información disponible | Responsabilidad |
| --- | --- | --- |
| Estratega | Pedido, guía e historial editorial | Elaborar un brief con público, canal, objetivo, hechos autorizados, reglas y antecedentes relevantes. |
| Redactor | Brief y, en una segunda pasada, borrador y observación | Escribir la pieza y realizar la corrección solicitada. |
| Revisor | Borrador, requisitos del pedido, antecedente relevante y acceso a la guía | Evaluar la pieza, explicar el ajuste necesario o identificar el dato faltante. |

El StateGraph ejecuta los tres roles en secuencia. Cada nodo selecciona los campos que incorpora al contexto del agente. Para evaluar la originalidad de un push, por ejemplo, el revisor necesita conocer el enfoque del push anterior. Alcanza con pasarle ese antecedente.

El revisor puede aprobar, solicitar una corrección o indicar que falta información comercial. El código lleva la cuenta de las correcciones por pedido. La primera observación devuelve el borrador al redactor. Una segunda observación cierra la ejecución con la pieza pendiente. Un dato comercial faltante da lugar a una consulta al usuario desde la primera revisión. Solo las piezas aprobadas pueden guardarse.

Consideramos que el revisor editara directamente. Elegimos mantener la autoría en el redactor y hacer visible qué observó el revisor y cómo se corrigió. El costo máximo de esa decisión es una ejecución adicional de cada uno de esos dos nodos. Una prueba prevista consiste en forzar dos pedidos de ajuste consecutivos y comprobar que el flujo finalice sin escribir en el CSV.

### Contrato de entrega

La carpeta etapa1/ debe poder ejecutarse con streamlit run main.py. La interfaz invoca responder(pregunta) y recibe respuesta y detalle. Cada entrada de detalle contiene titulo y contenido. El diseño del grafo está acordado y su implementación y validación quedan pendientes.

## Próxima decisión · Recuperación de reglas de marca

Evaluar chunks por sección y por fila de canal frente a ventanas de tamaño fijo. Usar como caso de prueba un WhatsApp con descuento. La evidencia recuperada debe permitir identificar tanto las reglas de WhatsApp como los legales de la promoción.

## Paso 2 · Primera prueba de recuperación

Extrajimos 26 fragmentos de la guía, conservando encabezados en las filas de las tablas. Usamos el modelo multilingüe de Clase 1 con vectores normalizados e IndexFlatIP para buscar por similitud coseno. Guardamos el índice y los textos juntos. La segunda ejecución reutilizó el índice y reprodujo el orden de resultados. En este entorno macOS se usó un hilo OpenMP tras un fallo de ejecución con la configuración por defecto.

Para el WhatsApp de Nuevos con descuento en Cocina, el segmento quedó primero, el canal segundo y el legal de descuentos quinto, después del legal de cuotas. Un top 3 omitiría una regla obligatoria. Antes de fijar la cantidad de fragmentos, queda evaluar las demás consultas del TP y comparar con búsquedas específicas por tipo de regla.

## Comparación sobre las cuatro consultas oficiales

Con el mismo índice, comparamos el pedido completo con subconsultas manuales por canal, segmento explícito y situación aplicable. En la segunda estrategia intercalamos los resultados por puesto y quitamos duplicados. Ambas entregaron cinco fragmentos. Contamos como acierto recuperar el bloque específico de referencia.

| Caso | Bloques de referencia | Pedido completo | Subconsultas |
|---|---|---:|---:|
| Instagram | Instagram, Premium, tono de lanzamiento | 1/3 | 2/3 |
| Email | Email, recuperación, plazos de entrega | 1/3 | 3/3 |
| WhatsApp | WhatsApp, Nuevos, descuentos | 3/3 | 2/3 |
| Push | Push, Recurrentes | 1/2 | 2/2 |

En total se recuperaron 6 y 9 de las 11 referencias respectivamente. Los fragmentos fuera de esa selección ocuparon 4111 y 2592 caracteres. Pueden aportar contexto complementario. La estrategia por subconsultas perdió el legal de descuentos y omitió el tono de lanzamiento. La prueba mide recuperación con subconsultas formuladas a mano, sin evaluar la capacidad de un agente para derivarlas ni la calidad del texto final. Para el push, la verificación de repetición requiere además el historial editorial.

## Prueba de recuperación híbrida

Sobre los mismos cuatro pedidos y referencias, detectamos menciones explícitas de los cinco canales, tres segmentos y tres tipos de promoción mediante coincidencia de palabras. Seleccionamos las filas o reglas correspondientes por encabezado y completamos hasta cinco fragmentos únicos con el ranking FAISS del pedido completo. No hubo clasificación por LLM.

En orden Instagram, Email, WhatsApp y Push, la cobertura fue 2/3, 2/3, 3/3 y 2/2. Total 9/11, con 3266 caracteres fuera de las referencias elegidas. Faltaron el tono de lanzamiento y la regla sobre plazos. Se recuperó el legal de descuentos ausente en la estrategia por subconsultas. La detección literal se evaluó solo en pedidos con menciones afirmativas. Quedan sin evaluar sinónimos, negaciones y ambigüedades. La prueba se ejecutó sin integrar una tool al agente.

## Tool de consulta de la guía

consultar_guia_marca recibe situación, canal, segmento y promoción aplicable. Selecciona fragmentos por encabezado y completa hasta cinco con FAISS. Los legales promocionales entran por el campo promoción para evitar activar un beneficio por mera similitud. Esto hace que la interpretación del pedido por el agente sea decisiva. El contrato actual admite un beneficio por llamada.

Prueba aislada mediante invoke, reutilizando el índice guardado. Para WhatsApp y Nuevos con descuento devolvió tres reglas obligatorias y dos fragmentos complementarios. Con promoción ninguna devolvió dos reglas obligatorias y tres complementarios. Verificamos que el legal de descuento solo se seleccionó en el primer caso. La interpretación autónoma de ambos pedidos por el LLM queda pendiente.

## Prueba de argumentos generados por el modelo

Probamos dos pedidos independientes con create_agent, Groq openai/gpt-oss-20b, temperatura 0 y reasoning_effort bajo. El prompt pidió consultar la guía para producir un brief. En una corrida por pedido, el modelo hizo una llamada exitosa a consultar_guia_marca con WhatsApp y Nuevos en ambos casos. Para el 15 % en Cocina indicó descuento y se recuperó el legal. Para la variante sin descuento indicó ninguna y se recuperaron las reglas de canal y segmento. En el primer caso usó el pedido entero como situación y en el segundo solo “Cocina”. Esta prueba verifica selección de argumentos en esos dos ejemplos. La calidad del brief y la estabilidad entre corridas quedan por evaluar.

## Historial editorial de lectura

consultar_historial lee el CSV en cada llamada para ver nuevas aprobaciones. Filtra por canal y segmento opcionales e incluye piezas dirigidas a Todos cuando busca para un segmento concreto. Devuelve hasta tres antecedentes por fecha descendente, con título y hasta 320 caracteres de texto para acotar el contexto. Una campaña anterior puede quedar fuera de esa ventana.

En una prueba aislada con Groq, el modelo eligió Push y Recurrentes, recuperó el push del 20/10 e identificó su título y llamado a la acción como elementos a evitar. Sugirió como alternativa una oferta exclusiva sin sustento en el pedido. En el brief final habrá que controlar que las ideas respeten los hechos autorizados. Se comprobó también una búsqueda sin coincidencias y la inclusión de comunicaciones a Todos.

## Prototipo del estratega

Implementamos un brief validado con Pydantic y ToolStrategy para pasar campos específicos al redactor. En el push oficial, la primera corrida consultó guía e historial, recuperó «Preparate para el calor» y los límites 40/90, pero propuso una línea nueva, eficiencia energética y garantía de postventa sin respaldo. Tras reforzar el prompt, la segunda corrida mantuvo los límites y consignó tema, canal y segmento, pero omitió la consulta al historial y sugirió control inteligente y eficiencia energética. El esquema asegura la forma del brief. La obligatoriedad de las consultas y el respaldo de las afirmaciones quedan pendientes antes de integrar el redactor.

## Evidencia obligatoria antes de elaborar el brief

preparar_brief invoca ambas tools desde Python y entrega el pedido y sus resultados al estratega. Por ahora el llamador suministra canal, segmento y promoción. En la primera prueba con evidencia precargada se recuperó el antecedente del 20/10, pero el brief todavía sugirió ahorro y facilidad de instalación. Pedimos una sola acción útil y dimos como ejemplo medir el espacio disponible. La segunda prueba conservó el antecedente y los límites 40/90 y elaboró ese consejo sin afirmar prestaciones. Es una prueba con un ejemplo explícito en el prompt. El modelo todavía mezcló reglas de canal en hechos_autorizados. Quedan por validar otros pedidos y el tratamiento de hechos antes de pasar el brief al redactor.

## Separación de fuentes en el brief

Python conserva el pedido original, los filtros, la guía recuperada y el historial en campos separados. El modelo genera únicamente objetivo, enfoque, antecedentes a evitar y datos faltantes. Así, los datos comerciales se contrastan con el pedido original y las reglas conservan el texto de la guía. Se mantiene el alcance de la materia: RAG, tools, prompts y transferencia explícita de contexto entre agentes.

Probamos el push y el email de recuperación con Groq y con filtros suministrados por el llamador. Ambos conservaron el pedido y las reglas obligatorias del canal. Al generalizar el prompt y quitar el ejemplo de aires, el push volvió a sugerir cuotas y ahorro sin respaldo. En el email, el agente propuso un cupón y un destino de enlace sin registrarlos como datos faltantes. La separación de fuentes permite revisar esas afirmaciones contra el pedido, pero la estrategia generada sigue requiriendo revisión. Antes de aprobar o guardar, el flujo debe tratar como pendiente cualquier beneficio o dato indispensable sin respaldo.

## Integración en Streamlit

La Etapa 1 usa StateGraph para ejecutar estratega, redactor y revisor. El estratega identifica los campos del pedido y carga guía e historial. El redactor recibe el pedido, las reglas y la estrategia. El revisor recibe el borrador, el pedido, las reglas y un antecedente. Un contador de Python limita la devolución al redactor a una ronda. El código comprueba los largos del canal y solo invoca la escritura si hay veredicto favorable y pedido de guardado.

En un CSV temporal, verificamos que dos pedidos de corrección terminan sin agregar filas, que corrección seguida de aprobación agrega una fila y que pedir datos termina sin agregar filas. En Streamlit, el primer push quedó pendiente tras dos revisiones por largo. Después de precisar el máximo y las observaciones, otro push y un post de Instagram obtuvieron aprobación del modelo. La revisión humana detectó tuteo en el push y acceso anticipado sin sustento en Instagram. Se reforzaron ambos prompts en esos puntos. El email terminó pendiente y su observación llegó a sugerir un cupón sin respaldo. El caso WhatsApp encontró un error del proveedor durante la tanda. Se agregó manejo de errores de Groq en la interfaz. Las aprobaciones del modelo siguen necesitando contraste con la guía y el pedido.

En la corrida posterior, el revisor confundió «Elegí» con tuteo. Añadimos formas correctas y formas a corregir al prompt del revisor. La calidad lingüística sigue pendiente de validación con el prompt actualizado. La app responde en localhost:8502 y la prueba de escritura usó un archivo temporal.

## Correcciones a partir de la prueba manual en Streamlit

El push aprobado incluyó «cada 15 días» y «Abre la app». El WhatsApp quedó pendiente sin pedir claramente el enlace. Adelantamos la comprobación de datos del descuento al estratega: para WhatsApp sin enlace, pide el enlace y termina antes de redactar o guardar. En push, el código marca para corregir duraciones numéricas ausentes del pedido y la etiqueta literal «Abre la app». Son controles acotados y no validan todas las afirmaciones posibles. Ambas rutas se comprobaron con respuestas simuladas del modelo.

## Borrador visible cuando falta el enlace de WhatsApp

En una prueba manual, el chat mostró solo el veredicto y dejó en el detalle un borrador con fechas y URL ficticias. El caso WhatsApp con descuento sin enlace ahora muestra en el mensaje principal una plantilla pendiente de aprobación con un marcador de enlace. Python reutiliza el porcentaje y las categorías reconocidas cuando aparecen explícitamente. AppTest verificó el pedido del 15 % en Cocina con clasificación simulada, sin escritura en el CSV.

## 26/11/2026 · Evaluación manual de Instagram Premium · E1-04

Fuente: salida y detalle compartidos por el usuario desde la aplicación de Etapa 1; no es una nueva ejecución ni una prueba simulada. Pedido: anunciar la nueva colección de muebles de exterior para Premium en Instagram.

El recorrido observado fue estratega, redactor, revisión con corrección, redactor y segunda revisión con corrección. Terminó pendiente al agotarse la única ronda permitida, de acuerdo con el diseño. La primera versión no tenía hashtags y ambas versiones escribieron «Elegi» sin tilde. El revisor pidió los hashtags en la primera revisión, pero detectó la tilde recién en la segunda. Se desperdició la oportunidad de corregir todos los errores juntos.

La exigencia de agregar emojis fue un falso requisito: la tabla de Instagram dice «hasta 3» y las reglas de voz fijan un máximo, no un mínimo. Sí corresponde exigir de tres a cinco hashtags e incluir `#HorneroEnCasa`. La segunda versión cumplía esos conteos, pero conservó la falta de tilde.

Hay una inconsistencia de fuentes que requiere decisión: la sección 7 de la guía menciona acceso anticipado para Premium y la sección 9 lo usa en un ejemplo; en cambio, los prompts de redactor y revisor exigen respaldo en el pedido para esa afirmación. El estratega la propuso y el revisor afirmó que no había datos sin respaldo. Hay que acordar si esas reglas de segmento autorizan un beneficio permanente o si cada campaña debe confirmarlo y aplicar el mismo criterio en los tres roles.

El estratega colocó el ejemplo negativo de la guía en `antecedentes_a_evitar`. Eso no es una pieza histórica. La consulta al CSV actual con los mismos filtros de canal Instagram y segmento Premium/Todos no devuelve filas; ese caso debe representar explícitamente ausencia de antecedentes, sin transformar ejemplos de la guía en historial.

Próximo trabajo: alinear política de fuentes; separar controles objetivos de formato y revisión semántica; recoger todas las observaciones en la primera revisión y evaluar de nuevo. No se modificaron prompts ni se relajó el límite de correcciones en esta evaluación. E1-04 sigue en curso.

## 26/11/2026 · Controles de formato y revisión conjunta · E1-06, E1-07

El usuario autorizó implementar controles objetivos y consolidar las observaciones. La decisión sobre beneficios de segmento se mantiene pendiente en E1-08: puede tratarse el acceso anticipado como derecho permanente de Premium o como beneficio que se confirma por lanzamiento. No se cambió automáticamente esa política.

`validaciones.py` centraliza los límites de la sección 4 de la guía para Instagram, Email, WhatsApp, Push y LinkedIn. Controla largos, palabras del email, cantidad de hashtags, `#HorneroEnCasa` y máximos de emojis. Cero emojis es válido. Para Instagram, WhatsApp y LinkedIn cuenta título y cuerpo publicados; para Push y Email aplica límites separados. Los caracteres se cuentan en Unicode NFC con `len`; los emojis por secuencias visibles, sin contar por separado tonos de piel, banderas o familias. `regex` se declara como dependencia directa; ya estaba instalado y fijado en el lock. Si cambia la guía, revisar también esta tabla de reglas.

El redactor recibe la misma configuración que usa Python. El revisor devuelve todas las categorías en una respuesta estructurada: ortografía, tono, respaldo, repetición, contenido y datos faltantes. Python reúne esa respuesta con los hallazgos objetivos y calcula el veredicto. Un dato faltante conserva los otros hallazgos y termina pendiente. Se mantiene una ronda de corrección y el guardado exclusivo de piezas aprobadas a pedido del usuario.

Las primeras pruebas reales detectaron la tilde y los hashtags juntos, pero el modelo produjo explicaciones contradictorias en tono. Por eso ortografía y tono ahora requieren citas literales con reemplazo concreto. Se eliminan cambios idénticos y duplicados; una cita que no aparece en la pieza se marca para revisión. Los demás juicios editoriales siguen dependiendo del modelo: la estructura no garantiza detectar todos los errores.

Alternativa descartada: aumentar rondas para compensar revisiones parciales.

Validación final: `python -m unittest discover -s tests -v` pasó 16/16 y `pip check` no detectó conflictos. En una revisión real del primer borrador del usuario, Groq devolvió juntos los dos hallazgos de hashtags y el reemplazo «Elegi» por «Elegí», sin exigir emojis ni agregar observaciones de tono. `python scripts/verificar_funcionamiento.py --live` comprobó ambas interfaces, RAG, CSV temporal y el grafo con el nuevo esquema editorial (cinco pasos de detalle, 5,4 s del bloque de grafo). CSV original intacto. Pruebas ejecutadas en Windows; el código no usa rutas ni lógica específicas del sistema operativo. Los cambios quedan locales, sin commit/push en esta tarea. E1-04 y la política de negocio E1-08 siguen pendientes de cierre.

## 26/11/2026 · Prioridad de la guía de marca · E1-08

Decisión del usuario: debe primar la guía. La sección 7 declara el acceso anticipado como beneficio de Premium; no exige confirmarlo por lanzamiento. La condición de reconfirmación había sido agregada en prompts y se retiró. Las entradas anteriores conservan la discusión previa; esta decisión la resuelve.

Se agregó `POLITICA_FUENTES` compartida por estratega, redactor y revisor: la guía determina reglas y beneficios explícitos del segmento; el pedido determina los detalles de la campaña. Un beneficio permitido no obliga a incluirlo. Ejemplos, historial y textos de legales no autorizan promociones nuevas. El acceso anticipado no permite inventar cuántas horas o días de ventaja hay, porcentajes, códigos ni fechas. La misma política queda indicada en AGENTS para evitar que futuros cambios la contradigan.

Validación: 16/16 tests técnicos OK. En dos consultas reales al revisor, una pieza Premium con «la ves antes que nadie» fue aprobada y otra que agregaba 10 % de descuento y código PREMIUM10 fue marcada para corregir por falta de respaldo. Ambas usaron la guía recuperada y el pedido original, sin guardar piezas. E1-08 se cierra; E1-04 requiere repetir las cuatro consultas oficiales con la versión actual.

La verificación completa `python scripts/verificar_funcionamiento.py --live` también pasó con la política compartida: ambas interfaces, RAG y persistencia temporal OK; estratega, redactor y revisor completaron tres pasos de detalle en 5,2 s del bloque de grafo. CSV original intacto.

## 27/11/2026 · Reinicio para pruebas manuales · E1-03, E1-04

Al reiniciar la app se observó que el navegador conectaba y mostraba «Stop», pero no llegaba a renderizar el título mientras se importaban dependencias de IA. `main.py` importaba `agentes` antes de mostrar la interfaz. Se movió ese import al bloque de la primera consulta, dentro del indicador «Pensando...», para mostrar el título y el chat sin esperar esa carga. No cambia la lógica de agentes ni los datos.

Tras reiniciar de nuevo, Chromium confirmó título de Marketing y entrada de chat visibles en `127.0.0.1:8502`. Se abrió la aplicación en el navegador del usuario para repetir las cuatro consultas oficiales. Esta comprobación de arranque no invocó Groq ni modificó el CSV.

Regresión del cambio de arranque: `python -m unittest discover -s tests -p test_funcionamiento.py -v` pasó 9/9, incluida la interacción con el chat y la presentación de respuesta y detalle con el agente simulado.

## 27/11/2026 · Retirar restricciones añadidas · E1-09

El usuario reportó cuatro salidas reales: Instagram aprobado con «solo para Premium», email con un cupón inventado de $15 y pedido de legales para sostenerlo, WhatsApp frenado antes de los agentes y push con línea nueva y cuotas no confirmadas. Solicitó retirar los guardrails que no surjan de la guía.

Se revisaron las secciones 2–8 de la guía y los requisitos mínimos de la consigna. Los legales sí existen: la sección 6 los exige para descuentos, cuotas y envío sin cargo; la sección 8 pide un beneficio concreto con legales para recuperación. La consigna también exige no inventar datos. Se conservan esos requisitos. No se toma la oferta ficticia del redactor como un nuevo requisito que el usuario deba completar.

Se retiraron: el corte por regex de URL o fechas antes de redactar; la plantilla fija de WhatsApp; los filtros especiales sobre «Abre la app» y duraciones de mantenimiento en push; la revisión obligatoria en seis categorías y el bloqueo por citas que no coincidían literalmente. El revisor vuelve a un veredicto y una observación conjunta, exigiendo fundamento en la guía o el pedido. Repetir un saludo o una fórmula de empatía de la guía no equivale a repetir una campaña. El largo ideal de Instagram no es su máximo.

La respuesta final siempre incluye la pieza completa. Los datos necesarios sin definir aparecen como `[PENDIENTE: dato]`, con las aclaraciones al final. Si un borrador inventó algo, vuelve al redactor para retirarlo o marcar el dato, en vez de preguntar por condiciones legales de ese invento. Se conserva una ronda para acotar llamadas. Una pieza con marcadores no se guarda en el historial de aprobados.

La recuperación de la guía incluye voz, prohibiciones, reglas generales y política de entregas; luego canal, segmento y promoción aplicables, más tres fragmentos relevantes por similitud. Reglas de otros canales, segmentos, promociones y ejemplos no entran como contexto adicional. Los legales generales se pasan por separado al revisor, sin convertirlos en ofertas para la generación. Sin historial, Python conserva `antecedentes_a_evitar=[]` para no presentar un ejemplo de la guía como antecedente real.

Regresión inicial: 17/17 pruebas técnicas OK. Se están ejecutando las cuatro consultas originales con Groq y una copia temporal del CSV para contrastar los cambios con los casos reportados.

La primera tanda con el modelo 20B mostró una aprobación incorrecta de envío sin cargo no solicitado, dos errores HTTP 400 al generar nombres de tools inexistentes y un límite HTTP 429 de tokens/minuto. Una prueba con 120B conservando `ToolStrategy` también mostró el error de tool inexistente; el tamaño de modelo por sí solo no resolvía el transporte.

Se reemplazó la simulación de tools de salida por `ProviderStrategy` con JSON Schema nativo, soportado por Groq para GPT-OSS. Los esquemas solo fijan la forma de los datos; no agregan condiciones editoriales. La primera clasificación real con ese modo pasó. Se usa 120B por defecto para evaluar la calidad, con `HORNERO_MODELO` configurable y sin cambiar el `.env` local del usuario. `langchain>=1.2` declara el mínimo necesario para esta opción; el lock instalado ya lo cumple. Las consultas de comparación se espacian para no confundir el límite del proveedor con una falla editorial.

El brief ya no tiene un campo `datos_faltantes`: las pruebas mostraron que el modelo lo llenaba con datos opcionales y luego los convertía en obligaciones. Los tres roles reciben canal, segmento y promoción extraídos del pedido. La generación usa el pedido y las reglas aplicables; el revisor recibe además los legales condicionales. Se usa razonamiento medio en estrategia, redacción y revisión, y bajo para clasificar.

Cierre técnico de E1-09: 21/21 pruebas locales OK, comprobación de dependencias sin conflictos, script de funcionamiento sin API OK y servidor reiniciado con los cambios en 8502. Se agregaron regresiones para no mezclar contextos, preservar enlaces provistos, retirar enlaces/códigos improvisados y evitar CTA vacíos en WhatsApp. Las pruebas reales se hicieron sobre copias del CSV. Los cambios quedan locales, sin commit ni push. Esto cierra el ajuste de restricciones y presentación; la calidad editorial E1-04 sigue en evaluación.

En WhatsApp el redactor genera el cuerpo; el código añade un único enlace para CTA y bases, tomado de las fuentes, o `[PENDIENTE: enlace a bases]`. No se verifica el sitio ni se exige una validación "oficial". Se descartan enlaces generados y cláusulas de código promocional improvisadas cuando no se pidió código. Se evitan los CTA vacíos tras separar el enlace. Las aclaraciones finales se concentran en los marcadores reales, no en requisitos adicionales inventados por el revisor. Para Push se aclara la acción de abrir la app respetando el voseo, sin exigir la cadena literal «Abre la app».

Se completó una tanda real de las cuatro consultas con el CSV temporal y se hicieron regresiones puntuales de WhatsApp. El anuncio dejó de pedir nombre, materiales, imagen y fecha; el email quedó con un único marcador de beneficio y condiciones. Otras iteraciones todavía mostraron errores semánticos (propiedades o financiación no confirmadas y confusiones con los enlaces), por lo que E1-04 no se declara cerrada. Los ajustes de formato y procedencia de enlaces se comprobaron además con pruebas locales. Algunas llamadas reales tardaron 50–100 s, incluyendo carga inicial y esperas del proveedor; no se usa esa tanda como evaluación estadística ni como tabla de tiempos de Etapa 2. Reportes intermedios en `.cache/` local, no versionados. CSV original intacto.

## 27/11/2026 ? Volver al modelo original ? E1-04

Por pedido del usuario, Marketing vuelve a `openai/gpt-oss-20b` como modelo predeterminado y en `.env.example`. El trabajo sobre calidad debe centrarse en los prompts y el flujo con ese modelo. Se conserva el formato JSON nativo entre roles. La prueba con 120B queda como antecedente; no es la configuraci?n vigente. La evaluaci?n editorial con 20B sigue pendiente.

Verificacion del cambio: 21/21 tests locales OK; modelo efectivo de `_llm()` confirmado como `openai/gpt-oss-20b` sin invocar la API. Aplicacion reiniciada en el puerto 8502. No se repitio la tanda editorial con Groq.

## 27/11/2026 ? Evaluacion con 20B y revision del RAG ? E1-04

La primera tanda con razonamiento medio produjo tres errores 400 de JSON y una clasificacion que no reconocio email. Se cambio a razonamiento bajo y se aclaro el canal en el prompt. Los 21 tests y una prueba real de funcionamiento pasaron. Una segunda tanda completo las cuatro consultas usando una copia del CSV, pero no cierra la evaluacion editorial: Instagram incluyo materiales resistentes no confirmados; el email invento cupon y contacto y el revisor repitio observaciones; WhatsApp agrego primera compra; el push excedio el largo aun despues de una correccion.

Inspeccion del RAG con consultas representativas: devolvio reglas de Instagram y Premium, y la seccion de recuperacion para el email. Recupera reglas generales y filtros por canal, segmento y promocion, y hasta tres fragmentos por similitud; aparecieron fragmentos de poca relevancia. La seccion de recuperacion depende de quedar entre esos tres resultados y el filtrado depende de una clasificacion previa. No hay evidencia de que la recuperacion explique por si sola las afirmaciones inventadas: las instrucciones relevantes tambien llegan a los agentes. Falta evaluar recuperacion con las consultas exactas y mejorar trazabilidad, prompts y revision. El CSV original permanece intacto.

## 27/11/2026 · Revisar contexto para las cuatro consultas · E1-04

Se reconstruyó la recuperación para los textos exactos de las cuatro consultas con los campos previstos y el historial original: `.cache/contexto-e1-04.json` conserva la salida local completa. No es una traza capturada de los mensajes de una ejecución real. Instagram incluyó reglas de Instagram y Premium; email incluyó recuperación; WhatsApp incluyó descuento y Nuevos; push incluyó Push y Recurrentes. Sin embargo, recuperación apareció también por similitud en WhatsApp y push. Algunos otros fragmentos eran poco relevantes.

El estratega recibe pedido, guía sin los legales generales e historial; el redactor recibe pedido, reglas, estrategia y controles de formato; el revisor recibe reglas, legales condicionales, un antecedente y pieza. El clasificador ahora identifica si se trata de recuperación y esa sección se selecciona por ese campo, evitando incluirla en otros pedidos por similitud. La corrección depende de la clasificación y debe seguir evaluándose. Se dejó de ocultar el resto de observaciones del revisor cuando hay marcadores pendientes, y se pidió una revisión breve sin repetir puntos. No se garantiza que el modelo lo cumpla.

Validación: 22 tests locales y una ejecución real completa del grafo con Groq, sin evaluación editorial. Al probar los cuatro clasificadores, los cuatro identificaron bien canal y recuperación, pero email infirió Recurrentes sin que se pidiera. Tras aclarar el prompt, una nueva prueba de ese email devolvió segmento omitido y recuperación verdadera. La tanda editorial completa todavía debe repetirse con estos cambios; E1-04 y E1-05 siguen abiertas. El CSV original quedó intacto.

Tanda editorial posterior: Instagram fue aprobado con materiales de alta calidad no respaldados; email falló por límite 429 de Groq; WhatsApp quedó pendiente por enlace y añadió un marcador [LINK] duplicado; push fue aprobado con cuotas no solicitadas. Se agregó la limpieza del marcador redundante de enlace y los 22 tests locales siguen pasando. Una corrida no demuestra estabilidad: sigue pendiente resolver la revisión de afirmaciones y ofertas no respaldadas y repetir la evaluación, incluido el email. Las pruebas usaron CSV temporal.

## 27/11/2026 · Simplificar la recuperación · E1-04

Por pedido del usuario se mantiene el RAG y se evitan decisiones para casos particulares. La consigna exige RAG, no proveer toda la guía. Se retiró el campo específico de recuperación del clasificador: ahora el buscador semántico puede recuperar esa sección y los tres roles reciben la instrucción general de aplicar cada fragmento solo si corresponde al pedido. Se conservan las reglas generales y las reglas de canal, segmento y promoción identificados, pues la búsqueda semántica les asignó puntajes bajos en algunos casos pertinentes. El umbral de similitud no se ajustó a las cuatro consultas: el puntaje de recuperación fue alto también en un push que no trataba de recuperar clientes. La selección sigue dependiendo de la clasificación del canal, segmento y promoción y la relevancia del contexto debe evaluarse con más variantes.

Se retiró el borrado automático de frases de WhatsApp que contenían «código»: podía ocultar contenido válido y prevenir que el revisor lo examinara. El revisor recibe los antecedentes disponibles y un pedido general de verificar el respaldo de características y condiciones. Estas instrucciones no garantizan detección. Las 21 pruebas locales pasaron y el script funcional sin API verificó la reutilización real del índice y un CSV temporal.

Se hizo una sola tanda acotada en Groq para email y push. El email generó un texto sin beneficio y fue aprobado pese a que la sección recuperada de la guía exige beneficio con legales; push recibió error 429 y no se pudo evaluar. El CSV original quedó intacto. La clasificación por recuperación se había probado previamente, pero ese enfoque se reemplazó y su resultado no valida el actual. El seguimiento de E1-04 debe resolver el uso de las reglas recuperadas, evitar ofertas inventadas y verificar nuevamente las cuatro consultas, sin cambiar de modelo. Las salidas detalladas de la tanda están en `.cache/evaluacion-rag-dos-casos.json` local.

## 27/11/2026 · Intento de corrida completa · E1-04

Se pidió al estratega sintetizar en el enfoque los hechos y reglas aplicables y se pasó el resumen al revisor. Una versión con dos campos adicionales falló en Groq al generar el email porque faltaban esos campos en el JSON; se retiraron y se conservó la indicación dentro del campo de enfoque existente. Se limitó la respuesta de cada llamada a 1024 tokens para reducir la reserva de capacidad; queda por verificar en ejecuciones reales que no trunque las respuestas.

La tanda inicial recibió un límite por minuto. En el segundo intento, Instagram terminó con «durabilidad» sin respaldo claro y el revisor aprobó; email falló por el esquema adicional, luego retirado; WhatsApp recibió error 429 por el límite diario de 200.000 tokens de la cuenta. Groq estimó unos 16 minutos hasta aceptar la solicitud rechazada; eso no garantiza capacidad para una tanda completa. Se detuvo la tanda para evitar reintentos inútiles. La versión posterior al retiro de los campos no tiene una corrida real completa. Las 21 pruebas locales y el script funcional sin API pasaron; CSV original intacto. E1-04 continúa en curso.

## 27/11/2026 · Criterio sobre datos inventados · E1-04

El usuario aclaró que debe controlarse la invención de datos concretos, sin exigir respaldo técnico para cada expresión publicitaria general. La mención anterior de «durabilidad» no debe tratarse automáticamente como incumplimiento. Se ajustaron los prompts y AGENTS para distinguir expresiones generales de especificaciones verificables, precios, plazos, garantías y condiciones comerciales; se mantiene la guía de marca. Falta evaluar el cambio en una corrida real.
