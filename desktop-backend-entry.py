"""Frozen entry point for the TestMaster Desktop local service."""

import os

import uvicorn
from fastapi_backend.main import app


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("TESTMASTER_BACKEND_HOST", "127.0.0.1"),
        port=int(os.getenv("TESTMASTER_BACKEND_PORT", "5001")),
        workers=1,
        log_level=os.getenv("TESTMASTER_LOG_LEVEL", "info"),
        access_log=False,
    )
