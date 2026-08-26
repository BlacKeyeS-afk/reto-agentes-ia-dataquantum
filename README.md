# Reto Python + Agentes de IA — DataQuantum

## Descripción

Este repositorio documenta un reto práctico de Python sobre agentes de IA organizado como una progresión por niveles:

**Básico → Intermedio → Avanzado → Experto**

El proyecto evoluciona desde una llamada básica a un modelo de lenguaje hasta un asistente inteligente de tareas con herramientas, validaciones seguras y un flujo multipaso orquestado con LangGraph.

## Estado del reto

- Nivel Básico: **COMPLETADO**
- Nivel Intermedio: **COMPLETADO**
- Nivel Avanzado: **COMPLETADO**
- Nivel Experto: **COMPLETADO**

## Evolución por niveles

### Básico

- Conexión con Groq mediante su SDK oficial.
- Preguntas introducidas desde la terminal.
- Bucle interactivo hasta escribir `salir`.
- Validación de entradas y manejo de errores controlado.

### Intermedio

- Memoria conversacional durante una misma ejecución.
- Roles `system`, `user` y `assistant`.
- Experimentación controlada con distintos system prompts.
- Persistencia del historial en JSON.
- Privacidad de los historiales generados.
- Comparación de tono, longitud, detalle y orientación de los prompts.

### Avanzado

- Tool use / function calling.
- Herramientas locales `calculate` y `get_task_info`.
- Descripción de herramientas mediante JSON Schema.
- Validación segura del nombre, los argumentos y los tipos.
- Selección y procesamiento de múltiples tools.
- Agent loop multipaso implementado manualmente.
- Límite de seguridad `MAX_AGENT_STEPS`.

### Experto

- Arquitectura modular y responsabilidades separadas.
- Orquestación con LangGraph y `StateGraph`.
- Nodos `agent` y `tools` con routing condicional.
- Aplicación de terminal ejecutable.
- Logging básico y seguro.
- 64 tests automáticos con pytest.
- Evaluación funcional reproducible de seis casos.

## Arquitectura del Nivel Experto

```text
src/experto/
├── __init__.py
├── agent.py
├── config.py
├── graph.py
├── main.py
├── state.py
└── tools.py

tests/
├── __init__.py
├── test_agent.py
├── test_graph.py
└── test_tools.py

evals/
├── __init__.py
├── evaluate_agent.py
└── results/
    └── .gitkeep

data/
└── tareas.json

logs/
└── .gitkeep
```

Responsabilidades principales:

- `config.py`: configuración no sensible, como modelo, rutas, prompt, logging y límite de pasos.
- `state.py`: definición del estado compartido que circula por el grafo.
- `tools.py`: herramientas locales, JSON Schemas, validación de argumentos y despacho seguro.
- `agent.py`: creación del cliente Groq, llamada al modelo y normalización de respuestas.
- `graph.py`: nodos, transiciones, routing condicional y construcción del `StateGraph`.
- `main.py`: configuración de terminal, carga segura del entorno, interfaz de usuario y ejecución del grafo.

## Arquitectura del agente

```text
Usuario
  ↓
main.py
  ↓
StateGraph
  ↓
agent
  ↓
¿tool?
  ├─ no → END
  └─ sí
       ↓
      tools
       ↓
      agent
       ↓
     repetir
```

LangGraph gestiona el estado y las transiciones entre nodos. Groq continúa siendo el proveedor del modelo, mientras que el código Python conserva el control sobre la validación y ejecución de herramientas. El modelo no ejecuta Python directamente: solicita una herramienta y Python decide, mediante un despacho explícito, si la petición es válida y puede ejecutarse.

## Modelo

- Modelo: `openai/gpt-oss-120b`
- Proveedor: Groq
- Integración: SDK oficial `groq`

## Herramientas

### `calculate`

Operaciones permitidas:

- `add`
- `subtract`
- `multiply`
- `divide`

La implementación no utiliza `eval()`, valida los tipos y los números finitos, limita las operaciones a una lista cerrada y controla la división entre cero.

### `get_task_info`

Consulta exclusivamente los datos locales de `data/tareas.json` y devuelve, cuando la tarea existe:

- nombre;
- prioridad;
- duración en minutos;
- categoría.

También maneja de forma controlada tareas inexistentes, ficheros ausentes, JSON inválido y estructuras de datos incorrectas.

## Seguridad

- `.env` está ignorado por Git.
- La API key se obtiene desde el entorno y permanece fuera del código.
- Las herramientas permitidas se identifican explícitamente.
- Los parámetros se describen mediante JSON Schema.
- Los argumentos del modelo se validan antes de ejecutar funciones Python.
- No se utiliza `eval()`, `exec()`, `getattr()` dinámico ni importación dinámica.
- `MAX_AGENT_STEPS = 5` evita bucles indefinidos.
- Los logs no incluyen conversaciones completas, credenciales ni argumentos JSON completos.
- Los historiales y resultados variables permanecen locales e ignorados cuando corresponde.

## Requisitos

El proyecto se ha desarrollado y validado con **Python 3.13.x**. La versión utilizada durante el reto es Python 3.13.15.

Las dependencias directas y sus versiones exactas están fijadas en `requirements.txt`:

```text
groq==1.6.0
langgraph==1.2.11
pytest==9.1.1
python-dotenv==1.2.3
```

## Instalación

Desde Windows PowerShell, situado en la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Si `.venv` ya existe y usa la versión correcta de Python, no es necesario recrearlo; basta con activarlo e instalar o comprobar las dependencias.

## Configuración

Crea un archivo `.env` en la raíz del proyecto:

```dotenv
GROQ_API_KEY=tu_clave_de_groq
```

No incluyas una clave real en archivos versionados. `.env` está ignorado por Git y `.env.example` sirve como referencia segura.

## Ejecución

Desde la raíz del repositorio:

```powershell
.\.venv\Scripts\python.exe -m src.experto.main
```

Ejemplos conceptuales de preguntas:

```text
¿Cuánto es 16 multiplicado por 7?
¿Qué prioridad tiene estudiar Python?
```

Cada ejecución de la CLI comienza con una pregunta nueva. El grafo puede realizar varias llamadas internas al modelo y a herramientas antes de producir la respuesta final.

## Tests

Con el entorno virtual activado:

```powershell
pytest -q
```

También puede ejecutarse de forma explícita con el Python del entorno:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Resultado actual documentado:

```text
64 passed
```

La suite comprueba herramientas, validaciones, routing y adaptación de respuestas mediante objetos simulados. Este resultado aumenta la confianza en esas partes, pero no garantiza la ausencia absoluta de errores.

## Evaluación funcional

La evaluación utiliza seis preguntas fijas y ejecuta cada caso una sola vez, sin reintentos automáticos:

```powershell
.\.venv\Scripts\python.exe -m evals.evaluate_agent
```

Resultado histórico conservado:

```text
Total: 6
PASS: 5
FAIL: 1
Éxito: 83.3%
```

El único `FAIL` histórico fue un falso negativo del validador en el caso de una tarea inexistente. El agente respondió correctamente que no había encontrado la tarea y no inventó una prioridad, pero el criterio automático no contemplaba la expresión «no he encontrado». El resultado histórico se mantiene en `83.3%`; no se ha convertido retrospectivamente en `100%`.

Los resultados se guardan localmente en `evals/results/latest.json`, que está ignorado por Git porque las respuestas generativas pueden variar entre ejecuciones.

## Logging

La aplicación intenta registrar eventos técnicos en `logs/app.log`:

- se guarda únicamente de forma local;
- está ignorado por Git;
- utiliza UTF-8;
- se abre en modo append para conservar eventos anteriores;
- registra estados técnicos, rutas y conteos seguros;
- no registra preguntas o respuestas completas, API keys, historial ni argumentos JSON completos.

Si el archivo de log no puede crearse, la aplicación continúa utilizando la salida a consola y mantiene su manejo de errores habitual.

## Comparación: arquitectura manual y LangGraph

En el Nivel Avanzado, `run_agent()` controla manualmente el flujo mediante un bucle `for`, condiciones `if/else`, llamadas al modelo, validación de tool calls, ejecución y finalización.

En el Nivel Experto, esas transiciones se representan mediante un `StateGraph`, nodos, estado compartido y conditional edges. Las herramientas y sus validaciones continúan siendo código Python explícito.

LangGraph no se eligió porque sea universalmente mejor. Se adoptó como decisión de ingeniería después de comprender e implementar primero el flujo manual, con el objetivo de comparar ambas arquitecturas y estudiar qué abstracciones aporta un framework de orquestación.

## Estructura Git y progreso

El historial utiliza commits pequeños para documentar hitos como:

- preparación inicial del repositorio;
- asistente del Nivel Básico;
- memoria conversacional;
- tool/function calling;
- agent loop multipaso;
- migración de la orquestación a LangGraph;
- logging seguro;
- tests automáticos;
- evaluación funcional.

## Privacidad

Los siguientes archivos generados o sensibles no se versionan:

```text
.env
conversaciones/*.json
logs/*.log
evals/results/*.json
```

Las carpetas necesarias se conservan mediante `.gitkeep` cuando procede.

## Limitaciones actuales

- Las respuestas de un modelo generativo pueden variar entre ejecuciones.
- El agente dispone actualmente de dos herramientas locales.
- No existe un checkpointer ni memoria persistente de LangGraph entre ejecuciones.
- Cada ejecución de la CLI comienza con una pregunta nueva.
- Los validadores basados en coincidencias de texto pueden producir falsos negativos.
- La evaluación actual es pequeña y no representa todos los escenarios posibles.

Estas limitaciones describen el alcance actual del proyecto y no implican que el funcionamiento existente sea incorrecto.

## Próximas mejoras

Ideas para futuras iteraciones, todavía no implementadas:

- mejorar los evaluadores con criterios semánticos;
- ampliar y diversificar los casos de evaluación;
- añadir un checkpointer o memoria persistente cuando exista una necesidad clara;
- incorporar más herramientas justificadas por casos de uso reales;
- medir la cobertura de tests;
- ampliar la comparación entre la implementación manual y LangGraph.

## Diario de decisiones

`docs/diario_decisiones.md` contiene el razonamiento técnico, las alternativas consideradas, las incidencias relevantes y la evolución del proyecto por niveles.

## Licencia y uso

El repositorio no incluye actualmente un archivo `LICENSE`; por tanto, no se declara una licencia de uso específica.
