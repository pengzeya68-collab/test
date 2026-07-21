import pytest

from fastapi_backend.core.exceptions import ValidationException
from fastapi_backend.models.ui_automation import UIRun
from fastapi_backend.services.ui_automation import run_service


def _run(status: str) -> UIRun:
    return UIRun(
        user_id=1,
        case_id=1,
        status=status,
        trigger_type="manual",
        total_steps=1,
        passed_steps=0,
        failed_steps=0,
        skipped_steps=0,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("terminal", ["passed", "failed", "timed_out"])
async def test_run_cannot_finish_before_it_starts(terminal):
    run = _run("queued")

    with pytest.raises(ValidationException, match="Illegal run status transition"):
        await run_service._transition_run(run, terminal)

    assert run.status == "queued"


@pytest.mark.asyncio
async def test_run_follows_declared_state_machine():
    run = _run("waiting_for_agent")

    await run_service._transition_run(run, "assigned")
    await run_service._transition_run(run, "running")
    await run_service._transition_run(run, "passed")

    assert run.status == "passed"


@pytest.mark.asyncio
async def test_cancel_before_start_remains_supported():
    run = _run("queued")

    await run_service._transition_run(run, "cancelled")

    assert run.status == "cancelled"


class _ScalarDb:
    def __init__(self, run):
        self.run = run

    async def scalar(self, _query):
        return self.run


@pytest.mark.asyncio
async def test_finish_event_must_be_last_in_batch():
    run = _run("running")
    run.id = 9
    run.artifact_manifest = {"_last_sequence": 0}

    with pytest.raises(ValidationException, match="run:finish must be the final"):
        await run_service.append_run_events(
            _ScalarDb(run),
            user_id=1,
            run_id=9,
            events=[
                {"sequence": 1, "type": "run:finish", "status": "passed"},
                {"sequence": 2, "type": "log", "message": "late event"},
            ],
        )

    assert run.status == "running"
    assert run.artifact_manifest == {"_last_sequence": 0}
