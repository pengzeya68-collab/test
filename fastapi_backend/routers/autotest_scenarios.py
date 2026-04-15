"""
AutoTest 统一路由 - 场景管理

路径前缀: /api/auto-test/scenarios
映射原 auto_test_platform 的 /api/scenarios
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.autotest import (
    AutoTestScenario,
    AutoTestScenarioStep,
    AutoTestCase,
    AutoTestDataset,
)
from fastapi_backend.schemas.autotest import (
    AutoTestScenarioCreate,
    AutoTestScenarioUpdate,
    AutoTestScenarioResponse,
    ScenarioStepCreate,
    ScenarioStepUpdate,
    ScenarioStepResponse,
    AutoTestDatasetCreate,
    AutoTestDatasetUpdate,
    AutoTestDatasetResponse,
    DataMatrix,
    InlineScenarioExecutionRequest,
)

router = APIRouter(prefix="/api/auto-test/scenarios", tags=["AutoTest-场景"], dependencies=[Depends(get_current_user)])


# ========== 场景 CRUD ==========

@router.get("/", response_model=List[AutoTestScenarioResponse])
async def list_scenarios(db: AsyncSession = Depends(get_db)):
    """获取所有场景"""
    result = await db.execute(
        select(AutoTestScenario)
        .options(selectinload(AutoTestScenario.steps).selectinload(AutoTestScenarioStep.api_case))
        .order_by(AutoTestScenario.created_at.desc())
    )
    scenarios = result.scalars().all()
    return scenarios


@router.get("/available-cases", response_model=List[dict])
async def get_available_cases(
    keyword: str = None,
    group_id: int = None,
    db: AsyncSession = Depends(get_db),
):
    """获取可用的接口列表（用于添加步骤时选择）"""
    query = select(AutoTestCase)
    if keyword:
        query = query.where(AutoTestCase.name.like(f"%{keyword}%"))
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
async def get_scenario(scenario_id: int, db: AsyncSession = Depends(get_db)):
    """获取场景详情"""
    result = await db.execute(
        select(AutoTestScenario)
        .options(selectinload(AutoTestScenario.steps).selectinload(AutoTestScenarioStep.api_case))
        .where(AutoTestScenario.id == scenario_id)
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    return scenario


@router.post("/", response_model=AutoTestScenarioResponse)
async def create_scenario(scenario: AutoTestScenarioCreate, db: AsyncSession = Depends(get_db)):
    """创建场景"""
    db_scenario = AutoTestScenario(**scenario.model_dump())
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
    db: AsyncSession = Depends(get_db),
):
    """更新场景"""
    result = await db.execute(select(AutoTestScenario).where(AutoTestScenario.id == scenario_id))
    db_scenario = result.scalar_one_or_none()
    if not db_scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    update_data = scenario.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_scenario, key, value)

    await db.commit()
    await db.refresh(db_scenario)

    result = await db.execute(
        select(AutoTestScenario)
        .options(selectinload(AutoTestScenario.steps).selectinload(AutoTestScenarioStep.api_case))
        .where(AutoTestScenario.id == scenario_id)
    )
    return result.scalar_one()


@router.put("/{scenario_id}/status")
async def update_scenario_status(
    scenario_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    """更新场景启用/停用状态"""
    result = await db.execute(select(AutoTestScenario).where(AutoTestScenario.id == scenario_id))
    db_scenario = result.scalar_one_or_none()
    if not db_scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    is_active = payload.get("is_active")
    if is_active is None:
        raise HTTPException(status_code=400, detail="缺少 is_active 参数")

    db_scenario.is_active = bool(is_active)
    await db.commit()
    await db.refresh(db_scenario)

    if not db_scenario.is_active:
        from fastapi_backend.services.autotest_scheduler import get_scheduler
        sched = get_scheduler()
        task_id = f"auto_sched_{scenario_id}"
        try:
            sched.pause_job(task_id)
        except Exception:
            pass

    return {"id": db_scenario.id, "is_active": db_scenario.is_active}


@router.delete("/{scenario_id}")
async def delete_scenario(scenario_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AutoTestScenario).where(AutoTestScenario.id == scenario_id))
    db_scenario = result.scalar_one_or_none()
    if not db_scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    try:
        from fastapi_backend.services.autotest_scheduler import remove_scheduled_task
        remove_scheduled_task(str(scenario_id))
    except Exception:
        pass

    await db.delete(db_scenario)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="删除失败，事务已回滚")
    return {"message": "删除成功"}


# ========== 场景步骤 CRUD ==========

@router.post("/{scenario_id}/steps", response_model=ScenarioStepResponse)
async def add_step(
    scenario_id: int,
    step: ScenarioStepCreate,
    db: AsyncSession = Depends(get_db),
):
    """添加步骤"""
    result = await db.execute(select(AutoTestScenario).where(AutoTestScenario.id == scenario_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="场景不存在")

    result = await db.execute(select(AutoTestCase).where(AutoTestCase.id == step.api_case_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="指定的接口不存在")

    db_step = AutoTestScenarioStep(
        scenario_id=scenario_id,
        api_case_id=step.api_case_id,
        step_order=step.step_order,
        is_active=step.is_active,
        variable_overrides=step.variable_overrides,
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


@router.put("/{scenario_id}/steps/{step_id}", response_model=ScenarioStepResponse)
async def update_step(
    scenario_id: int,
    step_id: int,
    step: ScenarioStepUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新步骤"""
    result = await db.execute(
        select(AutoTestScenarioStep)
        .options(selectinload(AutoTestScenarioStep.api_case))
        .where(AutoTestScenarioStep.id == step_id, AutoTestScenarioStep.scenario_id == scenario_id)
    )
    db_step = result.scalar_one_or_none()
    if not db_step:
        raise HTTPException(status_code=404, detail="步骤不存在")

    update_data = step.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_step, key, value)

    await db.commit()
    await db.refresh(db_step)
    return db_step


@router.delete("/{scenario_id}/steps/{step_id}")
async def delete_step(scenario_id: int, step_id: int, db: AsyncSession = Depends(get_db)):
    """删除步骤"""
    result = await db.execute(
        select(AutoTestScenarioStep).where(
            AutoTestScenarioStep.id == step_id, AutoTestScenarioStep.scenario_id == scenario_id
        )
    )
    db_step = result.scalar_one_or_none()
    if not db_step:
        raise HTTPException(status_code=404, detail="步骤不存在")

    await db.delete(db_step)
    await db.commit()
    return {"message": "删除成功"}


@router.put("/{scenario_id}/steps/reorder")
async def reorder_steps(
    scenario_id: int,
    step_orders: List[dict],
    db: AsyncSession = Depends(get_db),
):
    """批量更新步骤顺序"""
    for item in step_orders:
        result = await db.execute(
            select(AutoTestScenarioStep).where(
                AutoTestScenarioStep.id == item["step_id"],
                AutoTestScenarioStep.scenario_id == scenario_id,
            )
        )
        db_step = result.scalar_one_or_none()
        if db_step:
            db_step.step_order = item["step_order"]

    await db.commit()
    return {"message": "排序更新成功"}


# ========== 数据集管理 ==========

@router.get("/{scenario_id}/dataset", response_model=Optional[AutoTestDatasetResponse])
async def get_scenario_dataset(scenario_id: int, db: AsyncSession = Depends(get_db)):
    """获取场景的数据集"""
    result = await db.execute(select(AutoTestDataset).where(AutoTestDataset.scenario_id == scenario_id))
    dataset = result.scalar_one_or_none()
    return dataset


@router.post("/{scenario_id}/dataset", response_model=AutoTestDatasetResponse)
async def create_or_update_dataset(
    scenario_id: int,
    dataset_data: AutoTestDatasetCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建或更新场景的数据集（Upsert）"""
    result = await db.execute(select(AutoTestScenario).where(AutoTestScenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    result = await db.execute(select(AutoTestDataset).where(AutoTestDataset.scenario_id == scenario_id))
    existing_dataset = result.scalar_one_or_none()

    if existing_dataset:
        existing_dataset.name = dataset_data.name
        existing_dataset.data_matrix = dataset_data.data_matrix.model_dump()
        existing_dataset.description = dataset_data.description
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
async def delete_dataset(scenario_id: int, db: AsyncSession = Depends(get_db)):
    """删除场景的数据集"""
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
    db: AsyncSession = Depends(get_db),
):
    """解析上传的 CSV/Excel 文件，返回数据矩阵"""
    import csv
    import io

    content = await file.read()

    try:
        if file.filename.endswith('.csv'):
            decoded_content = content.decode('utf-8')
            reader = csv.reader(io.StringIO(decoded_content))
            rows = list(reader)
        elif file.filename.endswith(('.xlsx', '.xls')):
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
    db: AsyncSession = Depends(get_db),
):
    """使用 Pytest 引擎执行数据驱动测试"""
    # 检查场景是否存在
    result = await db.execute(select(AutoTestScenario).where(AutoTestScenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    try:
        from fastapi_backend.services.autotest_pytest_engine import run_scenario_pytest
        exec_result = run_scenario_pytest(
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")
