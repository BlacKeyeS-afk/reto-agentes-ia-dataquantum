import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


def main() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY no está configurada en el entorno.")
        return

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": "Responde únicamente con: conexión correcta",
                }
            ],
        )
        print(response.choices[0].message.content)
    except Exception as error:
        print(f"Error al conectar con Groq ({type(error).__name__}).")


if __name__ == "__main__":
    main()
