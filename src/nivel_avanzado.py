import json
import os
from math import isfinite
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import Groq


MODEL_NAME = "openai/gpt-oss-120b"
TOOL_NAME = "calculate"
ALLOWED_OPERATIONS = ("add", "subtract", "multiply", "divide")
CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": TOOL_NAME,
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
                "Eres un asistente técnico. Usa la herramienta calculate cuando "
                "la pregunta requiera una operación matemática básica."
            ),
        },
        {"role": "user", "content": question},
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=[CALCULATOR_TOOL],
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

    if len(tool_calls) != 1:
        print("Error: se esperaba una única solicitud de herramienta.")
        return

    tool_call = tool_calls[0]
    if tool_call.type != "function" or tool_call.function.name != TOOL_NAME:
        print("Error: el modelo solicitó una herramienta no permitida.")
        return
    if not tool_call.id:
        print("Error: la solicitud de herramienta no contiene un identificador.")
        return

    # Los argumentos del modelo se validan antes de llamar a Python.
    try:
        operation, a, b = parse_calculate_arguments(tool_call.function.arguments)
        result = calculate(operation, a, b)
    except ValueError as error:
        print(f"Error al ejecutar la herramienta: {error}")
        return

    assistant_tool_message: dict[str, Any] = {
        "role": "assistant",
        "tool_calls": [
            {
                "id": tool_call.id,
                "type": "function",
                "function": {
                    "name": TOOL_NAME,
                    "arguments": tool_call.function.arguments,
                },
            }
        ],
    }
    if assistant_message.content:
        assistant_tool_message["content"] = assistant_message.content

    messages.append(assistant_tool_message)
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps({"result": result}, ensure_ascii=False),
        }
    )

    try:
        final_response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
        )
    except Exception:
        print("Error al obtener la respuesta final de Groq.")
        return

    if not final_response.choices:
        print("Error: el modelo devolvió una respuesta final vacía.")
        return

    final_content = final_response.choices[0].message.content
    if not final_content or not final_content.strip():
        print("Error: el modelo devolvió una respuesta final vacía.")
        return

    print(f"IA: {final_content}")


if __name__ == "__main__":
    main()
