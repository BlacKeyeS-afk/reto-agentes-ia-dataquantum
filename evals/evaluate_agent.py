"""Evaluación funcional del agente experto con seis casos reproducibles."""

import json
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv

from src.experto.agent import AgentError, create_groq_client
from src.experto.config import MODEL_NAME
from src.experto.graph import build_graph
from src.experto.main import configure_terminal_encoding, create_initial_state
from src.experto.state import AgentState


RESULTS_FILE = Path(__file__).resolve().parent / "results" / "latest.json"

EVALUATION_CASES = [
    {
        "name": "respuesta_directa",
        "question": "Explícame qué es una lista de Python en una frase.",
        "expected": "Respuesta final no vacía, sin error y sin herramientas.",
    },
    {
        "name": "calculadora",
        "question": "¿Cuánto es 13 multiplicado por 9?",
        "expected": "calculate devuelve 117 y la respuesta final contiene 117.",
    },
    {
        "name": "consulta_prioridad",
        "question": "¿Qué prioridad tiene estudiar Python?",
        "expected": "get_task_info devuelve prioridad alta y la respuesta la comunica.",
    },
    {
        "name": "consulta_duracion",
        "question": "¿Cuánto dura hacer compra?",
        "expected": "get_task_info devuelve 45 minutos y la respuesta contiene 45.",
    },
    {
        "name": "multipaso",
        "question": (
            "¿Cuánto dura estudiar Python y cuántos minutos serían si hiciera "
            "esa tarea 3 veces?"
        ),
        "expected": (
            "get_task_info devuelve 90 minutos y la respuesta final contiene 270; "
            "calculate es opcional."
        ),
    },
    {
        "name": "tarea_inexistente",
        "question": "¿Qué prioridad tiene limpiar la piscina?",
        "expected": (
            "get_task_info indica que no existe y la respuesta no inventa prioridad."
        ),
    },
]


def normalize_text(text: str) -> str:
    """Normaliza texto para comparaciones sencillas no sensibles a acentos."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(character for character in decomposed if not unicodedata.combining(character))


def contains_number(text: str, number: int) -> bool:
    """Comprueba un número completo sin exigir una frase exacta."""
    return re.search(rf"(?<!\d){number}(?!\d)", text) is not None


def extract_tool_activity(
    messages: list[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    """Obtiene nombres y resultados de tools sin conservar el historial completo."""
    tool_names: list[str] = []
    names_by_call_id: dict[str, str] = {}

    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        tool_calls = message.get("tool_calls")
        if not isinstance(tool_calls, list):
            continue
        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue
            call_id = tool_call.get("id")
            function = tool_call.get("function")
            if not isinstance(call_id, str) or not isinstance(function, dict):
                continue
            name = function.get("name")
            if not isinstance(name, str):
                continue
            tool_names.append(name)
            names_by_call_id[call_id] = name

    tool_results: list[dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "tool":
            continue
        call_id = message.get("tool_call_id")
        content = message.get("content")
        if not isinstance(call_id, str) or not isinstance(content, str):
            continue
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            continue
        if isinstance(result, dict):
            tool_results.append(
                {
                    "name": names_by_call_id.get(call_id),
                    "result": result,
                }
            )

    return tool_names, tool_results


def find_tool_results(
    tool_results: list[dict[str, Any]], tool_name: str
) -> list[dict[str, Any]]:
    """Devuelve únicamente resultados estructurados de una herramienta concreta."""
    return [
        item["result"]
        for item in tool_results
        if item.get("name") == tool_name and isinstance(item.get("result"), dict)
    ]


def validate_common(state: AgentState) -> str | None:
    """Comprueba las condiciones compartidas por todos los casos."""
    if state["error"] is not None:
        return f"El agente devolvió un error: {state['error']}"
    final_answer = state["final_answer"]
    if not isinstance(final_answer, str) or not final_answer.strip():
        return "El agente no devolvió una respuesta final válida."
    return None


def validate_direct(
    state: AgentState,
    tools_used: list[str],
    tool_results: list[dict[str, Any]],
) -> tuple[bool, str]:
    del tool_results
    common_error = validate_common(state)
    if common_error:
        return False, common_error
    if tools_used:
        return False, "La respuesta directa utilizó herramientas sin necesitarlas."
    return True, "Respuesta final no vacía obtenida sin herramientas."


def validate_calculator(
    state: AgentState,
    tools_used: list[str],
    tool_results: list[dict[str, Any]],
) -> tuple[bool, str]:
    common_error = validate_common(state)
    if common_error:
        return False, common_error
    if "calculate" not in tools_used:
        return False, "El agente no utilizó calculate."
    calculate_results = find_tool_results(tool_results, "calculate")
    if not any(result.get("result") == 117 for result in calculate_results):
        return False, "calculate no produjo el resultado esperado 117."
    if not contains_number(state["final_answer"], 117):
        return False, "La respuesta final no contiene 117."
    return True, "calculate produjo 117 y la respuesta final lo comunicó."


def validate_priority(
    state: AgentState,
    tools_used: list[str],
    tool_results: list[dict[str, Any]],
) -> tuple[bool, str]:
    common_error = validate_common(state)
    if common_error:
        return False, common_error
    if "get_task_info" not in tools_used:
        return False, "El agente no utilizó get_task_info."
    task_results = find_tool_results(tool_results, "get_task_info")
    has_expected_data = any(
        result.get("found") is True
        and isinstance(result.get("task"), dict)
        and result["task"].get("prioridad") == "alta"
        for result in task_results
    )
    if not has_expected_data:
        return False, "get_task_info no devolvió la prioridad alta esperada."
    if "alta" not in normalize_text(state["final_answer"]):
        return False, "La respuesta final no comunica la prioridad alta."
    return True, "La tool devolvió prioridad alta y la respuesta la comunicó."


def validate_duration(
    state: AgentState,
    tools_used: list[str],
    tool_results: list[dict[str, Any]],
) -> tuple[bool, str]:
    common_error = validate_common(state)
    if common_error:
        return False, common_error
    if "get_task_info" not in tools_used:
        return False, "El agente no utilizó get_task_info."
    task_results = find_tool_results(tool_results, "get_task_info")
    has_expected_data = any(
        result.get("found") is True
        and isinstance(result.get("task"), dict)
        and result["task"].get("duracion_minutos") == 45
        for result in task_results
    )
    if not has_expected_data:
        return False, "get_task_info no devolvió la duración esperada de 45 minutos."
    if not contains_number(state["final_answer"], 45):
        return False, "La respuesta final no contiene 45."
    return True, "La tool devolvió 45 minutos y la respuesta los comunicó."


def validate_multistep(
    state: AgentState,
    tools_used: list[str],
    tool_results: list[dict[str, Any]],
) -> tuple[bool, str]:
    common_error = validate_common(state)
    if common_error:
        return False, common_error
    if "get_task_info" not in tools_used:
        return False, "El agente no consultó la tarea con get_task_info."
    task_results = find_tool_results(tool_results, "get_task_info")
    has_ninety_minutes = any(
        result.get("found") is True
        and isinstance(result.get("task"), dict)
        and result["task"].get("duracion_minutos") == 90
        for result in task_results
    )
    if not has_ninety_minutes:
        return False, "get_task_info no devolvió los 90 minutos esperados."
    if not contains_number(state["final_answer"], 270):
        return False, "La respuesta final no contiene el resultado 270."
    calculate_results = find_tool_results(tool_results, "calculate")
    if "calculate" in tools_used and not any(
        result.get("result") == 270 for result in calculate_results
    ):
        return False, "calculate se utilizó, pero no produjo 270."
    return True, "Se usaron los 90 minutos reales y la respuesta final contiene 270."


def validate_missing_task(
    state: AgentState,
    tools_used: list[str],
    tool_results: list[dict[str, Any]],
) -> tuple[bool, str]:
    common_error = validate_common(state)
    if common_error:
        return False, common_error
    if "get_task_info" not in tools_used:
        return False, "El agente no utilizó get_task_info."
    task_results = find_tool_results(tool_results, "get_task_info")
    if not any(result.get("found") is False for result in task_results):
        return False, "get_task_info no indicó que la tarea fuera inexistente."

    normalized_answer = normalize_text(state["final_answer"])
    not_found_markers = (
        "no se encontro",
        "no existe",
        "inexistente",
        "no esta registrada",
        "no esta en",
    )
    if not any(marker in normalized_answer for marker in not_found_markers):
        return False, "La respuesta final no comunica claramente que la tarea no existe."

    invented_priority = re.search(
        r"prioridad\s+(?:es|:)?\s*(?:alta|media|baja)\b",
        normalized_answer,
    )
    if invented_priority:
        return False, "La respuesta final inventa una prioridad para la tarea inexistente."
    return True, "La tarea se comunicó como inexistente sin inventar una prioridad."


VALIDATORS: dict[
    str,
    Callable[
        [AgentState, list[str], list[dict[str, Any]]],
        tuple[bool, str],
    ],
] = {
    "respuesta_directa": validate_direct,
    "calculadora": validate_calculator,
    "consulta_prioridad": validate_priority,
    "consulta_duracion": validate_duration,
    "multipaso": validate_multistep,
    "tarea_inexistente": validate_missing_task,
}


def evaluate_case(compiled_graph: Any, case: dict[str, str]) -> dict[str, Any]:
    """Ejecuta una sola vez un caso y registra su resultado sin historial interno."""
    try:
        state: AgentState = compiled_graph.invoke(create_initial_state(case["question"]))
        tools_used, tool_results = extract_tool_activity(state["messages"])
        passed, reason = VALIDATORS[case["name"]](state, tools_used, tool_results)
        final_answer = state["final_answer"]
        return {
            "name": case["name"],
            "question": case["question"],
            "status": "PASS" if passed else "FAIL",
            "reason": reason,
            "agent_error": state["error"],
            "agent_steps": state["agent_steps"],
            "tools_used": tools_used,
            "final_answer": final_answer if isinstance(final_answer, str) else None,
        }
    except Exception as error:
        return {
            "name": case["name"],
            "question": case["question"],
            "status": "FAIL",
            "reason": f"La evaluación no pudo completar el caso: {type(error).__name__}.",
            "agent_error": "Error inesperado durante la evaluación.",
            "agent_steps": 0,
            "tools_used": [],
            "final_answer": None,
        }


def calculate_summary(results: list[dict[str, Any]]) -> dict[str, int | float]:
    """Calcula métricas agregadas sin modificar los resultados individuales."""
    total = len(results)
    passed = sum(result.get("status") == "PASS" for result in results)
    failed = total - passed
    success_percentage = round((passed / total) * 100, 1) if total else 0.0
    return {
        "total": total,
        "pass": passed,
        "fail": failed,
        "success_percentage": success_percentage,
    }


def build_report(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Construye el documento JSON sanitizado de una ejecución."""
    public_cases = [
        {
            "name": case["name"],
            "question": case["question"],
            "expected": case["expected"],
        }
        for case in EVALUATION_CASES
    ]
    return {
        "fecha": datetime.now().astimezone().isoformat(timespec="seconds"),
        "modelo": MODEL_NAME,
        "casos": public_cases,
        "resultados": results,
        "resumen": calculate_summary(results),
    }


def write_report(report: dict[str, Any], path: Path = RESULTS_FILE) -> None:
    """Guarda el resultado local en JSON legible y sin secretos."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def display_results(report: dict[str, Any]) -> None:
    """Muestra los resultados y métricas de forma legible en terminal."""
    for result in report["resultados"]:
        tools = ", ".join(result["tools_used"]) or "ninguna"
        answer = result["final_answer"] or "(sin respuesta final)"
        error = result["agent_error"] or "ninguno"
        print(f"[{result['status']}] {result['name']}")
        print(f"  Pregunta: {result['question']}")
        print(f"  Motivo: {result['reason']}")
        print(f"  Error del agente: {error}")
        print(f"  Pasos: {result['agent_steps']}")
        print(f"  Herramientas: {tools}")
        print(f"  Respuesta: {answer}")

    summary = report["resumen"]
    print("\nResumen:")
    print(f"Total: {summary['total']}")
    print(f"PASS: {summary['pass']}")
    print(f"FAIL: {summary['fail']}")
    print(f"Éxito: {summary['success_percentage']}%")
    print(f"Resultado local: {RESULTS_FILE.relative_to(Path.cwd())}")


def main() -> int:
    """Ejecuta exactamente una vez cada caso de evaluación configurado."""
    configure_terminal_encoding()
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not isinstance(api_key, str) or not api_key.strip():
        print("Error: GROQ_API_KEY no está configurada.")
        return 1

    try:
        client = create_groq_client(api_key)
        compiled_graph = build_graph(client)
    except AgentError as error:
        print(f"Error: {error}")
        return 1
    except Exception:
        print("Error: No se pudo preparar la evaluación.")
        return 1

    results = [evaluate_case(compiled_graph, case) for case in EVALUATION_CASES]
    report = build_report(results)
    try:
        write_report(report)
    except (OSError, TypeError, ValueError):
        print("Error: No se pudo guardar el resultado local de la evaluación.")
    display_results(report)
    return 0 if report["resumen"]["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
