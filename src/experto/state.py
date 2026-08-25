"""Estructura mínima del estado compartido del futuro grafo."""

from typing import Any, TypedDict


class AgentState(TypedDict):
    """Datos que circularán entre los nodos del asistente experto."""

    messages: list[dict[str, Any]]
    agent_steps: int
    final_answer: str | None
    error: str | None
