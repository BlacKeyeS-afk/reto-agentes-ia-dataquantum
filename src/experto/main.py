"""Punto de entrada del asistente inteligente de tareas."""

import logging
import os
import sys
from typing import Any

from dotenv import load_dotenv

from .agent import AgentError, build_initial_messages, create_groq_client
from .config import LOG_FILE, LOG_FORMAT, LOG_LEVEL
from .graph import build_graph
from .state import AgentState


logger = logging.getLogger(__name__)


def configure_terminal_encoding() -> None:
    """Intenta usar UTF-8 en stdout y stderr sin impedir la ejecución."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue

        try:
            reconfigure(encoding="utf-8")
        except (AttributeError, OSError, TypeError, ValueError):
            continue


def configure_logging() -> None:
    """Configura logs de consola y archivo sin impedir el arranque."""
    try:
        handlers: list[logging.Handler] = [logging.StreamHandler()]
        file_logging_available = True

        try:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(LOG_FILE, encoding="utf-8"))
        except (OSError, ValueError):
            file_logging_available = False

        logging.basicConfig(
            level=LOG_LEVEL,
            format=LOG_FORMAT,
            handlers=handlers,
        )
        for dependency_logger in ("groq", "httpx", "httpcore"):
            logging.getLogger(dependency_logger).setLevel(logging.WARNING)
        if not file_logging_available:
            logger.warning("El archivo de log no está disponible; se usa solo consola.")
    except Exception:
        # Un fallo del logging no debe impedir que la aplicación continúe.
        return


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
    logger.info("Inicio de ejecución del grafo.")
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
    configure_logging()
    logger.info("Aplicación iniciada.")
    print("=== Asistente IA - Nivel Experto (LangGraph) ===")

    try:
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not isinstance(api_key, str) or not api_key.strip():
            logger.error("Aplicación finalizada: falta la configuración de Groq.")
            print("Error: GROQ_API_KEY no está configurada.")
            return
        client = create_groq_client(api_key)
        logger.info("Cliente Groq creado correctamente.")

        question = input("Escribe una pregunta: ").strip()
        if not question:
            logger.warning("Aplicación finalizada: entrada de usuario vacía.")
            print("Error: Debes escribir una pregunta.")
            return

        result = run_agent(client, question)
        if result["error"] is None:
            logger.info("Ejecución del grafo finalizada correctamente.")
        else:
            logger.error("Ejecución del grafo finalizada con error controlado.")
        display_result(result)
    except AgentError as error:
        logger.error("Aplicación finalizada con error controlado del modelo.")
        print(f"Error: {error}")
    except (EOFError, KeyboardInterrupt):
        logger.warning("Aplicación finalizada sin una entrada utilizable.")
        print("\nError: No se pudo leer una pregunta.")
    except Exception:
        logger.error("Aplicación finalizada por un error inesperado.")
        print("Error: No se pudo ejecutar el asistente.")


if __name__ == "__main__":
    main()
