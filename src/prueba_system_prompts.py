import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


MODEL_NAME = "openai/gpt-oss-120b"
COMMON_QUESTION = "Explícame qué es una API."
SYSTEM_PROMPTS = {
    "A": "Eres un asistente útil, claro y conciso.",
    "B": (
        "Eres un profesor de programación paciente. Explica los conceptos paso a "
        "paso con ejemplos sencillos."
    ),
    "C": (
        "Eres un asistente técnico experto. Responde de forma breve, precisa y "
        "profesional."
    ),
}


def main() -> None:
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

    for label, system_prompt in SYSTEM_PROMPTS.items():
        print(f"\n=== Prompt {label} ===")

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": COMMON_QUESTION},
                ],
            )
            assistant_content = response.choices[0].message.content
            if not assistant_content or not assistant_content.strip():
                raise ValueError
        except Exception:
            print("Error al consultar Groq para este prompt.")
            continue

        print("Respuesta:")
        print(assistant_content)


if __name__ == "__main__":
    main()
