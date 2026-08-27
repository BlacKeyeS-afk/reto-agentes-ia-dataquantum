# Manual de ejecución — Reto Python + Agentes de IA DataQuantum

Esta guía resume los pasos necesarios para instalar, configurar y ejecutar el agente desde Windows con PowerShell.

## 1. Requisitos previos

Antes de comenzar necesitas:

- Python 3.13.x.
- Git.
- Conexión a Internet para utilizar Groq.
- Una API key válida de Groq.

Nunca copies una API key real dentro del código ni la añadas al repositorio.

## 2. Clonar el repositorio

Abre PowerShell y ejecuta:

```powershell
git clone https://github.com/BlacKeyeS-afk/reto-agentes-ia-dataquantum.git
cd reto-agentes-ia-dataquantum
```

El repositorio es privado. La cuenta de GitHub utilizada para clonarlo debe tener acceso autorizado y estar autenticada mediante el método correspondiente, por ejemplo GitHub CLI o el gestor de credenciales de Git.

## 3. Crear el entorno virtual

Desde la raíz del proyecto:

```powershell
python -m venv .venv
```

## 4. Activar el entorno virtual

En PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea temporalmente `Activate.ps1` por su política de ejecución, no es necesario desactivar permanentemente ninguna protección. Puedes ejecutar directamente el Python del entorno virtual en todos los comandos:

```powershell
.\.venv\Scripts\python.exe
```

## 5. Instalar las dependencias

Con el entorno activado:

```powershell
python -m pip install -r requirements.txt
```

Si no has activado el entorno, utiliza:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Las dependencias principales actuales son:

- `groq==1.6.0`
- `langgraph==1.2.11`
- `pytest==9.1.1`
- `python-dotenv==1.2.3`

## 6. Configurar Groq

Crea un archivo llamado `.env` en la raíz del proyecto con este contenido de ejemplo:

```dotenv
GROQ_API_KEY=tu_clave_de_groq
```

Sustituye únicamente el valor de ejemplo en tu copia local. El archivo `.env` está protegido por `.gitignore` y no debe añadirse a Git.

## 7. Comprobar la estructura

Desde la raíz deben existir, como mínimo:

```text
README.md
requirements.txt
.env
src/
data/
tests/
evals/
```

El archivo `.env` se crea localmente y no forma parte del repositorio clonado.

## 8. Ejecutar el agente experto

El comando recomendado es:

```powershell
.\.venv\Scripts\python.exe -m src.experto.main
```

La salida inicial esperada es:

```text
=== Asistente IA - Nivel Experto (LangGraph) ===
Escribe una pregunta:
```

Preguntas de ejemplo:

- `¿Cuánto es 16 multiplicado por 7?`
- `¿Qué prioridad tiene estudiar Python?`
- `¿Cuánto dura estudiar Python y cuántos minutos serían si hiciera esa tarea 3 veces?`

Estas preguntas pueden provocar llamadas reales a Groq al ejecutar la aplicación.

## 9. Cómo cerrar

Esta versión del Nivel Experto procesa una sola pregunta por ejecución. El programa termina después de mostrar la respuesta final o un error controlado.

Para realizar otra pregunta, vuelve a ejecutar:

```powershell
.\.venv\Scripts\python.exe -m src.experto.main
```

## 10. Herramientas disponibles

El agente dispone de dos herramientas locales:

### `calculate`

Realiza operaciones matemáticas básicas:

- suma;
- resta;
- multiplicación;
- división.

### `get_task_info`

Consulta las tareas locales almacenadas en `data/tareas.json`, incluyendo información como prioridad, duración y categoría.

El modelo decide cuándo solicitar una herramienta. Python valida el nombre y los argumentos y ejecuta únicamente las herramientas permitidas.

## 11. Ejecutar los tests

Ejecuta:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

El resultado actual esperado es:

```text
64 passed
```

El tiempo exacto de ejecución puede variar según el equipo.

## 12. Evaluación funcional

La evaluación funcional se ejecuta con:

```powershell
.\.venv\Scripts\python.exe -m evals.evaluate_agent
```

Este comando **sí realiza llamadas reales a Groq** y puede consumir cuota. No es necesario ejecutarlo para comprobar simplemente que la aplicación arranca o que los tests pasan.

El resultado histórico documentado es:

```text
5/6
83.3%
```

## 13. Logs

La aplicación intenta generar localmente:

```text
logs/app.log
```

- Está ignorado por Git.
- Contiene eventos técnicos para facilitar el diagnóstico.
- No debería contener API keys ni conversaciones completas.
- Si el archivo no puede crearse, la aplicación continúa utilizando la consola.

## 14. Datos locales

El archivo:

```text
data/tareas.json
```

contiene los datos utilizados por `get_task_info`. No es necesario modificarlo para ejecutar los ejemplos existentes.

## 15. Errores frecuentes

| Mensaje o problema | Qué comprobar |
| --- | --- |
| `GROQ_API_KEY no está configurada` | Revisa que `.env` exista en la raíz y contenga `GROQ_API_KEY=tu_clave_de_groq` con tu valor local. |
| `No module named ...` | Activa `.venv` o instala `requirements.txt` utilizando el Python del entorno virtual. |
| `python` no se reconoce | Comprueba la instalación de Python y que esté disponible en `PATH`. |
| PowerShell no permite `Activate.ps1` | Usa directamente `.\.venv\Scripts\python.exe` o revisa la política de ejecución aplicable sin desactivar permanentemente la seguridad. |
| Error de conexión con Groq | Revisa la conexión a Internet, la API key y el estado o cuota del servicio. |
| Tarea no encontrada | Comprueba los nombres disponibles en `data/tareas.json`. |

## 16. Comandos rápidos

```powershell
# Preparación inicial
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Ejecutar agente
.\.venv\Scripts\python.exe -m src.experto.main

# Tests
.\.venv\Scripts\python.exe -m pytest -q

# Evaluación real (consume Groq)
.\.venv\Scripts\python.exe -m evals.evaluate_agent
```

## 17. Documentación adicional

- `README.md`: documentación completa del proyecto.
- `docs/diario_decisiones.md`: decisiones técnicas y evolución del reto.
- `docs/pdfs/`: documentación visual de los cuatro niveles.
