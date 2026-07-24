"""Phase A: variable merge priority runtime > data_row > scenario_extract > env > project > default."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from fastapi_backend.services.autotest_variable_service import merge_variable_layers


def test_variable_priority_runtime_wins():
    merged = merge_variable_layers(
        defaults={"k": "default", "only_default": "d"},
        project={"k": "project", "only_project": "p"},
        env={"k": "env", "only_env": "e"},
        scenario_extract={"k": "extract", "only_extract": "x"},
        data_row={"k": "row", "only_row": "r"},
        runtime={"k": "runtime", "only_runtime": "rt"},
    )
    assert merged["k"] == "runtime"
    assert merged["only_runtime"] == "rt"
    assert merged["only_row"] == "r"
    assert merged["only_extract"] == "x"
    assert merged["only_env"] == "e"
    assert merged["only_project"] == "p"
    assert merged["only_default"] == "d"


def test_merge_lower_layers_fill_gaps_only():
    merged = merge_variable_layers(project={"a": 1, "b": 2}, runtime={"b": 9})
    assert merged == {"a": 1, "b": 9}


@pytest.mark.asyncio
async def test_resolve_variables_does_not_clobber_runtime(monkeypatch):
    from fastapi_backend.services import autotest_request_service as req

    class _Scalars:
        def all(self):
            return [
                SimpleNamespace(name="k", value="global", is_encrypted=False),
                SimpleNamespace(name="g_only", value="G", is_encrypted=False),
            ]

    class _Result:
        def scalars(self):
            return _Scalars()

        def scalar_one_or_none(self):
            return SimpleNamespace(
                id=1,
                base_url="https://env.example",
                parent_id=None,
                variables={"k": "env", "e_only": "E"},
            )

    class _Session:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def execute(self, stmt):
            return _Result()

    monkeypatch.setattr(
        "fastapi_backend.core.autotest_database.AsyncSessionLocal",
        lambda: _Session(),
    )
    out = await req.resolve_variables(env_id=1, variables={"k": "runtime"}, user_id=1)
    assert out["k"] == "runtime"
    assert out["g_only"] == "G"
    assert out["e_only"] == "E"
    assert out.get("base_url") == "https://env.example"
