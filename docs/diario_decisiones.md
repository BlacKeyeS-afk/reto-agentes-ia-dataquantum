# Diario de decisiones

## 2026-08-17 — Preparación inicial

- Se ha elegido Python 3.13.15.
- Se utiliza un entorno virtual llamado `.venv`.
- Las claves API no se almacenarán en Git.
- El proyecto se construirá de forma incremental.

## 2026-08-17 — Dependencias iniciales del Nivel Básico

- El proyecto debe poder realizarse sin gastar dinero en APIs.
- Se ha elegido Groq como proveedor del LLM.
- Inicialmente se utilizará el modelo `openai/gpt-oss-120b`.
- Se ha elegido Groq porque dispone de un nivel gratuito y permite evolucionar posteriormente hacia tool/function calling.
- Se utiliza el SDK oficial `groq`.
- Se utiliza `python-dotenv` para cargar `GROQ_API_KEY` desde `.env`.
- Las credenciales reales nunca se almacenarán en Git.
- Por ahora no se utilizarán LangChain ni LangGraph, para entender primero el funcionamiento directo de una API de LLM.

## 2026-08-17 — Primera conexión real con Groq

- Se realizó con éxito la primera conexión real con Groq.
- Se verificó toda la cadena `.env` → Python → SDK → API → modelo → respuesta.
- Codex mostró `conexi�n` por un problema de codificación de su terminal, pero la respuesta real recibida era `conexión correcta`.
- Se decidió utilizar identificadores de código en inglés y mantener en español los mensajes de interfaz.
