import json
import os
from math import isfinite
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import Groq


MODEL_NAME = "openai/gpt-oss-120b"
MAX_AGENT_STEPS = 5
CALCULATOR_TOOL_NAME = "calculate"
TASK_INFO_TOOL_NAME = "get_task_info"
ALLOWED_OPERATIONS = ("add", "subtract", "multiply", "divide")
TASKS_FILE = Path(__file__).resolve().parent.parent / "data" / "tareas.json"
CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": CALCULATOR_TOOL_NAME,
        "description": "Realiza operaciones matemáticas básicas.",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": list(ALLOWED_OPERATIONS),
                    "description": "Operación matemática que se debe ejecutar.",
                },
                "a": {
                    "type": "number",
                    "description": "Primer operando.",
                },
                "b": {
                    "type": "number",
                    "description": "Segundo operando.",
                },
            },
            "required": ["operation", "a", "b"],
            "additionalProperties": False,
        },
    },
}
TASK_INFO_TOOL = {
    "type": "function",
    "function": {
        "name": TASK_INFO_TOOL_NAME,
        "description": (
            "Consulta la prioridad, duración y categoría de una tarea concreta "
            "almacenada en la lista local de tareas."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task_name": {
                    "type": "string",
                    "description": "Nombre exacto de la tarea que se desea consultar.",
                }
            },
            "required": ["task_name"],
            "additionalProperties": False,
        },
    },
}
AVAILABLE_TOOLS = [CALCULATOR_TOOL, TASK_INFO_TOOL]


def calculate(operation: str, a: float, b: float) -> float:
    # El despacho explícito impide ejecutar código o funciones arbitrarias.
    if operation == "add":
        return a + b
    if operation == "subtract":
        return a - b
    if operation == "multiply":
        return a * b
    if operation == "divide":
        if b == 0:
            raise ValueError("No se puede dividir entre cero.")
        return a / b

    raise ValueError("La operación solicitada no está permitida.")


def get_task_info(task_name: str) -> dict[str, Any]:
    if not isinstance(task_name, str) or not task_name.strip():
        return {"found": False, "error": "El nombre de la tarea no es válido."}

    try:
        tasks = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"found": False, "error": "No se encontró el fichero de tareas."}
    except json.JSONDecodeError:
        return {"found": False, "error": "El fichero de tareas no contiene JSON válido."}
    except (OSError, UnicodeError):
        return {"found": False, "error": "No se pudo leer el fichero de tareas."}

    if not isinstance(tasks, list):
        return {"found": False, "error": "El fichero de tareas tiene una estructura inválida."}

    normalized_name = task_name.strip().casefold()
    for task in tasks:
        if not isinstance(task, dict):
            continue

        name = task.get("nombre")
        if not isinstance(name, str) or name.strip().casefold() != normalized_name:
            continue

        priority = task.get("prioridad")
        duration = task.get("duracion_minutos")
        category = task.get("categoria")
        if (
            not isinstance(priority, str)
            or isinstance(duration, bool)
            or not isinstance(duration, (int, float))
            or not isinstance(category, str)
        ):
            return {
                "found": False,
                "error": "La tarea encontrada tiene una estructura inválida.",
            }

        return {
            "found": True,
            "task": {
                "nombre": name,
                "prioridad": priority,
                "duracion_minutos": duration,
                "categoria": category,
            },
        }

    return {
        "found": False,
        "error": f"No se encontró la tarea '{task_name.strip()}'.",
    }


def parse_calculate_arguments(raw_arguments: str) -> tuple[str, float, float]:
    try:
        arguments = json.loads(raw_arguments)
    except (json.JSONDecodeError, TypeError):
        raise ValueError("Los argumentos no contienen JSON válido.") from None

    if not isinstance(arguments, dict):
        raise ValueError("Los argumentos deben formar un objeto JSON.")

    required_arguments = {"operation", "a", "b"}
    if set(arguments) != required_arguments:
        raise ValueError("Los argumentos deben contener únicamente operation, a y b.")

    operation = arguments["operation"]
    if not isinstance(operation, str) or operation not in ALLOWED_OPERATIONS:
        raise ValueError("La operación solicitada no está permitida.")

    a = arguments["a"]
    b = arguments["b"]
    if (
        isinstance(a, bool)
        or isinstance(b, bool)
        or not isinstance(a, (int, float))
        or not isinstance(b, (int, float))
    ):
        raise ValueError("Los operandos a y b deben ser números.")

    a_value = float(a)
    b_value = float(b)
    if not isfinite(a_value) or not isfinite(b_value):
        raise ValueError("Los operandos deben ser números finitos.")

    return operation, a_value, b_value


def parse_task_arguments(raw_arguments: str) -> str:
    try:
        arguments = json.loads(raw_arguments)
    except (json.JSONDecodeError, TypeError):
        raise ValueError("Los argumentos no contienen JSON válido.") from None

    if not isinstance(arguments, dict):
        raise ValueError("Los argumentos deben formar un objeto JSON.")

    if set(arguments) != {"task_name"}:
        raise ValueError("Los argumentos deben contener únicamente task_name.")

    task_name = arguments["task_name"]
    if not isinstance(task_name, str) or not task_name.strip():
        raise ValueError("task_name debe ser una cadena de texto no vacía.")

    return task_name.strip()


def run_agent(client: Any, messages: list[dict[str, Any]]) -> None:
    # El límite evita que una sucesión de tool calls mantenga el agente en bucle.
    for _ in range(MAX_AGENT_STEPS):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=AVAILABLE_TOOLS,
                tool_choice="auto",
            )
        except Exception:
            print("Error al consultar Groq.")
            return

        if not response.choices:
            print("Error: el modelo devolvió una respuesta vacía.")
            return

        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls or []

        if not tool_calls:
            assistant_content = assistant_message.content
            if not assistant_content or not assistant_content.strip():
                print("Error: el modelo devolvió una respuesta vacía.")
                return
            print(f"IA: {assistant_content}")
            return

        prepared_calls: list[dict[str, Any]] = []
        assistant_tool_calls: list[dict[str, Any]] = []

        # Se validan todas las solicitudes antes de ejecutar la primera función.
        for tool_call in tool_calls:
            if tool_call.type != "function" or tool_call.function is None:
                print("Error: el modelo solicitó una herramienta no permitida.")
                return
            if not tool_call.id:
                print("Error: la solicitud de herramienta no contiene un identificador.")
                return

            tool_name = tool_call.function.name
            raw_arguments = tool_call.function.arguments

            try:
                if tool_name == CALCULATOR_TOOL_NAME:
                    validated_arguments = parse_calculate_arguments(raw_arguments)
                elif tool_name == TASK_INFO_TOOL_NAME:
                    validated_arguments = (parse_task_arguments(raw_arguments),)
                else:
                    print("Error: el modelo solicitó una herramienta no permitida.")
                    return
            except ValueError as error:
                print(f"Error al ejecutar la herramienta: {error}")
                return

            prepared_calls.append(
                {
                    "id": tool_call.id,
                    "name": tool_name,
                    "validated_arguments": validated_arguments,
                }
            )
            assistant_tool_calls.append(
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": raw_arguments,
                    },
                }
            )

        assistant_tool_message: dict[str, Any] = {
            "role": "assistant",
            "tool_calls": assistant_tool_calls,
        }
        if assistant_message.content:
            assistant_tool_message["content"] = assistant_message.content
        messages.append(assistant_tool_message)

        # Las herramientas se ejecutan en el mismo orden solicitado por el modelo.
        for prepared_call in prepared_calls:
            tool_name = prepared_call["name"]
            validated_arguments = prepared_call["validated_arguments"]

            try:
                if tool_name == CALCULATOR_TOOL_NAME:
                    operation, a, b = validated_arguments
                    tool_result = {"result": calculate(operation, a, b)}
                elif tool_name == TASK_INFO_TOOL_NAME:
                    (task_name,) = validated_arguments
                    tool_result = get_task_info(task_name)
                else:
                    print("Error: el modelo solicitó una herramienta no permitida.")
                    return
            except ValueError as error:
                print(f"Error al ejecutar la herramienta: {error}")
                return

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": prepared_call["id"],
                    "content": json.dumps(tool_result, ensure_ascii=False),
                }
            )

    print("Error: se alcanzó el máximo de pasos del agente sin una respuesta final.")


def main() -> None:
    print("=== Asistente IA - Nivel Avanzado ===")

    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY no está configurada en el entorno.")
        return

    question = input("Escribe una pregunta: ").strip()
    if not question:
        print("Debes escribir una pregunta.")
        return

    try:
        client = Groq(api_key=api_key)
    except Exception:
        print("Error: no se pudo inicializar el cliente de Groq.")
        return

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "Eres un asistente técnico. Usa calculate para operaciones "
                "matemáticas, incluso si dependen de datos obtenidos previamente, "
                "y get_task_info para consultar información de una tarea local. "
                "Continúa usando herramientas hasta poder responder con precisión."
            ),
        },
        {"role": "user", "content": question},
    ]
    run_agent(client, messages)


if __name__ == "__main__":
    main()
