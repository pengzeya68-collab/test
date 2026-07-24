$ErrorActionPreference = 'Stop'
$desktopDir = Split-Path -Parent $PSScriptRoot
$projectRoot = Split-Path -Parent $desktopDir
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$entry = Join-Path $projectRoot 'desktop-backend-entry.py'
$dist = Join-Path $desktopDir 'backend-dist'
$work = Join-Path $desktopDir '.backend-build'

if (-not (Test-Path -LiteralPath $python)) {
    throw 'Backend packaging requires .venv\Scripts\python.exe'
}

Push-Location $projectRoot
try {
    & $python -m PyInstaller --noconfirm --clean --onedir --name testmaster-backend `
        --distpath $dist --workpath $work --specpath $work `
        --paths $projectRoot `
        --collect-submodules fastapi_backend.routers `
        --collect-submodules fastapi_backend.services `
        --collect-submodules fastapi_backend.models `
        --collect-submodules fastapi_backend.schemas `
        --collect-submodules fastapi_backend.core `
        --collect-submodules fastapi_backend.deps `
        --collect-submodules fastapi_backend.middleware `
        --collect-submodules fastapi_backend.utils `
        --collect-all alembic `
        --collect-submodules uvicorn `
        --collect-submodules sqlalchemy `
        --collect-submodules aiohttp `
        --collect-submodules grpc_tools `
        --collect-submodules grpc_reflection `
        --collect-submodules paho `
        --collect-submodules celery `
        --collect-submodules kombu `
        --collect-submodules billiard `
        --collect-submodules vine `
        --hidden-import aiosqlite `
        --add-data "$projectRoot\fastapi_backend\alembic;fastapi_backend\alembic" `
        --add-data "$projectRoot\fastapi_backend\alembic.ini;fastapi_backend" `
        $entry
} finally {
    Pop-Location
}

if ($LASTEXITCODE -ne 0) { throw "Backend packaging failed with exit code $LASTEXITCODE" }
