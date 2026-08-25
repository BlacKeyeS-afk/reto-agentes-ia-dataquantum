"""Tests de las herramientas locales y sus validaciones."""

import pytest

from src.experto import tools
from src.experto.tools import (
    calculate,
    execute_tool,
    get_task_info,
    parse_calculate_arguments,
    parse_task_arguments,
)


@pytest.mark.parametrize(
    ("operation", "a", "b", "expected"),
    [
        ("add", 2, 3, 5),
        ("subtract", 10, 4, 6),
        ("multiply", 7, 8, 56),
        ("divide", 20, 4, 5),
    ],
)
def test_calculate_operations(operation, a, b, expected):
    assert calculate(operation, a, b) == expected


def test_calculate_rejects_division_by_zero():
    with pytest.raises(ValueError, match="dividir entre cero"):
        calculate("divide", 10, 0)


def test_calculate_rejects_unknown_operation():
    with pytest.raises(ValueError, match="no está permitida"):
        calculate("power", 2, 3)


def test_parse_calculate_arguments_accepts_valid_json():
    assert parse_calculate_arguments('{"operation":"multiply","a":9,"b":7}') == (
        "multiply",
        9.0,
        7.0,
    )


def test_parse_calculate_arguments_rejects_invalid_json():
    with pytest.raises(ValueError, match="JSON válido"):
        parse_calculate_arguments("not-json")


def test_parse_calculate_arguments_rejects_invalid_operation():
    with pytest.raises(ValueError, match="no está permitida"):
        parse_calculate_arguments('{"operation":"power","a":2,"b":3}')


@pytest.mark.parametrize(
    "raw_arguments",
    [
        '{"operation":"add","a":"2","b":3}',
        '{"operation":"add","a":2,"b":null}',
    ],
)
def test_parse_calculate_arguments_rejects_incorrect_types(raw_arguments):
    with pytest.raises(ValueError, match="deben ser números"):
        parse_calculate_arguments(raw_arguments)


@pytest.mark.parametrize(
    "raw_arguments",
    [
        '{"operation":"add","a":true,"b":3}',
        '{"operation":"add","a":2,"b":false}',
    ],
)
def test_parse_calculate_arguments_rejects_booleans(raw_arguments):
    with pytest.raises(ValueError, match="deben ser números"):
        parse_calculate_arguments(raw_arguments)


@pytest.mark.parametrize(
    "raw_arguments",
    [
        '{"operation":"add","a":NaN,"b":3}',
        '{"operation":"add","a":1e400,"b":3}',
    ],
)
def test_parse_calculate_arguments_rejects_non_finite_numbers(raw_arguments):
    with pytest.raises(ValueError, match="números finitos"):
        parse_calculate_arguments(raw_arguments)


def test_parse_calculate_arguments_rejects_additional_arguments():
    raw_arguments = '{"operation":"add","a":2,"b":3,"extra":1}'
    with pytest.raises(ValueError, match="únicamente operation, a y b"):
        parse_calculate_arguments(raw_arguments)


def test_parse_calculate_arguments_rejects_missing_arguments():
    with pytest.raises(ValueError, match="únicamente operation, a y b"):
        parse_calculate_arguments('{"operation":"add","a":2}')


def test_parse_task_arguments_accepts_valid_json():
    assert parse_task_arguments('{"task_name":"  estudiar Python  "}') == (
        "estudiar Python"
    )


def test_parse_task_arguments_rejects_invalid_json():
    with pytest.raises(ValueError, match="JSON válido"):
        parse_task_arguments("not-json")


def test_parse_task_arguments_rejects_empty_name():
    with pytest.raises(ValueError, match="no vacía"):
        parse_task_arguments('{"task_name":"   "}')


def test_parse_task_arguments_rejects_missing_property():
    with pytest.raises(ValueError, match="únicamente task_name"):
        parse_task_arguments("{}")


def test_parse_task_arguments_rejects_additional_properties():
    with pytest.raises(ValueError, match="únicamente task_name"):
        parse_task_arguments('{"task_name":"estudiar Python","extra":1}')


def test_get_task_info_returns_expected_task_data():
    result = get_task_info("estudiar Python")

    assert result["found"] is True
    assert result["task"] == {
        "nombre": "estudiar Python",
        "prioridad": "alta",
        "duracion_minutos": 90,
        "categoria": "estudio",
    }


def test_get_task_info_is_case_insensitive():
    result = get_task_info("ESTUDIAR PYTHON")

    assert result["found"] is True
    assert result["task"]["nombre"] == "estudiar Python"


def test_get_task_info_handles_unknown_task():
    result = get_task_info("tarea inexistente")

    assert result["found"] is False
    assert "No se encontró" in result["error"]


def test_get_task_info_handles_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(tools, "TASKS_FILE", tmp_path / "missing.json")

    assert get_task_info("estudiar Python") == {
        "found": False,
        "error": "No se encontró el fichero de tareas.",
    }


def test_get_task_info_handles_invalid_json(monkeypatch, tmp_path):
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("not-json", encoding="utf-8")
    monkeypatch.setattr(tools, "TASKS_FILE", invalid_file)

    assert get_task_info("estudiar Python") == {
        "found": False,
        "error": "El fichero de tareas no contiene JSON válido.",
    }


def test_execute_tool_runs_calculate():
    result = execute_tool("calculate", '{"operation":"multiply","a":9,"b":7}')

    assert result == {"result": 63.0}


def test_execute_tool_runs_task_lookup():
    result = execute_tool("get_task_info", '{"task_name":"estudiar Python"}')

    assert result["found"] is True
    assert result["task"]["duracion_minutos"] == 90


def test_execute_tool_rejects_unknown_tool():
    with pytest.raises(ValueError, match="no está permitida"):
        execute_tool("unknown", "{}")
