"""Tests del adaptador Groq mediante respuestas completamente simuladas."""

from types import SimpleNamespace

import pytest

from src.experto.agent import (
    AgentError,
    build_initial_messages,
    call_model,
    normalize_assistant_message,
    prepare_agent_state_update,
)
from src.experto.config import MODEL_NAME, SYSTEM_PROMPT
from src.experto.tools import AVAILABLE_TOOLS


def make_tool_call(call_id="call-1", name="calculate", arguments=None):
    if arguments is None:
        arguments = '{"operation":"multiply","a":12,"b":8}'
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def make_assistant_message(content=None, tool_calls=None):
    return SimpleNamespace(content=content, tool_calls=tool_calls)


class FakeCompletions:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


def make_client(message=None, choices=None, error=None):
    if choices is None:
        choices = [] if message is None else [SimpleNamespace(message=message)]
    completions = FakeCompletions(
        response=SimpleNamespace(choices=choices),
        error=error,
    )
    client = SimpleNamespace(
        chat=SimpleNamespace(completions=completions),
    )
    return client, completions


def make_state():
    return {
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "pregunta"},
        ],
        "agent_steps": 1,
        "final_answer": None,
        "error": None,
    }


def test_build_initial_messages_accepts_valid_question():
    assert build_initial_messages("  pregunta  ") == [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "pregunta"},
    ]


@pytest.mark.parametrize("question", ["", "   ", None])
def test_build_initial_messages_rejects_empty_question(question):
    with pytest.raises(AgentError, match="no vacía"):
        build_initial_messages(question)


def test_normalize_assistant_message_returns_final():
    message = make_assistant_message(content="  respuesta final  ", tool_calls=[])

    assert normalize_assistant_message(message) == {
        "type": "final",
        "content": "respuesta final",
    }


def test_normalize_assistant_message_preserves_calculate_call():
    message = make_assistant_message(tool_calls=[make_tool_call()])

    assert normalize_assistant_message(message) == {
        "type": "tool_calls",
        "message": {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {
                        "name": "calculate",
                        "arguments": '{"operation":"multiply","a":12,"b":8}',
                    },
                }
            ],
        },
    }


def test_normalize_assistant_message_preserves_multiple_calls():
    message = make_assistant_message(
        tool_calls=[
            make_tool_call("call-1"),
            make_tool_call(
                "call-2",
                "get_task_info",
                '{"task_name":"estudiar Python"}',
            ),
        ]
    )

    result = normalize_assistant_message(message)

    assert [call["id"] for call in result["message"]["tool_calls"]] == [
        "call-1",
        "call-2",
    ]


def test_normalize_assistant_message_rejects_empty_content():
    with pytest.raises(AgentError, match="respuesta vacía"):
        normalize_assistant_message(make_assistant_message(content="   ", tool_calls=[]))


def test_normalize_assistant_message_rejects_invalid_structure():
    with pytest.raises(AgentError, match="mensaje inválido"):
        normalize_assistant_message(SimpleNamespace(tool_calls=[]))


def test_normalize_assistant_message_rejects_invalid_id():
    with pytest.raises(AgentError, match="solicitud de herramienta inválida"):
        normalize_assistant_message(
            make_assistant_message(tool_calls=[make_tool_call(call_id="")])
        )


def test_call_model_returns_simulated_final_and_uses_expected_parameters():
    client, completions = make_client(
        make_assistant_message(content="respuesta", tool_calls=[])
    )
    messages = [{"role": "user", "content": "pregunta"}]

    result = call_model(client, messages)

    assert result == {"type": "final", "content": "respuesta"}
    assert completions.calls == [
        {
            "model": MODEL_NAME,
            "messages": messages,
            "tools": AVAILABLE_TOOLS,
            "tool_choice": "auto",
        }
    ]


def test_call_model_returns_simulated_tool_call():
    client, _ = make_client(make_assistant_message(tool_calls=[make_tool_call()]))

    result = call_model(client, [{"role": "user", "content": "pregunta"}])

    assert result["type"] == "tool_calls"
    assert result["message"]["tool_calls"][0]["function"]["name"] == "calculate"


def test_call_model_rejects_empty_choices():
    client, _ = make_client(choices=[])

    with pytest.raises(AgentError, match="sin choices"):
        call_model(client, [])


def test_call_model_converts_client_exception_to_agent_error():
    client, _ = make_client(error=RuntimeError("simulated failure"))

    with pytest.raises(AgentError, match="Error al consultar Groq"):
        call_model(client, [])


def test_prepare_agent_state_update_handles_final_response():
    state = make_state()

    result = prepare_agent_state_update(
        state,
        {"type": "final", "content": "respuesta final"},
    )

    assert result["agent_steps"] == 2
    assert result["final_answer"] == "respuesta final"
    assert result["messages"][:-1] == state["messages"]
    assert result["messages"][-1] == {
        "role": "assistant",
        "content": "respuesta final",
    }


def test_prepare_agent_state_update_handles_tool_calls():
    state = make_state()
    assistant_message = {
        "role": "assistant",
        "tool_calls": [
            {
                "id": "call-1",
                "type": "function",
                "function": {
                    "name": "calculate",
                    "arguments": '{"operation":"add","a":2,"b":3}',
                },
            }
        ],
    }

    result = prepare_agent_state_update(
        state,
        {"type": "tool_calls", "message": assistant_message},
    )

    assert result["agent_steps"] == 2
    assert result["final_answer"] is None
    assert result["messages"][:-1] == state["messages"]
    assert result["messages"][-1] == assistant_message
