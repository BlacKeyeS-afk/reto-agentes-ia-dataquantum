# Diario de decisiones

## 2026-08-17 — Preparación inicial

- Se ha elegido Python 3.13.15.
- Se utiliza un entorno virtual llamado `.venv`.
- Las claves API no se almacenarán en Git.
- El proyecto se construirá de forma incremental.

## 2026-08-17 — Dependencias iniciales del Nivel Básico

- El proyecto debe poder realizarse sin gastar dinero en APIs.
- Se ha elegido Groq como proveedor del LLM.
- Inicialmente se utilizará el modelo `openai/gpt-oss-120b`.
- Se ha elegido Groq porque dispone de un nivel gratuito y permite evolucionar posteriormente hacia tool/function calling.
- Se utiliza el SDK oficial `groq`.
- Se utiliza `python-dotenv` para cargar `GROQ_API_KEY` desde `.env`.
- Las credenciales reales nunca se almacenarán en Git.
- Por ahora no se utilizarán LangChain ni LangGraph, para entender primero el funcionamiento directo de una API de LLM.

## 2026-08-17 — Primera conexión real con Groq

- Se realizó con éxito la primera conexión real con Groq.
- Se verificó toda la cadena `.env` → Python → SDK → API → modelo → respuesta.
- Codex mostró `conexi�n` por un problema de codificación de su terminal, pero la respuesta real recibida era `conexión correcta`.
- Se decidió utilizar identificadores de código en inglés y mantener en español los mensajes de interfaz.

## 2026-08-17 — Evolución del Nivel Básico a múltiples preguntas

- La primera versión solo permitía realizar una pregunta.
- Se evolucionó a un bucle `while` para permitir múltiples preguntas.
- Se utiliza `break` cuando el usuario escribe `salir`.
- Se utiliza `continue` cuando la entrada está vacía o cuando una consulta falla.
- Se utiliza `.strip()` para eliminar espacios exteriores.
- Se utiliza `.casefold()` para reconocer `salir` independientemente de mayúsculas o minúsculas.
- El cliente de Groq se crea una única vez antes del bucle.
- Cada petición contiene únicamente la pregunta actual.
- Todavía no existe memoria ni historial, porque se implementarán en el Nivel Intermedio.
- Los errores de una consulta no cierran completamente el programa; el usuario puede seguir preguntando.

### Pruebas realizadas y revalidadas el 2026-08-20

- Entrada formada solo por espacios seguida de `salir`: mostró `Debes escribir una pregunta.`, volvió a solicitar una entrada, no llamó a Groq y finalizó con `Hasta luego.`.
- Comando `SALIR` en una ejecución nueva: se reconoció independientemente de las mayúsculas, no llamó a Groq y finalizó con `Hasta luego.`.
- Sesión con dos preguntas y `salir`: realizó exactamente dos llamadas, respondió `Roma.` a la pregunta sobre la capital de Italia, respondió `15` a la suma y finalizó correctamente.
- Aislamiento entre preguntas: se comprobó en el código que cada petición crea una lista `messages` nueva con solo la pregunta actual, sin memoria ni historial.
- No se produjeron errores reales del programa durante estas pruebas.

## 2026-08-21 — Memoria conversacional del Nivel Intermedio

- Se creó `src/nivel_intermedio.py` sin modificar el Nivel Básico.
- Se introdujo una lista `messages` persistente durante la ejecución.
- El historial comienza con un mensaje con `role="system"`.
- Cada pregunta válida se añade con `role="user"` y se envía a Groq toda la lista `messages`.
- Cada respuesta válida se añade con `role="assistant"`, lo que permite memoria conversacional dentro de una misma ejecución.
- La memoria todavía no persiste al cerrar el programa.
- Si una llamada falla o la respuesta no contiene texto válido, se elimina la última pregunta mediante `pop()` para mantener consistente el historial.
- Las entradas vacías y el comando `salir` no modifican `messages`.

### Pruebas realizadas

- Entrada formada solo por espacios seguida de `salir`: mostró el aviso, no llamó a Groq y finalizó correctamente.
- Comando `SALIR`: se reconoció en mayúsculas, no llamó a Groq y mostró `Hasta luego.`.
- Memoria conversacional: en una sesión con exactamente dos llamadas, el usuario indicó que se llamaba JP y la segunda respuesta fue `JP`.
- Estructura del historial: tras dos intercambios correctos queda conceptualmente como `system`, `user`, `assistant`, `user`, `assistant`.
- Protección ante fallos: con un cliente local simulado se comprobó que una excepción y una respuesta vacía eliminan únicamente la pregunta fallida y conservan intacto el historial anterior.
- No se produjeron errores reales del programa durante estas pruebas.

## 2026-08-21 — Persistencia del historial en JSON

- Se añadió persistencia en JSON al finalizar una conversación con el comando `salir`.
- La memoria durante la ejecución continúa utilizando la lista `messages` en RAM.
- El JSON funciona como historial persistente en disco después de cerrar el programa.
- Los archivos se guardan en `conversaciones/` con fecha y hora en el nombre; si ya existe el nombre, se añade un sufijo para evitar sobrescrituras.
- Se utilizan únicamente `json`, `datetime` y `pathlib` de la biblioteca estándar.
- El JSON se genera con `indent=2` y `ensure_ascii=False` para que resulte legible y conserve correctamente tildes y otros caracteres Unicode.
- No se guardan credenciales, la clave de Groq ni el contenido de `.env`.
- Una sesión sin preguntas no genera ningún archivo de conversación.
- Si el guardado falla, se muestra un mensaje genérico y el programa continúa su cierre sin mostrar un traceback.
- Se mantiene separado el concepto de memoria temporal en RAM y persistencia del historial en disco.

### Pruebas realizadas

- Salida sin preguntas: no creó ningún JSON y mostró que no había conversación que guardar.
- Conversación con memoria: realizó exactamente dos llamadas a Groq, recordó el nombre JP y guardó un archivo con los roles `system`, `user`, `assistant`, `user`, `assistant`.
- Validación del archivo: el JSON contiene fecha y modelo, es sintácticamente válido, conserva caracteres como `¿`, `¡` y tildes de forma legible, y no contiene credenciales.
- Protección contra sobrescrituras: dos guardados locales en el mismo segundo generaron nombres diferentes y conservaron intacto el primer archivo.
- No se produjeron errores reales del programa durante estas pruebas.

### Privacidad de los historiales

- Los historiales JSON se generan localmente y no se versionan por privacidad; la carpeta `conversaciones/` se conserva en el repositorio mediante `.gitkeep`.

### Legibilidad del código

- Se añadieron comentarios para facilitar la comprensión del código.
- Los comentarios se centran en decisiones de diseño, flujo y manejo de errores.
- Se evitó comentar instrucciones evidentes para mantener el código limpio.

## 2026-08-21 — Experimentación con system prompts

Se comparó el mismo modelo, `openai/gpt-oss-120b`, con la pregunta común `Explícame qué es una API.` y tres mensajes system independientes:

- Prompt A: `Eres un asistente útil, claro y conciso.`
- Prompt B: `Eres un profesor de programación paciente. Explica los conceptos paso a paso con ejemplos sencillos.`
- Prompt C: `Eres un asistente técnico experto. Responde de forma breve, precisa y profesional.`

### Diferencias observadas

- Prompt A: utilizó un tono general y claro, pero produjo una respuesta extensa. Incluyó definición, funcionamiento, usos, tipos de API, tablas, un ejemplo y buenas prácticas.
- Prompt B: generó la respuesta más larga y didáctica. Explicó paso a paso, empleó la analogía de un restaurante e incluyó tablas, ejemplos con cURL, JavaScript y Python, además de un ejercicio práctico.
- Prompt C: produjo la respuesta más breve, precisa y técnica. Resumió definición, tipos y ventajas mediante una estructura profesional, sin desarrollar ejemplos de código.

### Conclusión

- El mensaje system condiciona de forma visible el tono, la longitud, el detalle, la claridad, el uso de ejemplos y la orientación didáctica o técnica, incluso manteniendo el mismo modelo y la misma pregunta.
- El Prompt C parece el más adecuado para el asistente del Nivel Intermedio porque ofrece respuestas técnicas, profesionales y concisas, apropiadas para una interacción ágil en terminal. El Prompt B sería preferible en un contexto específicamente educativo.
- No se produjeron errores reales durante las tres llamadas.

## 2026-08-21 — Nivel Intermedio completado

El Nivel Intermedio queda formalmente cerrado después de implementar y comprobar:

- Memoria conversacional mediante una lista `messages` con los roles `system`, `user` y `assistant`, conservando el contexto durante una misma ejecución.
- Manejo consistente del historial: `messages.pop()` elimina la pregunta actual si falla una consulta y las respuestas vacías se consideran errores.
- Persistencia del historial en archivos JSON con fecha y hora, prevención de sobrescrituras y formato legible mediante `ensure_ascii=False` e `indent=2`.
- Privacidad de las conversaciones mediante `.gitignore`, conservación de `conversaciones/` mediante `.gitkeep` y ausencia de credenciales en Git.
- Experimentación controlada con tres system prompts y comparación de tono, longitud, detalle y orientación.
- Elección razonada del Prompt C para un asistente técnico por su estilo breve, preciso y profesional.
- Comentarios en el código centrados en decisiones importantes, flujo y manejo de errores.
- Ejecución correcta de las pruebas funcionales, de memoria, persistencia, privacidad y system prompts.

### Diferencia respecto al Nivel Básico

- Nivel Básico: cada petición contiene únicamente la pregunta actual.
- Nivel Intermedio: cada petición envía el historial acumulado de `messages`.

### Conceptos aprendidos

- Memoria en RAM.
- Persistencia en disco.
- System prompts.
- Roles de conversación.
- Manejo consistente del historial.
- JSON.
- Privacidad de datos.
- Pruebas controladas.

### Estado

- Nivel Básico: **COMPLETADO**
- Nivel Intermedio: **COMPLETADO**
- Nivel Avanzado: **PENDIENTE**
- Nivel Experto: **PENDIENTE**

## 2026-08-22 — Primer tool calling real del Nivel Avanzado

Se creó `src/nivel_avanzado.py` sin modificar los niveles anteriores y se implementó una única herramienta local segura llamada `calculate`. El modelo no ejecuta Python directamente: solicita el uso de la herramienta y Python valida la petición antes de decidir si la ejecuta. No se utiliza `eval()` y las operaciones permitidas forman una lista cerrada: `add`, `subtract`, `multiply` y `divide`.

Los argumentos recibidos del modelo se interpretan como JSON y se validan antes de utilizarlos, incluyendo su estructura, tipos, nombres, operación y valores finitos. Cuando la solicitud es válida, el resultado local se devuelve al modelo mediante `role="tool"`, conservando el `tool_call_id`, y se realiza una segunda llamada para que el modelo redacte la respuesta final.

### Pruebas reales

- Prueba matemática, `27 × 14`: el modelo solicitó `calculate` con `operation=multiply`, Python obtuvo localmente `378` y la respuesta final fue correcta.
- Pregunta normal, `¿Qué es Python?`: el modelo no solicitó herramientas y respondió directamente.
- División entre cero, `10 / 0`: el modelo respondió directamente que la operación es indefinida y no ejecutó `calculate`. La protección local frente a la división entre cero ya estaba validada mediante pruebas locales.

### Seguridad

- La única herramienta permitida está declarada explícitamente y su nombre se valida antes de ejecutarla.
- Los argumentos y sus tipos se validan, y la operación debe pertenecer al `enum` permitido.
- No se utiliza `eval()` ni se permite la ejecución arbitraria de código.
- Los errores se controlan sin mostrar tracebacks al usuario.

### Resultado

No se produjeron errores reales ni incompatibilidades con Groq. Las pruebas finalizaron correctamente.

## 2026-08-24 — Selección entre múltiples herramientas

Se añadió una segunda herramienta local llamada `get_task_info` y se creó `data/tareas.json` con datos ficticios y no sensibles. La nueva herramienta permite consultar la prioridad, la duración y la categoría de una tarea, mientras que `calculate` se mantiene como herramienta para operaciones matemáticas básicas.

El modelo recibe ambas tools y decide cuál utilizar según la pregunta. Antes de ejecutar una función, Python valida explícitamente el nombre de la herramienta y sus argumentos. El despacho se mantiene cerrado y explícito para impedir la ejecución arbitraria de código.

### Pruebas

- Calculadora, `18 × 7`: el modelo seleccionó `calculate` con `operation=multiply`, se obtuvo localmente `126` y la respuesta final fue correcta.
- Consulta de tareas, duración y prioridad de `estudiar Python`: el modelo seleccionó `get_task_info` y respondió con los datos reales del JSON, `90` minutos y prioridad `alta`.
- Pregunta general, qué es una API: el modelo no solicitó ninguna herramienta y respondió directamente.

### Casos límite

- Una herramienta desconocida se rechaza.
- Un `task_name` ausente, vacío o inválido se rechaza antes de ejecutar la función.
- Una tarea inexistente se maneja mediante un resultado estructurado.
- Un fichero con JSON inválido se controla sin mostrar traceback.
- Los tipos incorrectos recibidos por `calculate` se rechazan.
- No se utilizan `eval()`, `exec()` ni mecanismos de ejecución arbitraria.

### Resultado

Todas las pruebas pasaron, sin errores reales ni incompatibilidades con Groq. Esta versión todavía admite una única solicitud de herramienta por respuesta y no incorpora un bucle agentic de múltiples pasos.

## 2026-08-24 — Bucle agentic multipaso

Se sustituyó el flujo limitado a una única herramienta por un bucle agentic. En cada ronda, el modelo puede devolver una o varias `tool_calls`; Python valida todas las solicitudes antes de ejecutar la primera y después ejecuta las herramientas en el orden solicitado por el modelo.

Cada resultado se añade a la conversación con `role="tool"` y conserva su `tool_call_id`. El agente vuelve a consultar al modelo y repite el ciclo hasta obtener una respuesta final en lenguaje natural. Se añadió `MAX_AGENT_STEPS = 5` como límite configurable para evitar bucles infinitos.

### Prueba multipaso

Pregunta: `¿Cuánto dura estudiar Python y cuántos minutos serían si hiciera esa tarea 3 veces?`

Flujo observado:

`get_task_info` → `90 minutos` → `calculate` → `90 × 3` → `270 minutos` → respuesta final.

El orden de las herramientas fue decidido por el modelo y no se codificó manualmente.

### Otras pruebas

- Uso exclusivo de `calculate`.
- Uso exclusivo de `get_task_info`.
- Respuesta directa sin herramientas.
- Rechazo de una herramienta desconocida.
- Rechazo de argumentos inválidos.
- Control de la división entre cero.
- Manejo estructurado de una tarea inexistente.
- Control de una respuesta vacía.
- Activación local del límite `MAX_AGENT_STEPS` mediante un cliente simulado.

### Resultado

Todas las pruebas pasaron, sin errores reales ni incompatibilidades con Groq. El agente puede encadenar herramientas correctamente hasta construir una respuesta final.

## 2026-08-24 — Nivel Avanzado completado

El Nivel Avanzado queda formalmente cerrado después de implementar y comprobar:

- Tool use / function calling y descripción de herramientas mediante JSON Schema.
- Las herramientas `calculate` y `get_task_info`, incluida la selección correcta entre ambas y la respuesta directa cuando no se necesita ninguna.
- Validación explícita del nombre y de los argumentos antes de ejecutar Python, con rechazo de JSON inválido, tipos incorrectos y herramientas desconocidas, además del control de la división entre cero.
- Despacho cerrado y seguro, sin `eval()`, `exec()`, `getattr()` dinámico ni mecanismos de ejecución arbitraria.
- Devolución de resultados mediante `role="tool"` y conservación de cada `tool_call_id`.
- Bucle agentic multipaso capaz de procesar varias `tool_calls`, validarlas todas antes de ejecutar la primera y ejecutarlas en el orden solicitado.
- Límite de seguridad configurable mediante `MAX_AGENT_STEPS = 5`.
- Encadenado real `get_task_info` → `calculate` → respuesta final.
- Pruebas locales y reales completadas, incluidas las situaciones límite, sin errores reales ni incompatibilidades con Groq.

### Diferencia respecto al Nivel Intermedio

- Nivel Intermedio: el modelo conversa con memoria y conserva el contexto durante una misma ejecución.
- Nivel Avanzado: el modelo, además, puede solicitar herramientas, recibir sus resultados y continuar el razonamiento hasta producir una respuesta final.

### Conceptos aprendidos

- Tool use / function calling.
- JSON Schema.
- Validación de entradas generadas por el modelo.
- Despacho seguro de herramientas.
- `tool_call_id` y `role="tool"`.
- Bucle agentic.
- Encadenado de herramientas.
- Límites de seguridad.
- Pruebas de casos límite.

### Estado

- Nivel Básico: **COMPLETADO**
- Nivel Intermedio: **COMPLETADO**
- Nivel Avanzado: **COMPLETADO**
- Nivel Experto: **PENDIENTE**

## 2026-08-24 — Arquitectura del Nivel Experto: LangGraph

Se evaluó continuar con el agent loop manual o utilizar LangGraph. La versión manual ya funciona y permanecerá disponible en `src/nivel_avanzado.py`.

Se decide utilizar LangGraph en el Nivel Experto para estudiar una arquitectura basada en estado, nodos y transiciones. Se mantendrá inicialmente el SDK oficial de Groq, sin migrar todavía a ChatGroq ni LangChain. También se conservarán `calculate`, `get_task_info` y todas sus validaciones.

LangGraph sustituirá principalmente el bucle manual, las decisiones de ruta y el control de transiciones. La seguridad y la validación de las tools seguirán siendo responsabilidad de nuestro código Python. Esta elección permitirá comparar la arquitectura manual con una basada en un framework, sin considerar que una sea universalmente mejor que la otra.

### Alternativa considerada

Continuar completamente "a mano".

Ventajas:

- Menor número de dependencias.
- Control explícito.
- Código ya probado.

Inconvenientes:

- `run_agent` concentra demasiadas responsabilidades.
- Escalar las rutas y los estados complicaría progresivamente la función.

### Razón de la elección

LangGraph se adopta porque ahora ya existe suficiente comprensión del flujo manual para evaluar con criterio qué abstracción aporta el framework.

## 2026-08-25 — Aplicación ejecutable del Nivel Experto

Se completó `src/experto/main.py` como punto de entrada funcional del asistente. El programa ya puede ejecutarse desde la raíz del proyecto mediante:

```powershell
.venv\Scripts\python.exe -m src.experto.main
```

`main.py` se limita a la interfaz de terminal, la carga de configuración y la ejecución del grafo. La llamada y normalización del modelo, las herramientas y sus validaciones, y la construcción de LangGraph permanecen separadas en sus respectivos módulos.

Se resolvió la incidencia real de Unicode observada en Windows configurando `stdout` como UTF-8 cuando la salida permite `reconfigure()`. La solución es defensiva: comprueba primero que ese método esté disponible y permite que la aplicación continúe en entornos donde no exista o no se pueda utilizar.

### Pruebas reales

**Prueba directa:** se preguntó qué es un set de Python. El agente realizó una llamada a Groq, no solicitó herramientas y devolvió una respuesta correcta.

**Prueba con `calculate`:** se solicitó calcular `16 × 7`. El modelo pidió `calculate`, la herramienta devolvió `112` y el agente redactó correctamente la respuesta final.

**Prueba de tarea:** se consultó la duración de `estudiar Python` y el tiempo necesario para realizarla dos veces. El modelo solicitó `get_task_info`, obtuvo una duración de `90 minutos` y respondió correctamente que dos repeticiones requieren `180 minutos`.

En la tercera prueba, el modelo **no solicitó `calculate`**. Después de recibir los 90 minutos mediante `get_task_info`, realizó por sí mismo la multiplicación por dos. Esto no se considera un error: el modelo decide cuándo necesita una herramienta, la respuesta final fue correcta y el flujo del grafo terminó correctamente.

El `AssertionError` mostrado después de esa ejecución pertenecía únicamente al arnés temporal de prueba, que esperaba de forma estricta la secuencia `get_task_info` → `calculate`. No fue un error de `main.py` ni del `StateGraph`.

### Flujo completo

`main` → cliente Groq → `StateGraph` → nodo `agent` → nodo `tools` cuando procede → nodo `agent` → `END` → respuesta final.

### Resultado

- Aplicación ejecutable funcional.
- Salida UTF-8 validada, incluido el carácter Unicode `U+202F` que había provocado la incidencia anterior.
- Sin errores reales del programa.
- Sin exposición de credenciales ni contenido de `.env`.

## 2026-08-26 — Nivel Experto completado

El Nivel Experto queda formalmente completado después de implementar y comprobar:

- Adopción razonada de LangGraph para sustituir la orquestación manual, manteniendo el SDK oficial de Groq como adaptador del modelo.
- Arquitectura modular en `src/experto/`, con responsabilidades separadas entre configuración, estado, herramientas, modelo, grafo e interfaz.
- Estado compartido mediante `AgentState` y construcción de un `StateGraph` con los nodos `agent` y `tools`.
- Routing explícito mediante conditional edges para ejecutar herramientas o finalizar según el estado.
- Ejecución multipaso, conservación de cada `tool_call_id` y devolución de resultados con `role="tool"`.
- Validación completa de todas las solicitudes de una ronda antes de ejecutar la primera herramienta.
- Despacho seguro y cerrado para `calculate` y `get_task_info`.
- Límite configurable `MAX_AGENT_STEPS = 5` para impedir ciclos indefinidos.
- CLI funcional, configuración defensiva de UTF-8 y manejo controlado de errores.
- Logging técnico y seguro, sin conversaciones completas ni credenciales.
- Suite automática con pytest formada por 64 tests.
- Evaluación funcional reproducible de seis casos con métricas explícitas.
- README completo con arquitectura, instalación, configuración, ejecución, pruebas, evaluación, seguridad y limitaciones.
- Medidas de privacidad para credenciales, conversaciones, logs y resultados variables de evaluación.

### Comparación con el Nivel Avanzado

- Nivel Avanzado: `run_agent()` concentra la orquestación mediante un bucle `for`, condiciones `if/else`, gestión manual de `tool_calls` y un estado representado principalmente por `messages`.
- Nivel Experto: `StateGraph` utiliza `AgentState`, nodos separados, conditional edges y routing explícito, con responsabilidades desacopladas entre módulos.

LangGraph no se considera universalmente superior. Construir primero el agent loop manual permitió comprender el estado, las llamadas al modelo, el ciclo de herramientas y las condiciones de finalización; con esa base fue posible evaluar con criterio qué problema de orquestación resuelve después el framework.

### Evaluación del agente

Resultado histórico conservado:

```text
Total: 6
PASS: 5
FAIL: 1
Éxito: 83.3%
```

El único `FAIL` histórico corresponde al caso de una tarea inexistente. El comportamiento real del agente fue correcto: comunicó que no había encontrado la tarea y no inventó una prioridad. El fallo automático se debió a una limitación del validador textual, que no contemplaba la expresión `no he encontrado`.

El resultado histórico no se modifica retrospectivamente y permanece en `5/6`, `83.3%`.

### Pruebas automáticas

La suite actual obtiene:

```text
64 passed
```

Las pruebas cubren conceptualmente las herramientas, la validación de argumentos, la normalización de respuestas, el routing, la conservación de `tool_call_id`, varias herramientas en una ronda, el manejo de errores y el límite de pasos. Superar la suite aumenta la confianza en esas partes, pero no garantiza la ausencia absoluta de errores.

### Seguridad y privacidad

- `GROQ_API_KEY` permanece fuera del código y `.env` está ignorado por Git.
- Las herramientas se describen mediante JSON Schema y sus nombres y argumentos se validan estrictamente.
- Solo se permiten herramientas declaradas explícitamente mediante un despacho cerrado.
- No se utilizan `eval()`, `exec()`, `getattr()` dinámico ni importaciones dinámicas.
- El número de llamadas al modelo queda limitado mediante `MAX_AGENT_STEPS`.
- El logging no almacena preguntas ni respuestas completas; los archivos de log son locales y están ignorados.
- Los resultados variables de evaluación se mantienen locales e ignorados.
- Los errores externos se transforman en errores controlados sin mostrar tracebacks ni credenciales al usuario.

### Conceptos aprendidos

- Arquitectura de agentes.
- LangGraph y `StateGraph`.
- Estado compartido.
- Nodos, edges, conditional edges y routing.
- Tool/function calling y JSON Schema.
- Validación segura y despacho cerrado de herramientas.
- Agent loops y límites de ejecución.
- Logging.
- Pytest.
- Evaluación funcional.
- Separación de responsabilidades.
- Privacidad de datos.
- Comparación entre framework e implementación manual.

### Limitaciones actuales

- Solo existen dos herramientas locales.
- El modelo generativo puede variar sus respuestas entre ejecuciones.
- No existe un checkpointer de LangGraph.
- No existe memoria persistente del Nivel Experto entre ejecuciones.
- Cada ejecución de la CLI comienza con una pregunta nueva.
- Los validadores textuales pueden producir falsos negativos; la evaluación histórica contiene un ejemplo de esta limitación.

Estas limitaciones describen el alcance actual y no se consideran fallos del proyecto.

## Reflexión final del reto

Se completó la progresión **Básico → Intermedio → Avanzado → Experto**. El Nivel Básico permitió comprender la comunicación mínima entre Python y un LLM. El Nivel Intermedio añadió memoria, contexto, roles y persistencia. El Nivel Avanzado introdujo tool/function calling y permitió construir de forma explícita un agent loop multipaso. El Nivel Experto reorganizó ese flujo con LangGraph, separó responsabilidades y añadió prácticas de proyecto como logging, tests, evaluación y documentación de uso.

La conclusión técnica respaldada por la evolución del repositorio es que implementar primero el flujo manual permitió identificar con claridad qué abstrae posteriormente LangGraph. Utilizar un framework sin comprender el estado, los `tool_calls`, los resultados `role="tool"`, el routing y la finalización habría aportado menos capacidad para evaluar sus ventajas e inconvenientes.

El resultado final no se presenta como un producto universalmente terminado, sino como una base técnica extensible, probada y documentada. Las preguntas subjetivas del documento sobre preferencias personales o prioridades futuras del alumno no pueden responderse objetivamente a partir del repositorio; por ello no se atribuyen opiniones personales no documentadas.

### Estado

- Nivel Básico: **COMPLETADO**
- Nivel Intermedio: **COMPLETADO**
- Nivel Avanzado: **COMPLETADO**
- Nivel Experto: **COMPLETADO**
