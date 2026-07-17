"""UI Automation router."""


from typing import Optional
import re

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fastapi_backend.core.config import settings
from fastapi_backend.core.database import get_db
from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.core.exceptions import BusinessException
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.models import User
from fastapi_backend.models.autotest import AutoTestEnvironment, AutoTestGlobalVariable
from fastapi_backend.schemas.ui_automation import (
    UIArtifactCreate,
    UIArtifactOut,
    UIArtifactUploadIn,
    UICaseCreate,
    UICaseGroupCreate,
    UICaseGroupOut,
    UICaseGroupUpdate,
    UICaseOut,
    UICaseUpdate,
    UICaseVersionCreate,
    UICaseVersionOut,
    UIRunCreate,
    UIRunEventBatchIn,
    UIRunEventBatchOut,
    UIRunOut,
    UIStepBatchSave,
    UIStepResultOut,
    UISuiteCreate,
    UISuiteUpdate,
    UISuiteOut,
    UISuiteItemCreate,
)
from fastapi_backend.services.ui_automation import case_service, run_service, suite_service
from fastapi_backend.services.autotest_variable_service import get_effective_variables
from fastapi_backend.utils.encryption import decrypt

router = APIRouter(prefix='/api/ui-automation', tags=['ui-automation'])


def _ensure_enabled() -> None:
    if not getattr(settings, 'UI_AUTOMATION_ENABLED', False):
        raise BusinessException('UI automation feature is disabled', code='FEATURE_DISABLED', status_code=403)


_SENSITIVE_VARIABLE = re.compile(r'(password|passwd|secret|token|api[_-]?key|private[_-]?key)', re.IGNORECASE)


@router.get('/runtime-config')
async def get_runtime_config(
    environment_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    autotest_db: AsyncSession = Depends(get_autotest_db),
):
    """Resolve execution variables for the trusted desktop main process."""
    _ensure_enabled()
    variables: dict[str, str] = {}
    secret_keys: set[str] = set()

    global_result = await autotest_db.execute(
        select(AutoTestGlobalVariable).where(AutoTestGlobalVariable.user_id == current_user.id)
    )
    for item in global_result.scalars().all():
        value = decrypt(item.value) if item.is_encrypted else item.value
        variables[item.name] = '' if value is None else str(value)
        if item.is_encrypted or _SENSITIVE_VARIABLE.search(item.name):
            secret_keys.add(item.name)

    base_url = ''
    environment_name = None
    if environment_id is not None:
        env_result = await autotest_db.execute(
            select(AutoTestEnvironment).where(
                AutoTestEnvironment.id == environment_id,
                AutoTestEnvironment.user_id == current_user.id,
            )
        )
        environment = env_result.scalar_one_or_none()
        if environment is None:
            raise BusinessException('Environment not found', code='ENVIRONMENT_NOT_FOUND', status_code=404)
        base_url = environment.base_url or ''
        environment_name = environment.env_name
        for item in await get_effective_variables(autotest_db, environment_id, user_id=current_user.id):
            variables[item['name']] = '' if item['value'] is None else str(item['value'])
            if _SENSITIVE_VARIABLE.search(item['name']):
                secret_keys.add(item['name'])

    return {
        'environment_id': environment_id,
        'environment_name': environment_name,
        'base_url': base_url,
        'variables': variables,
        'secret_keys': sorted(secret_keys),
    }

@router.get('/cases')
async def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    group_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    cases, total = await case_service.list_cases(
        db, current_user.id, page=page, page_size=page_size, group_id=group_id, keyword=keyword, status=status
    )
    return {'items': [UICaseOut.model_validate(case).model_dump() for case in cases], 'total': total, 'page': page, 'size': page_size}


@router.get('/cases/{case_id}')
async def get_case(case_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    case = await case_service.get_case(db, current_user.id, case_id)
    steps = await case_service.list_steps(db, case_id)
    payload = UICaseOut.model_validate(case).model_dump()
    payload['steps'] = [case_service.step_to_snapshot_dict(step) for step in steps]
    return payload


@router.post('/cases')
async def create_case(body: UICaseCreate, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    case = await case_service.create_case(db, current_user.id, body.model_dump())
    await db.commit()
    return UICaseOut.model_validate(case).model_dump()


@router.put('/cases/{case_id}')
async def update_case(case_id: int, body: UICaseUpdate, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    case = await case_service.update_case(db, current_user.id, case_id, body.model_dump(exclude_unset=True))
    await db.commit()
    return UICaseOut.model_validate(case).model_dump()


@router.delete('/cases/{case_id}')
async def delete_case(case_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    await case_service.delete_case(db, current_user.id, case_id)
    await db.commit()
    return {'message': 'Case deleted'}


@router.put('/cases/{case_id}/steps')
async def batch_save_steps(case_id: int, body: UIStepBatchSave, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    await case_service.get_case(db, current_user.id, case_id)
    steps = await case_service.batch_save_steps(db, case_id, [step.model_dump(by_alias=True) for step in body.steps])
    await db.commit()
    return {'message': f'Saved {len(steps)} steps', 'steps': [case_service.step_to_snapshot_dict(step) for step in steps]}


@router.post('/cases/{case_id}/versions')
async def create_version(case_id: int, body: UICaseVersionCreate, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    version = await case_service.create_version_from_case(db, current_user.id, case_id, body.change_summary)
    await db.commit()
    return UICaseVersionOut.model_validate(version).model_dump()


@router.get('/cases/{case_id}/versions')
async def list_versions(case_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    versions = await case_service.list_versions(db, case_id, current_user.id)
    return {'items': [UICaseVersionOut.model_validate(version).model_dump() for version in versions], 'total': len(versions)}


@router.get('/cases/{case_id}/versions/{version_id}')
async def get_version(case_id: int, version_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    version = await case_service.get_version(db, case_id, version_id, current_user.id)
    return UICaseVersionOut.model_validate(version).model_dump()


@router.post('/cases/{case_id}/versions/{version_id}/restore')
async def restore_version(case_id: int, version_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    case = await case_service.restore_version(db, case_id, version_id, current_user.id)
    await db.commit()
    return UICaseOut.model_validate(case).model_dump()


@router.get('/groups')
async def list_groups(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    groups = await case_service.list_groups(db, current_user.id)
    return {'items': [UICaseGroupOut.model_validate(group).model_dump() for group in groups], 'total': len(groups)}


@router.post('/groups')
async def create_group(body: UICaseGroupCreate, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    group = await case_service.create_group(db, current_user.id, body.model_dump())
    await db.commit()
    return UICaseGroupOut.model_validate(group).model_dump()


@router.put('/groups/{group_id}')
async def update_group(group_id: int, body: UICaseGroupUpdate, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    group = await case_service.update_group(db, current_user.id, group_id, body.model_dump(exclude_unset=True))
    await db.commit()
    return UICaseGroupOut.model_validate(group).model_dump()


@router.delete('/groups/{group_id}')
async def delete_group(group_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    await case_service.delete_group(db, current_user.id, group_id)
    await db.commit()
    return {'message': 'Group deleted'}


@router.get('/suites')
async def list_ui_suites(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    suites = await suite_service.list_suites(db, current_user.id)
    return {'items': [UISuiteOut.model_validate(item).model_dump() for item in suites], 'total': len(suites)}


@router.post('/suites')
async def create_ui_suite(body: UISuiteCreate, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    suite = await suite_service.create_suite(db, current_user.id, body.model_dump())
    await db.commit()
    return UISuiteOut.model_validate(suite).model_dump()


@router.get('/suites/{suite_id}')
async def get_ui_suite(suite_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    suite = await suite_service.get_suite(db, current_user.id, suite_id)
    return UISuiteOut.model_validate(suite).model_dump()


@router.put('/suites/{suite_id}')
async def update_ui_suite(suite_id: int, body: UISuiteUpdate, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    suite = await suite_service.update_suite(db, current_user.id, suite_id, body.model_dump(exclude_unset=True))
    await db.commit()
    return UISuiteOut.model_validate(suite).model_dump()


@router.put('/suites/{suite_id}/items')
async def replace_ui_suite_items(suite_id: int, body: list[UISuiteItemCreate], current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    suite = await suite_service.replace_items(db, current_user.id, suite_id, [item.model_dump() for item in body])
    await db.commit()
    return UISuiteOut.model_validate(suite).model_dump()


@router.get('/suites/{suite_id}/execution-plan')
async def get_ui_suite_execution_plan(suite_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    return await suite_service.build_execution_plan(db, current_user.id, suite_id)


@router.delete('/suites/{suite_id}')
async def delete_ui_suite(suite_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    await suite_service.delete_suite(db, current_user.id, suite_id)
    await db.commit()
    return {'message': 'Suite deleted'}

@router.get('/runs')
async def list_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    status: Optional[str] = Query(None),
    case_id: Optional[int] = Query(None),
    suite_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    runs, total = await run_service.list_runs(db, current_user.id, page=page, page_size=page_size, status=status, case_id=case_id, suite_id=suite_id)
    return {'items': [UIRunOut.model_validate(run).model_dump() for run in runs], 'total': total, 'page': page, 'size': page_size}


@router.post('/runs')
async def create_run(body: UIRunCreate, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    run = await run_service.create_run(db, current_user.id, body.model_dump())
    await db.commit()
    return UIRunOut.model_validate(run).model_dump()


@router.get('/runs/{run_id}')
async def get_run(run_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    run = await run_service.get_run(db, current_user.id, run_id)
    return UIRunOut.model_validate(run).model_dump()


@router.get('/runs/{run_id}/step-results')
async def get_run_step_results(run_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    step_results = await run_service.list_step_results(db, current_user.id, run_id)
    return {'items': [UIStepResultOut.model_validate(item).model_dump() for item in step_results], 'total': len(step_results)}


@router.post('/runs/{run_id}/events')
async def append_run_events(run_id: int, body: UIRunEventBatchIn, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    accepted, ignored, last_sequence, run = await run_service.append_run_events(
        db,
        current_user.id,
        run_id,
        [event.model_dump(exclude_none=True) for event in body.events],
    )
    await db.commit()
    return UIRunEventBatchOut(accepted=accepted, ignored=ignored, last_sequence=last_sequence, status=run.status).model_dump()


@router.get('/runs/{run_id}/artifacts')
async def list_run_artifacts(run_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    artifacts = await run_service.list_artifacts(db, current_user.id, run_id)
    return {'items': [UIArtifactOut.model_validate(item).model_dump() for item in artifacts], 'total': len(artifacts)}


@router.get('/runs/{run_id}/artifacts/{artifact_id}/content')
async def get_run_artifact_content(run_id: int, artifact_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    artifact, content = await run_service.read_artifact_content(db, current_user.id, run_id, artifact_id)
    import base64
    return {
        'filename': artifact.filename,
        'mime_type': artifact.mime_type or 'application/octet-stream',
        'size_bytes': len(content),
        'content_base64': base64.b64encode(content).decode('ascii'),
    }

@router.post('/runs/{run_id}/artifacts')
async def register_run_artifact(run_id: int, body: UIArtifactCreate = Body(...), current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    artifact = await run_service.register_artifact(db, current_user.id, run_id, body.model_dump())
    await db.commit()
    return UIArtifactOut.model_validate(artifact).model_dump()



@router.post('/runs/{run_id}/artifacts/upload')
async def upload_run_artifact(run_id: int, body: UIArtifactUploadIn, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    artifact = await run_service.upload_artifact_content(db, current_user.id, run_id, body.model_dump())
    await db.commit()
    return UIArtifactOut.model_validate(artifact).model_dump()


@router.get('/health')
async def health():
    return {'status': 'ok', 'enabled': getattr(settings, 'UI_AUTOMATION_ENABLED', False), 'module': 'ui-automation', 'phase': 'phase-1'}










