"""Creación del cliente, llamada al modelo y normalización de su respuesta."""

from typing import Any

from groq import Groq

from .config import MODEL_NAME, SYSTEM_PROMPT
from .state import AgentState
from .tools import AVAILABLE_TOOLS


class AgentError(RuntimeError):
    """Error controlado de la capa de modelo."""


def build_initial_messages(question: str) -> list[dict[str, str]]:
    """Crea los mensajes iniciales usando el system prompt configurado."""
    if not isinstance(question, str) or not question.strip():
        raise AgentError("La pregunta debe ser una cadena de texto no vacía.")

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question.strip()},
    ]


def create_groq_client(api_key: str) -> Groq:
    """Crea un cliente Groq sin obtener ni mostrar la credencial."""
    if not isinstance(api_key, str) or not api_key.strip():
        raise AgentError("La API key de Groq no está configurada.")

    try:
        return Groq(api_key=api_key.strip())
    except Exception:
        raise AgentError("No se pudo inicializar el cliente de Groq.") from None


def normalize_assistant_message(assistant_message: Any) -> dict[str, Any]:
    """Convierte el mensaje del SDK en una estructura interna estable."""
    try:
        tool_calls = assistant_message.tool_calls or []
    except AttributeError:
        tool_calls = []

    if not isinstance(tool_calls, (list, tuple)):
        raise AgentError("El modelo devolvió una solicitud de herramienta inválida.")

    if tool_calls:
        normalized_calls: list[dict[str, Any]] = []

        for tool_call in tool_calls:
            try:
                tool_call_id = tool_call.id
                tool_call_type = tool_call.type
                function_name = tool_call.function.name
                function_arguments = tool_call.function.arguments
            except AttributeError:
                raise AgentError(
                    "El modelo devolvió una solicitud de herramienta inválida."
                ) from None

            if (
                not isinstance(tool_call_id, str)
                or not tool_call_id
                or not isinstance(tool_call_type, str)
                or not tool_call_type
                or not isinstance(function_name, str)
                or not function_name
                or not isinstance(function_arguments, str)
            ):
                raise AgentError(
                    "El modelo devolvió una solicitud de herramienta inválida."
                )

            normalized_calls.append(
                {
                    "id": tool_call_id,
                    "type": tool_call_type,
                    "function": {
                        "name": function_name,
                        "arguments": function_arguments,
                    },
                }
            )

        return {
            "type": "tool_calls",
            "message": {
                "role": "assistant",
                "tool_calls": normalized_calls,
            },
        }

    try:
        content = assistant_message.content
    except AttributeError:
        raise AgentError("El modelo devolvió un mensaje inválido.") from None

    if not isinstance(content, str) or not content.strip():
        raise AgentError("El modelo devolvió una respuesta vacía.")

    return {
        "type": "final",
        "content": content.strip(),
    }


def call_model(client: Any, messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Llama a Groq y devuelve el mensaje normalizado."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=AVAILABLE_TOOLS,
            tool_choice="auto",
        )
    except Exception:
        raise AgentError("Error al consultar Groq.") from None

    try:
        choices = response.choices
    except AttributeError:
        raise AgentError("El modelo devolvió una respuesta inválida.") from None

    if not choices:
        raise AgentError("El modelo devolvió una respuesta sin choices.")

    try:
        assistant_message = choices[0].message
    except (AttributeError, IndexError, TypeError):
        raise AgentError("El modelo devolvió un mensaje inválido.") from None

    if assistant_message is None:
        raise AgentError("El modelo devolvió un mensaje inválido.")

    return normalize_assistant_message(assistant_message)


def prepare_agent_state_update(
    state: AgentState,
    normalized_response: dict[str, Any],
) -> AgentState:
    """Añade la respuesta normalizada y aumenta el contador del agente."""
    response_type = normalized_response.get("type")

    if response_type == "final":
        content = normalized_response.get("content")
        if not isinstance(content, str) or not content:
            raise AgentError("La respuesta normalizada final es inválida.")
        assistant_message: dict[str, Any] = {
            "role": "assistant",
            "content": content,
        }
        final_answer: str | None = content
    elif response_type == "tool_calls":
        message = normalized_response.get("message")
        if not isinstance(message, dict):
            raise AgentError("La respuesta normalizada de herramientas es inválida.")
        assistant_message = message
        final_answer = None
    else:
        raise AgentError("El tipo de respuesta normalizada no es válido.")

    return {
        "messages": [*state["messages"], assistant_message],
        "agent_steps": state["agent_steps"] + 1,
        "final_answer": final_answer,
        "error": None,
    }
