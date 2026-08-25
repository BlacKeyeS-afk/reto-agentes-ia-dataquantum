"""Configuración no sensible del asistente del Nivel Experto."""

from pathlib import Path


MODEL_NAME = "openai/gpt-oss-120b"
MAX_AGENT_STEPS = 5
TASKS_FILE = Path(__file__).resolve().parents[2] / "data" / "tareas.json"
SYSTEM_PROMPT = (
    "Eres un asistente inteligente de tareas. Usa calculate para realizar "
    "operaciones matemáticas y get_task_info para consultar información de "
    "las tareas locales. Continúa usando herramientas hasta poder responder "
    "de forma clara y precisa."
)
