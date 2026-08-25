"""Lógica del futuro nodo de herramientas del grafo experto."""

import json
from typing import TypedDict

from .state import AgentState
from .tools import (
    CALCULATOR_TOOL_NAME,
    TASK_INFO_TOOL_NAME,
    execute_tool,
    parse_calculate_arguments,
    parse_task_arguments,
)


class ToolNodeError(RuntimeError):
    """Error controlado durante la preparación o ejecución de herramientas."""


class PreparedToolCall(TypedDict):
    """Solicitud validada y lista para su ejecución."""

    id: str
    name: str
    arguments: str


def _validate_tool_arguments(tool_name: str, raw_arguments: str) -> None:
    """Valida argumentos sin ejecutar todavía ninguna herramienta."""
    if tool_name == CALCULATOR_TOOL_NAME:
        operation, _, b = parse_calculate_arguments(raw_arguments)
        if operation == "divide" and b == 0:
            raise ToolNodeError("No se puede dividir entre cero.")
        return

    if tool_name == TASK_INFO_TOOL_NAME:
        parse_task_arguments(raw_arguments)
        return

    raise ToolNodeError("La herramienta solicitada no está permitida.")


def prepare_tool_calls(state: AgentState) -> list[PreparedToolCall]:
    """Valida toda la ronda de tool calls antes de permitir su ejecución."""
    messages = state["messages"]
    if not messages:
        raise ToolNodeError("No hay mensajes para procesar.")

    assistant_message = messages[-1]
    if not isinstance(assistant_message, dict):
        raise ToolNodeError("El último mensaje del estado no es válido.")
    if assistant_message.get("role") != "assistant":
        raise ToolNodeError("El último mensaje debe pertenecer al assistant.")

    tool_calls = assistant_message.get("tool_calls")
    if not isinstance(tool_calls, list) or not tool_calls:
        raise ToolNodeError("El último mensaje no contiene tool_calls válidos.")

    prepared_calls: list[PreparedToolCall] = []
    used_ids: set[str] = set()

    for tool_call in tool_calls:
        if not isinstance(tool_call, dict):
            raise ToolNodeError("El modelo devolvió un tool call inválido.")

        tool_call_id = tool_call.get("id")
        tool_call_type = tool_call.get("type")
        function = tool_call.get("function")

        if not isinstance(tool_call_id, str) or not tool_call_id.strip():
            raise ToolNodeError("El tool call no contiene un id válido.")
        if tool_call_id in used_ids:
            raise ToolNodeError("Los identificadores de los tool calls deben ser únicos.")
        if tool_call_type != "function":
            raise ToolNodeError("El tipo del tool call debe ser 'function'.")
        if not isinstance(function, dict):
            raise ToolNodeError("El tool call no contiene una función válida.")

        tool_name = function.get("name")
        raw_arguments = function.get("arguments")
        if not isinstance(tool_name, str) or not tool_name:
            raise ToolNodeError("El tool call no contiene un nombre de función válido.")
        if not isinstance(raw_arguments, str):
            raise ToolNodeError("Los argumentos del tool call deben ser texto JSON.")

        try:
            _validate_tool_arguments(tool_name, raw_arguments)
        except ValueError as error:
            raise ToolNodeError(str(error)) from None

        used_ids.add(tool_call_id)
        prepared_calls.append(
            {
                "id": tool_call_id,
                "name": tool_name,
                "arguments": raw_arguments,
            }
        )

    return prepared_calls


def execute_prepared_tool_calls(
    prepared_calls: list[PreparedToolCall],
) -> list[dict[str, str]]:
    """Ejecuta en orden una ronda que ya ha sido validada por completo."""
    tool_messages: list[dict[str, str]] = []

    for tool_call in prepared_calls:
        result = execute_tool(tool_call["name"], tool_call["arguments"])
        tool_messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": json.dumps(result, ensure_ascii=False),
            }
        )

    return tool_messages


def tools_node(state: AgentState) -> AgentState:
    """Procesa los tool calls o devuelve el estado anterior con un error seguro."""
    try:
        prepared_calls = prepare_tool_calls(state)
        tool_messages = execute_prepared_tool_calls(prepared_calls)
    except (ToolNodeError, ValueError, TypeError) as error:
        return {
            "messages": list(state["messages"]),
            "agent_steps": state["agent_steps"],
            "final_answer": None,
            "error": str(error),
        }
    except Exception:
        return {
            "messages": list(state["messages"]),
            "agent_steps": state["agent_steps"],
            "final_answer": None,
            "error": "No se pudieron ejecutar las herramientas solicitadas.",
        }

    return {
        "messages": [*state["messages"], *tool_messages],
        "agent_steps": state["agent_steps"],
        "final_answer": None,
        "error": None,
    }
