"""Punto de entrada del asistente inteligente de tareas."""

import os
import sys
from typing import Any

from dotenv import load_dotenv

from .agent import AgentError, build_initial_messages, create_groq_client
from .graph import build_graph
from .state import AgentState


def configure_terminal_encoding() -> None:
    """Intenta usar UTF-8 sin impedir la ejecución en salidas incompatibles."""
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if not callable(reconfigure):
        return

    try:
        reconfigure(encoding="utf-8")
    except (AttributeError, OSError, TypeError, ValueError):
        pass


def create_initial_state(question: str) -> AgentState:
    """Crea el estado inicial de una ejecución independiente."""
    return {
        "messages": build_initial_messages(question),
        "agent_steps": 0,
        "final_answer": None,
        "error": None,
    }


def run_agent(client: Any, question: str) -> AgentState:
    """Construye el grafo y ejecuta una pregunta completa."""
    graph = build_graph(client)
    return graph.invoke(create_initial_state(question))


def display_result(state: AgentState) -> None:
    """Muestra únicamente la respuesta final o un error controlado."""
    if state["error"] is not None:
        print(f"Error: {state['error']}")
        return

    final_answer = state["final_answer"]
    if isinstance(final_answer, str) and final_answer.strip():
        print(f"IA: {final_answer}")
        return

    print("Error: El agente terminó sin proporcionar una respuesta final.")


def main() -> None:
    """Carga la configuración, solicita una pregunta y ejecuta el agente."""
    configure_terminal_encoding()
    print("=== Asistente IA - Nivel Experto (LangGraph) ===")

    try:
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not isinstance(api_key, str) or not api_key.strip():
            print("Error: GROQ_API_KEY no está configurada.")
            return
        client = create_groq_client(api_key)

        question = input("Escribe una pregunta: ").strip()
        if not question:
            print("Error: Debes escribir una pregunta.")
            return

        result = run_agent(client, question)
        display_result(result)
    except AgentError as error:
        print(f"Error: {error}")
    except (EOFError, KeyboardInterrupt):
        print("\nError: No se pudo leer una pregunta.")
    except Exception:
        print("Error: No se pudo ejecutar el asistente.")


if __name__ == "__main__":
    main()
