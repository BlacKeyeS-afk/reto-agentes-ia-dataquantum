import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


MODEL_NAME = "openai/gpt-oss-120b"


def main() -> None:
    print("=== Asistente IA - Nivel Intermedio ===")

    env_path = Path(__file__).resolve().parent.parent / ".env"
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
            messages.pop()
            print("Error al consultar Groq. Inténtalo de nuevo.")
            continue

        messages.append({"role": "assistant", "content": assistant_content})
        print(f"IA: {assistant_content}")

    print("Hasta luego.")


if __name__ == "__main__":
    main()
