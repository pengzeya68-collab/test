"""
AutoTest 统一路由 - 场景管理

路径前缀: /api/auto-test/scenarios
映射原 auto_test_platform 的 /api/scenarios
"""

import uuid
import logging
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.core.audit_decorator import audit_log
from fastapi_backend.core.rbac import require_permissions
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.services.audit_service import AuditService
from fastapi_backend.models.autotest import (
    AutoTestScenario,
    AutoTestScenarioStep,
    AutoTestCase,
    AutoTestDataset,
    AutoTestScenarioExecutionRecord,
)
from fastapi_backend.models.models import User
from fastapi_backend.schemas.autotest import (
    AutoTestScenarioCreate,
    AutoTestScenarioUpdate,
    AutoTestScenarioResponse,
    ScenarioStepCreate,
    ScenarioStepUpdate,
    ScenarioStepResponse,
    AutoTestDatasetBase,
    AutoTestDatasetResponse,
    InlineScenarioExecutionRequest,
)

router = APIRouter(prefix="/api/auto-test/scenarios", tags=["AutoTest-场景"])

_logger = logging.getLogger(__name__)


# ========== 场景 CRUD ==========


@router.get("")
async def list_scenarios(
    skip: int = 0,
    limit: int = 20,
    keyword: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_permissions("scenario:read")),
    db: AsyncSession = Depends(get_db),
):
    """获取场景列表（分页 + 搜索 + 筛选）"""
    query = select(AutoTestScenario).where(AutoTestScenario.user_id == current_user.id)
    count_query = select(func.count(AutoTestScenario.id)).where(AutoTestScenario.user_id == current_user.id)

    if keyword:
        keyword_escaped = keyword.replace("%", "\\%").replace("_", "\\_")
        query = query.where(AutoTestScenario.name.like(f"%{keyword_escaped}%", escape="\\"))
        count_query = count_query.where(AutoTestScenario.name.like(f"%{keyword_escaped}%", escape="\\"))
    if is_active is not None:
        query = query.where(AutoTestScenario.is_active == is_active)
        count_query = count_query.where(AutoTestScenario.is_active == is_active)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    step_count_subq = (
        select(
            AutoTestScenarioStep.scenario_id,
            func.count(AutoTestScenarioStep.id).label("step_count"),
        )
        .group_by(AutoTestScenarioStep.scenario_id)
        .subquery()
    )

    query = (
        query.outerjoin(step_count_subq, AutoTestScenario.id == step_count_subq.c.scenario_id)
        .add_columns(func.coalesce(step_count_subq.c.step_count, 0).label("step_count"))
        .order_by(AutoTestScenario.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    items = []
    for row in rows:
        scenario = row[0]
        items.append(
            {
                "id": scenario.id,
                "name": scenario.name,
                "description": scenario.description,
                "is_active": scenario.is_active,
                "schedule_cron": scenario.schedule_cron_expression,
                "schedule_env_id": scenario.schedule_env_id,
                "webhook_url": scenario.schedule_webhook_url,
                "webhook_token": scenario.webhook_token,
                "created_at": scenario.created_at.isoformat() if scenario.created_at else None,
                "updated_at": scenario.updated_at.isoformat() if scenario.updated_at else None,
                "step_count": row.step_count,
            }
        )

    return {"items": items, "total": total}


@router.get("/available-cases", response_model=List[dict])
async def get_available_cases(
    keyword: str = None,
    group_id: int = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取可用的接口列表（用于添加步骤时选择）"""
    query = select(AutoTestCase).where(AutoTestCase.user_id == current_user.id)
    if keyword:
        keyword_escaped = keyword.replace("%", "\\%").replace("_", "\\_")
        query = query.where(AutoTestCase.name.like(f"%{keyword_escaped}%", escape="\\"))
    if group_id:
        query = query.where(AutoTestCase.group_id == group_id)

    result = await db.execute(query.order_by(AutoTestCase.updated_at.desc()))
    cases = result.scalars().all()
    return [
        {
            "id": case.id,
            "name": case.name,
            "method": case.method,
            "url": case.url,
            "group_id": case.group_id,
        }
        for case in cases
    ]


@router.get("/{scenario_id}", response_model=AutoTestScenarioResponse)
async def get_scenario(
    scenario_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取场景详情"""
    result = await db.execute(
        select(AutoTestScenario)
        .options(selectinload(AutoTestScenario.steps).selectinload(AutoTestScenarioStep.api_case))
        .where(AutoTestScenario.id == scenario_id, AutoTestScenario.user_id == current_user.id)
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    return scenario


@router.post("", response_model=AutoTestScenarioResponse)
@audit_log(action="create", resource_type="scenario")
async def create_scenario(
    scenario: AutoTestScenarioCreate,
    request: Request,
    current_user: User = Depends(require_permissions("scenario:create")),
    db: AsyncSession = Depends(get_db),
):
    """创建场景"""
    data = scenario.model_dump()
    data["webhook_token"] = str(uuid.uuid4())
    data["user_id"] = current_user.id
    db_scenario = AutoTestScenario(**data)
    db.add(db_scenario)
    await db.commit()
    await db.refresh(db_scenario)

    result = await db.execute(
        select(AutoTestScenario)
        .options(selectinload(AutoTestScenario.steps))
        .where(AutoTestScenario.id == db_scenario.id)
    )
    return result.scalar_one()


@router.put("/{scenario_id}", response_model=AutoTestScenarioResponse)
async def update_scenario(
    scenario_id: int,
    scenario: AutoTestScenarioUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新场景"""
    result = await db.execute(
        select(AutoTestScenario).where(AutoTestScenario.id == scenario_id, AutoTestScenario.user_id == current_user.id)
    )
    db_scenario = result.scalar_one_or_none()
    if not db_scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    update_data = scenario.model_dump(exclude_unset=True)
    if not db_scenario.webhook_token and "webhook_token" not in update_data:
        update_data["webhook_token"] = str(uuid.uuid4())
    PROTECTED_FIELDS = {"id", "user_id", "created_at"}
    # 捕获变更前快照（仅记录将被更新的非保护字段）
    audit_keys = [k for k in update_data.keys() if k not in PROTECTED_FIELDS]
    before = {k: getattr(db_scenario, k, None) for k in audit_keys}
    for key, value in update_data.items():
        if key in PROTECTED_FIELDS:
            continue
        setattr(db_scenario, key, value)

    await db.commit()
    await db.refresh(db_scenario)

    # 记录变更后快照并写入审计日志（手动调用，含 before/after）
    after = {k: getattr(db_scenario, k, None) for k in audit_keys}
    await AuditService.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="update",
        resource_type="scenario",
        resource_id=scenario_id,
        resource_name=getattr(db_scenario, "name", None),
        detail={"before": before, "after": after},
        request=request,
    )

    result = await db.execute(
        select(AutoTestScenario)
        .options(selectinload(AutoTestScenario.steps).selectinload(AutoTestScenarioStep.api_case))
        .where(AutoTestScenario.id == scenario_id)
    )
    return result.scalar_one()


class ScenarioStatusUpdate(BaseModel):
    is_active: bool


@router.put("/{scenario_id}/status")
async def update_scenario_status(
    scenario_id: int,
    payload: ScenarioStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新场景启用/停用状态"""
    result = await db.execute(
        select(AutoTestScenario).where(AutoTestScenario.id == scenario_id, AutoTestScenario.user_id == current_user.id)
    )
    db_scenario = result.scalar_one_or_none()
    if not db_scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    db_scenario.is_active = payload.is_active
    await db.commit()
    await db.refresh(db_scenario)

    from fastapi_backend.services.autotest_scheduler import get_scheduler
    from fastapi_backend.services.autotest_schedule_persistence import persist_schedule_is_active_db

    sched = get_scheduler()
    task_id = f"auto_sched_{scenario_id}"
    if not db_scenario.is_active:
        try:
            sched.pause_job(task_id)
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(f"暂停定时任务失败: {e}")
        await persist_schedule_is_active_db(scenario_id, False, user_id=current_user.id)
    else:
        try:
            sched.resume_job(task_id)
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(f"恢复定时任务失败: {e}")
        await persist_schedule_is_active_db(scenario_id, True, user_id=current_user.id)

    return {"id": db_scenario.id, "is_active": db_scenario.is_active}


@router.delete("/{scenario_id}")
@audit_log(action="delete", resource_type="scenario", resource_id_param="scenario_id")
async def delete_scenario(
    scenario_id: int,
    request: Request,
    current_user: User = Depends(require_permissions("scenario:delete")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AutoTestScenario).where(AutoTestScenario.id == scenario_id, AutoTestScenario.user_id == current_user.id)
    )
    db_scenario = result.scalar_one_or_none()
    if not db_scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    try:
        from fastapi_backend.services.autotest_scheduler import remove_scheduled_task

        remove_scheduled_task(f"auto_sched_{scenario_id}")
    except Exception as e:
        import logging

        logging.getLogger(__name__).warning(f"移除定时任务失败: {e}")

    # 清理关联的执行记录
    exec_records_result = await db.execute(
        select(AutoTestScenarioExecutionRecord).where(AutoTestScenarioExecutionRecord.scenario_id == scenario_id)
    )
    for record in exec_records_result.scalars().all():
        await db.delete(record)

    # 清理关联的数据集
    dataset_result = await db.execute(select(AutoTestDataset).where(AutoTestDataset.scenario_id == scenario_id))
    for dataset in dataset_result.scalars().all():
        await db.delete(dataset)

    await db.delete(db_scenario)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        import logging

        logging.getLogger(__name__).error(f"删除场景失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="删除失败，事务已回滚")

    # 清理 JSON 套件中的 scenario_ids 引用
    try:
        from fastapi_backend.routers.autotest_suites import _suites, _suites_lock, _save_suites

        async with _suites_lock:
            for suite in _suites.values():
                if scenario_id in suite.get("scenario_ids", []):
                    suite["scenario_ids"] = [sid for sid in suite["scenario_ids"] if sid != scenario_id]
            _save_suites(_suites)
    except Exception as e:
        _logger.warning(f"清理JSON套件引用失败: {e}")
    return {"message": "删除成功"}


# ========== 场景步骤 CRUD ==========


@router.post("/{scenario_id}/steps", response_model=ScenarioStepResponse)
async def add_step(
    scenario_id: int,
    step: ScenarioStepCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """添加步骤"""
    result = await db.execute(
        select(AutoTestScenario).where(AutoTestScenario.id == scenario_id, AutoTestScenario.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="场景不存在")

    # 只有 api_request 类型需要验证 api_case_id
    if step.step_type == "api_request" or not step.step_type:
        if step.api_case_id:
            result = await db.execute(
                select(AutoTestCase).where(AutoTestCase.id == step.api_case_id, AutoTestCase.user_id == current_user.id)
            )
            if not result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="指定的接口不存在")
        else:
            raise HTTPException(status_code=400, detail="API 请求类型步骤必须指定 api_case_id")

    # 对非 api_request 类型的 step_config 进行基本校验
    step_config = step.step_config or {}
    if step.step_type == "if":
        if not step_config.get("condition"):
            raise HTTPException(status_code=400, detail="if步骤必须包含condition")
    elif step.step_type == "for":
        if not step_config.get("loop_var") or not step_config.get("items"):
            raise HTTPException(status_code=400, detail="for步骤必须包含loop_var和items")
    elif step.step_type == "group":
        if not step_config.get("steps"):
            raise HTTPException(status_code=400, detail="group步骤必须包含steps")

    db_step = AutoTestScenarioStep(
        scenario_id=scenario_id,
        api_case_id=step.api_case_id,
        step_order=step.step_order,
        is_active=step.is_active,
        variable_overrides=step.variable_overrides,
        step_type=step.step_type,
        step_config=step.step_config,
        parent_step_id=step.parent_step_id,
        pre_script=step.pre_script,
        post_script=step.post_script,
    )
    db.add(db_step)
    await db.commit()
    await db.refresh(db_step)

    result = await db.execute(
        select(AutoTestScenarioStep)
        .options(selectinload(AutoTestScenarioStep.api_case))
        .where(AutoTestScenarioStep.id == db_step.id)
    )
    return result.scalar_one()


class StepOrderItem(BaseModel):
    step_id: int
    step_order: int


@router.put("/{scenario_id}/steps/reorder")
async def reorder_steps(
    scenario_id: int,
    step_orders: List[StepOrderItem],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """批量更新步骤顺序"""
    # 先校验场景归属
    scenario_result = await db.execute(
        select(AutoTestScenario).where(
            AutoTestScenario.id == scenario_id,
            AutoTestScenario.user_id == current_user.id,
        )
    )
    if not scenario_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="场景不存在")

    # 一次性查询该场景的所有步骤，避免 N+1 查询
    steps_result = await db.execute(
        select(AutoTestScenarioStep).where(
            AutoTestScenarioStep.scenario_id == scenario_id,
        )
    )
    steps_map = {step.id: step for step in steps_result.scalars().all()}

    # 第一步：先将所有步骤设为临时负值，避免交换顺序时违反 uq_scenario_step_order 唯一约束
    for item in step_orders:
        step = steps_map.get(item.step_id)
        if step:
            step.step_order = -item.step_order - 1
    await db.flush()
    # 第二步：设为目标值
    for item in step_orders:
        step = steps_map.get(item.step_id)
        if step:
            step.step_order = item.step_order
    await db.commit()
    return {"message": "排序更新成功"}


@router.put("/{scenario_id}/steps/{step_id}", response_model=ScenarioStepResponse)
async def update_step(
    scenario_id: int,
    step_id: int,
    step: ScenarioStepUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新步骤"""
    # 先校验场景归属
    scenario_result = await db.execute(
        select(AutoTestScenario).where(
            AutoTestScenario.id == scenario_id,
            AutoTestScenario.user_id == current_user.id,
        )
    )
    if not scenario_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="场景不存在")

    result = await db.execute(
        select(AutoTestScenarioStep)
        .options(selectinload(AutoTestScenarioStep.api_case))
        .where(AutoTestScenarioStep.id == step_id, AutoTestScenarioStep.scenario_id == scenario_id)
    )
    db_step = result.scalar_one_or_none()
    if not db_step:
        raise HTTPException(status_code=404, detail="步骤不存在")

    update_data = step.model_dump(exclude_unset=True)
    # 如果更新了 api_case_id，校验新用例归属当前用户
    if "api_case_id" in update_data and update_data["api_case_id"] is not None:
        case_result = await db.execute(
            select(AutoTestCase).where(
                AutoTestCase.id == update_data["api_case_id"],
                AutoTestCase.user_id == current_user.id,
            )
        )
        if not case_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="指定的接口不存在或无权访问")
    for key, value in update_data.items():
        setattr(db_step, key, value)

    await db.commit()
    await db.refresh(db_step)
    return db_step


@router.delete("/{scenario_id}/steps/{step_id}")
async def delete_step(
    scenario_id: int,
    step_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除步骤"""
    # 先校验场景归属
    scenario_result = await db.execute(
        select(AutoTestScenario).where(
            AutoTestScenario.id == scenario_id,
            AutoTestScenario.user_id == current_user.id,
        )
    )
    if not scenario_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="场景不存在")

    result = await db.execute(
        select(AutoTestScenarioStep).where(
            AutoTestScenarioStep.id == step_id, AutoTestScenarioStep.scenario_id == scenario_id
        )
    )
    db_step = result.scalar_one_or_none()
    if not db_step:
        raise HTTPException(status_code=404, detail="步骤不存在")

    await db.delete(db_step)
    await db.flush()

    reorder_result = await db.execute(
        select(AutoTestScenarioStep)
        .where(AutoTestScenarioStep.scenario_id == scenario_id)
        .order_by(AutoTestScenarioStep.step_order.asc(), AutoTestScenarioStep.id.asc())
    )
    for index, step in enumerate(reorder_result.scalars().all()):
        step.step_order = index
    await db.commit()
    return {"message": "删除成功"}


# ========== 数据集管理 ==========


@router.get("/{scenario_id}/dataset", response_model=Optional[AutoTestDatasetResponse])
async def get_scenario_dataset(
    scenario_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取场景的数据集"""
    # 先校验场景归属
    scenario_result = await db.execute(
        select(AutoTestScenario).where(
            AutoTestScenario.id == scenario_id,
            AutoTestScenario.user_id == current_user.id,
        )
    )
    if not scenario_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="场景不存在")

    result = await db.execute(select(AutoTestDataset).where(AutoTestDataset.scenario_id == scenario_id))
    dataset = result.scalar_one_or_none()
    return dataset


@router.post("/{scenario_id}/dataset", response_model=AutoTestDatasetResponse)
async def create_or_update_dataset(
    scenario_id: int,
    dataset_data: AutoTestDatasetBase,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建或更新场景的数据集（Upsert）"""
    result = await db.execute(
        select(AutoTestScenario).where(AutoTestScenario.id == scenario_id, AutoTestScenario.user_id == current_user.id)
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    result = await db.execute(select(AutoTestDataset).where(AutoTestDataset.scenario_id == scenario_id))
    existing_dataset = result.scalar_one_or_none()

    if existing_dataset:
        # 仅更新显式传入的字段，避免未传 description 时用 None 覆盖已有值
        update_data = dataset_data.model_dump(exclude_unset=True)
        if "name" in update_data:
            existing_dataset.name = update_data["name"]
        if "data_matrix" in update_data:
            existing_dataset.data_matrix = update_data["data_matrix"]
        if "description" in update_data:
            existing_dataset.description = update_data["description"]
        await db.commit()
        await db.refresh(existing_dataset)
        return existing_dataset
    else:
        new_dataset = AutoTestDataset(
            scenario_id=scenario_id,
            name=dataset_data.name,
            data_matrix=dataset_data.data_matrix.model_dump(),
            description=dataset_data.description,
        )
        db.add(new_dataset)
        await db.commit()
        await db.refresh(new_dataset)
        return new_dataset


@router.delete("/{scenario_id}/dataset")
async def delete_dataset(
    scenario_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除场景的数据集"""
    # 先校验场景归属
    scenario_result = await db.execute(
        select(AutoTestScenario).where(
            AutoTestScenario.id == scenario_id,
            AutoTestScenario.user_id == current_user.id,
        )
    )
    if not scenario_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="场景不存在")

    result = await db.execute(select(AutoTestDataset).where(AutoTestDataset.scenario_id == scenario_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")

    await db.delete(dataset)
    await db.commit()
    return {"message": "数据集已删除"}


@router.post("/{scenario_id}/dataset/parse-file")
async def parse_dataset_file(
    scenario_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """解析上传的 CSV/Excel 文件，返回数据矩阵"""
    import csv
    import io

    # 验证场景归属
    scenario_result = await db.execute(
        select(AutoTestScenario).where(
            AutoTestScenario.id == scenario_id,
            AutoTestScenario.user_id == current_user.id,
        )
    )
    if not scenario_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="场景不存在")

    content = await file.read()

    try:
        filename = file.filename or ""
        if filename.endswith(".csv"):
            decoded_content = content.decode("utf-8")
            reader = csv.reader(io.StringIO(decoded_content))
            rows = list(reader)
        elif filename.endswith((".xlsx", ".xls")):
            import openpyxl

            wb = openpyxl.load_workbook(io.BytesIO(content))
            ws = wb.active
            rows = list(ws.values)
        else:
            raise HTTPException(status_code=400, detail="仅支持 CSV 或 Excel 文件")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")

    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="文件至少需要包含列名和一行数据")

    columns = [str(col) if col is not None else f"column_{i}" for i, col in enumerate(rows[0])]
    data_rows = rows[1:]

    return {"columns": columns, "rows": data_rows, "row_count": len(data_rows)}


# ========== Pytest 数据驱动执行 ==========


@router.post("/{scenario_id}/run-pytest")
async def run_scenario_with_pytest(
    scenario_id: int,
    request: InlineScenarioExecutionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """使用 Pytest 引擎执行数据驱动测试"""
    # 检查场景是否存在
    result = await db.execute(
        select(AutoTestScenario).where(AutoTestScenario.id == scenario_id, AutoTestScenario.user_id == current_user.id)
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    try:
        from fastapi_backend.services.autotest_pytest_engine import run_scenario_pytest
        import asyncio

        exec_result = await asyncio.to_thread(
            run_scenario_pytest,
            scenario_id=scenario_id,
            scenario_name=scenario.name,
            steps=request.steps,
            data_matrix=request.data_matrix.model_dump(),
            env_vars=request.env_vars,
        )
        return {
            "success": exec_result["success"],
            "total_iterations": exec_result["total_iterations"],
            "passed": exec_result.get("passed", 0),
            "failed": exec_result.get("failed", 0),
            "duration": exec_result["duration"],
            "report_url": exec_result.get("report_url"),
            "error": exec_result.get("error"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")
