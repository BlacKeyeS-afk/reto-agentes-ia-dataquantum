"""Herramientas locales y validaciones seguras del asistente experto."""

import json
import logging
from math import isfinite
from typing import Any

from .config import TASKS_FILE


logger = logging.getLogger(__name__)


CALCULATOR_TOOL_NAME = "calculate"
TASK_INFO_TOOL_NAME = "get_task_info"
ALLOWED_OPERATIONS = ("add", "subtract", "multiply", "divide")

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
    """Realiza una operación matemática incluida en la lista permitida."""
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
    """Busca una tarea exacta en el fichero JSON local."""
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
    """Valida y normaliza los argumentos JSON de calculate."""
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
    """Valida y normaliza los argumentos JSON de get_task_info."""
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


def execute_tool(tool_name: str, raw_arguments: str) -> dict[str, Any]:
    """Valida y ejecuta exclusivamente una de las herramientas permitidas."""
    # El despacho explícito evita ejecutar funciones arbitrarias por su nombre.
    if tool_name == CALCULATOR_TOOL_NAME:
        logger.info("Inicio de herramienta permitida: calculate.")
        try:
            operation, a, b = parse_calculate_arguments(raw_arguments)
            result = {"result": calculate(operation, a, b)}
        except ValueError:
            logger.warning("Validación o ejecución rechazada para calculate.")
            raise
        logger.info("Herramienta completada correctamente: calculate.")
        return result

    if tool_name == TASK_INFO_TOOL_NAME:
        logger.info("Inicio de herramienta permitida: get_task_info.")
        try:
            task_name = parse_task_arguments(raw_arguments)
        except ValueError:
            logger.warning("Validación rechazada para get_task_info.")
            raise
        result = get_task_info(task_name)
        logger.info("Herramienta completada correctamente: get_task_info.")
        return result

    logger.warning("Solicitud de herramienta no permitida rechazada.")
    raise ValueError("La herramienta solicitada no está permitida.")
