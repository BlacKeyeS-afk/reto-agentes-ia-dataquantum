import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


MODEL_NAME = "openai/gpt-oss-120b"


def main() -> None:
    print("=== Asistente IA - Nivel Básico ===")

    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY no está configurada en el entorno.")
        return

    question = input("Escribe tu pregunta: ").strip()
    if not question:
        print("Debes escribir una pregunta.")
        return

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": question}],
        )
        print(f"IA: {response.choices[0].message.content}")
    except Exception as error:
        print(f"Error al consultar Groq ({type(error).__name__}).")


if __name__ == "__main__":
    main()
