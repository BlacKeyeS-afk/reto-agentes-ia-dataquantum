"""Tests del nodo de herramientas y del routing de LangGraph."""

import pytest

from src.experto import graph
from src.experto.config import MAX_AGENT_STEPS
from src.experto.graph import ToolNodeError, prepare_tool_calls, route_after_agent


def make_tool_call(call_id, name, arguments, call_type="function"):
    return {
        "id": call_id,
        "type": call_type,
        "function": {"name": name, "arguments": arguments},
    }


def make_state(messages, agent_steps=1, final_answer=None, error=None):
    return {
        "messages": messages,
        "agent_steps": agent_steps,
        "final_answer": final_answer,
        "error": error,
    }


def state_with_tool_calls(*tool_calls, agent_steps=1):
    return make_state(
        [{"role": "assistant", "tool_calls": list(tool_calls)}],
        agent_steps=agent_steps,
    )


def test_prepare_tool_calls_accepts_calculate():
    state = state_with_tool_calls(
        make_tool_call("call-1", "calculate", '{"operation":"add","a":2,"b":3}')
    )

    assert prepare_tool_calls(state) == [
        {
            "id": "call-1",
            "name": "calculate",
            "arguments": '{"operation":"add","a":2,"b":3}',
        }
    ]


def test_prepare_tool_calls_accepts_task_lookup():
    state = state_with_tool_calls(
        make_tool_call(
            "call-2",
            "get_task_info",
            '{"task_name":"estudiar Python"}',
        )
    )

    assert prepare_tool_calls(state)[0]["name"] == "get_task_info"


def test_prepare_tool_calls_accepts_multiple_calls_in_order():
    state = state_with_tool_calls(
        make_tool_call(
            "call-1",
            "get_task_info",
            '{"task_name":"estudiar Python"}',
        ),
        make_tool_call(
            "call-2",
            "calculate",
            '{"operation":"multiply","a":90,"b":3}',
        ),
    )

    assert [item["id"] for item in prepare_tool_calls(state)] == ["call-1", "call-2"]


def test_prepare_tool_calls_rejects_duplicate_ids():
    state = state_with_tool_calls(
        make_tool_call("same", "calculate", '{"operation":"add","a":2,"b":3}'),
        make_tool_call("same", "calculate", '{"operation":"add","a":4,"b":5}'),
    )

    with pytest.raises(ToolNodeError, match="deben ser únicos"):
        prepare_tool_calls(state)


def test_prepare_tool_calls_rejects_unknown_tool():
    state = state_with_tool_calls(make_tool_call("call-1", "unknown", "{}"))

    with pytest.raises(ToolNodeError, match="no está permitida"):
        prepare_tool_calls(state)


def test_prepare_tool_calls_rejects_non_function_type():
    state = state_with_tool_calls(
        make_tool_call(
            "call-1",
            "calculate",
            '{"operation":"add","a":2,"b":3}',
            call_type="custom",
        )
    )

    with pytest.raises(ToolNodeError, match="debe ser 'function'"):
        prepare_tool_calls(state)


def test_prepare_tool_calls_rejects_invalid_arguments():
    state = state_with_tool_calls(
        make_tool_call("call-1", "calculate", '{"operation":"add","a":"2","b":3}')
    )

    with pytest.raises(ToolNodeError, match="deben ser números"):
        prepare_tool_calls(state)


def test_prepare_tool_calls_rejects_empty_messages():
    with pytest.raises(ToolNodeError, match="No hay mensajes"):
        prepare_tool_calls(make_state([]))


def test_prepare_tool_calls_rejects_last_message_without_calls():
    state = make_state([{"role": "assistant", "content": "respuesta"}])

    with pytest.raises(ToolNodeError, match="no contiene tool_calls"):
        prepare_tool_calls(state)


def test_tools_node_adds_tool_role_and_preserves_id_and_steps():
    state = state_with_tool_calls(
        make_tool_call(
            "call-1",
            "calculate",
            '{"operation":"multiply","a":8,"b":9}',
        ),
        agent_steps=2,
    )

    result = graph.tools_node(state)

    assert result["messages"][-1]["role"] == "tool"
    assert result["messages"][-1]["tool_call_id"] == "call-1"
    assert result["agent_steps"] == 2
    assert result["error"] is None


def test_tools_node_preserves_multiple_call_order():
    state = state_with_tool_calls(
        make_tool_call("call-1", "calculate", '{"operation":"add","a":2,"b":3}'),
        make_tool_call(
            "call-2",
            "get_task_info",
            '{"task_name":"estudiar Python"}',
        ),
    )

    result = graph.tools_node(state)

    assert [message["tool_call_id"] for message in result["messages"][-2:]] == [
        "call-1",
        "call-2",
    ]


def test_tools_node_does_not_add_partial_results(monkeypatch):
    executed = []
    monkeypatch.setattr(
        graph,
        "execute_tool",
        lambda name, arguments: executed.append((name, arguments)),
    )
    state = state_with_tool_calls(
        make_tool_call("call-1", "calculate", '{"operation":"add","a":2,"b":3}'),
        make_tool_call("call-2", "unknown", "{}"),
    )

    result = graph.tools_node(state)

    assert executed == []
    assert result["messages"] == state["messages"]
    assert result["error"] is not None


def test_route_after_agent_ends_with_final_answer():
    state = make_state([], final_answer="respuesta")

    assert route_after_agent(state) == "end"


def test_route_after_agent_ends_with_error():
    state = make_state([], error="error controlado")

    assert route_after_agent(state) == "end"


def test_route_after_agent_routes_tool_calls():
    state = state_with_tool_calls(
        make_tool_call("call-1", "calculate", '{"operation":"add","a":2,"b":3}')
    )

    assert route_after_agent(state) == "tools"


def test_route_after_agent_ends_at_step_limit():
    state = state_with_tool_calls(
        make_tool_call("call-1", "calculate", '{"operation":"add","a":2,"b":3}'),
        agent_steps=MAX_AGENT_STEPS,
    )

    assert route_after_agent(state) == "end"


def test_route_after_agent_ends_with_incoherent_state():
    state = make_state([{"role": "assistant", "content": "sin final"}])

    assert route_after_agent(state) == "end"


def test_max_agent_steps_remains_five():
    assert MAX_AGENT_STEPS == 5
