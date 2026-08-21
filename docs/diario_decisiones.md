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
