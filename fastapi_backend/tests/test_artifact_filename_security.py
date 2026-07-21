import pytest
from fastapi import HTTPException

from fastapi_backend.core.exceptions import ValidationException
from fastapi_backend.routers.autotest_artifacts import _safe_filename
from fastapi_backend.services.ui_automation.run_service import _safe_artifact_filename


@pytest.mark.parametrize(
    "filename",
    ["report\r\nX-Injected: yes.png", "../escape.zip", "..\\escape.zip", "bad:name.png"],
)
def test_shared_artifact_filename_rejects_headers_and_paths(filename):
    with pytest.raises(HTTPException) as error:
        _safe_filename(filename)

    assert error.value.status_code == 422


def test_legacy_ui_artifact_filename_is_server_sanitized():
    assert _safe_artifact_filename("..\\..\\bad:name\r\n.png") == "bad_name__.png"


@pytest.mark.parametrize("filename", ["", "...", "\x00"])
def test_legacy_ui_artifact_filename_cannot_be_empty_after_sanitizing(filename):
    with pytest.raises(ValidationException):
        _safe_artifact_filename(filename)
