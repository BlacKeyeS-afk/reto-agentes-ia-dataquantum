import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


MODEL_NAME = "openai/gpt-oss-120b"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONVERSATIONS_DIR = PROJECT_ROOT / "conversaciones"


def build_conversation_path(created_at: datetime) -> Path:
    file_stem = f"conversacion_{created_at:%Y-%m-%d_%H-%M-%S}"
    file_path = CONVERSATIONS_DIR / f"{file_stem}.json"
    suffix = 1

    # Añade un sufijo si el nombre ya existe para no sobrescribir historiales.
    while file_path.exists():
        file_path = CONVERSATIONS_DIR / f"{file_stem}_{suffix}.json"
        suffix += 1

    return file_path


def save_conversation(messages: list[dict[str, str]]) -> Path | None:
    # El mensaje system por sí solo no justifica crear un historial persistente.
    has_questions = any(message.get("role") == "user" for message in messages)
    if not has_questions:
        print("No hay conversación que guardar.")
        return None

    created_at = datetime.now()
    conversation_data = {
        "fecha": created_at.isoformat(timespec="seconds"),
        "modelo": MODEL_NAME,
        "mensajes": messages,
    }

    try:
        CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = build_conversation_path(created_at)
        with file_path.open("w", encoding="utf-8") as file:
            # Conserva Unicode legible y facilita la revisión manual del JSON.
            json.dump(conversation_data, file, ensure_ascii=False, indent=2)
    except (OSError, TypeError, ValueError):
        print("Error: no se pudo guardar la conversación.")
        return None

    relative_path = file_path.relative_to(PROJECT_ROOT)
    print(f"Conversación guardada en: {relative_path.as_posix()}")
    return file_path


def main() -> None:
    print("=== Asistente IA - Nivel Intermedio ===")

    env_path = PROJECT_ROOT / ".env"
    load_dotenv(env_path)

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY no está configurada en el entorno.")
        return

    try:
        client = Groq(api_key=api_key)
    except Exception:
        print("Error: no se pudo inicializar el cliente de Groq.")
        return

    # Permanece fuera del bucle para conservar el contexto de toda la sesión.
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": "Eres un asistente útil, claro y conciso.",
        }
    ]

    while True:
        question = input("Escribe tu pregunta (o 'salir'): ").strip()

        if question.casefold() == "salir":
            break

        if not question:
            print("Debes escribir una pregunta.")
            continue

        messages.append({"role": "user", "content": question})

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
            )
            assistant_content = response.choices[0].message.content
            if not assistant_content or not assistant_content.strip():
                raise ValueError
        except Exception:
            # Evita dejar una pregunta user sin respuesta en el historial.
            messages.pop()
            print("Error al consultar Groq. Inténtalo de nuevo.")
            continue

        messages.append({"role": "assistant", "content": assistant_content})
        print(f"IA: {assistant_content}")

    save_conversation(messages)
    print("Hasta luego.")


if __name__ == "__main__":
    main()
