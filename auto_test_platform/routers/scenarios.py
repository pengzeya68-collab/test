"""
场景管理路由
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from auto_test_platform.database import get_db
from auto_test_platform.models import TestScenario, ScenarioStep, ApiCase, TestDataset
from auto_test_platform.schemas import (
    TestScenarioCreate, TestScenarioUpdate, TestScenarioResponse,
    ScenarioStepCreate, ScenarioStepUpdate, ScenarioStepResponse,
    TestDatasetCreate, TestDatasetUpdate, TestDatasetResponse,
    DataMatrix
)

router = APIRouter(prefix="/scenarios", tags=["场景管理"])


# ========== 场景 CRUD ==========

@router.get("/", response_model=List[TestScenarioResponse])
async def list_scenarios(db: AsyncSession = Depends(get_db)):
    """获取所有场景"""
    result = await db.execute(
        select(TestScenario)
        .options(selectinload(TestScenario.steps).selectinload(ScenarioStep.api_case))
        .order_by(TestScenario.created_at.desc())
    )
    scenarios = result.scalars().all()
    return scenarios


# ========== 获取可用的接口列表（用于添加步骤时选择） ==========

@router.get("/available-cases", response_model=List[dict])
async def get_available_cases(
    keyword: str = None,
    group_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    """获取可用的接口列表（用于添加步骤时选择）"""
    query = select(ApiCase)

    if keyword:
        query = query.where(ApiCase.name.like(f"%{keyword}%"))
    if group_id:
        query = query.where(ApiCase.group_id == group_id)

    result = await db.execute(query.order_by(ApiCase.updated_at.desc()))
    cases = result.scalars().all()

    return [
        {
            "id": case.id,
            "name": case.name,
            "method": case.method,
            "url": case.url,
            "group_id": case.group_id
        }
        for case in cases
    ]


@router.get("/{scenario_id}", response_model=TestScenarioResponse)
async def get_scenario(scenario_id: int, db: AsyncSession = Depends(get_db)):
    """获取场景详情"""
    result = await db.execute(
        select(TestScenario)
        .options(selectinload(TestScenario.steps).selectinload(ScenarioStep.api_case))
        .where(TestScenario.id == scenario_id)
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    return scenario


@router.post("/", response_model=TestScenarioResponse)
async def create_scenario(scenario: TestScenarioCreate, db: AsyncSession = Depends(get_db)):
    """创建场景"""
    db_scenario = TestScenario(**scenario.model_dump())
    db.add(db_scenario)
    await db.commit()
    await db.refresh(db_scenario)

    # 重新查询以获取完整数据
    result = await db.execute(
        select(TestScenario)
        .options(selectinload(TestScenario.steps))
        .where(TestScenario.id == db_scenario.id)
    )
    return result.scalar_one()


@router.put("/{scenario_id}", response_model=TestScenarioResponse)
async def update_scenario(scenario_id: int, scenario: TestScenarioUpdate, db: AsyncSession = Depends(get_db)):
    """更新场景"""
    result = await db.execute(
        select(TestScenario).where(TestScenario.id == scenario_id)
    )
    db_scenario = result.scalar_one_or_none()
    if not db_scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    update_data = scenario.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_scenario, key, value)

    await db.commit()
    await db.refresh(db_scenario)

    # 重新查询以获取完整数据
    result = await db.execute(
        select(TestScenario)
        .options(selectinload(TestScenario.steps).selectinload(ScenarioStep.api_case))
        .where(TestScenario.id == scenario_id)
    )
    return result.scalar_one()


@router.delete("/{scenario_id}")
async def delete_scenario(scenario_id: int, db: AsyncSession = Depends(get_db)):
    """删除场景"""
    result = await db.execute(
        select(TestScenario).where(TestScenario.id == scenario_id)
    )
    db_scenario = result.scalar_one_or_none()
    if not db_scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    await db.delete(db_scenario)
    await db.commit()
    return {"message": "删除成功"}


# ========== 场景步骤 CRUD ==========

@router.post("/{scenario_id}/steps", response_model=ScenarioStepResponse)
async def add_step(scenario_id: int, step: ScenarioStepCreate, db: AsyncSession = Depends(get_db)):
    """添加步骤"""
    # 检查场景是否存在
    result = await db.execute(
        select(TestScenario).where(TestScenario.id == scenario_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="场景不存在")

    # 检查接口是否存在
    result = await db.execute(
        select(ApiCase).where(ApiCase.id == step.api_case_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="指定的接口不存在")

    db_step = ScenarioStep(
        scenario_id=scenario_id,
        api_case_id=step.api_case_id,
        step_order=step.step_order,
        is_active=step.is_active,
        variable_overrides=step.variable_overrides
    )
    db.add(db_step)
    await db.commit()
    await db.refresh(db_step)

    # 返回包含接口详情的步骤
    result = await db.execute(
        select(ScenarioStep)
        .options(selectinload(ScenarioStep.api_case))
        .where(ScenarioStep.id == db_step.id)
    )
    return result.scalar_one()


@router.put("/{scenario_id}/steps/{step_id}", response_model=ScenarioStepResponse)
async def update_step(scenario_id: int, step_id: int, step: ScenarioStepUpdate, db: AsyncSession = Depends(get_db)):
    """更新步骤"""
    result = await db.execute(
        select(ScenarioStep)
        .options(selectinload(ScenarioStep.api_case))
        .where(ScenarioStep.id == step_id, ScenarioStep.scenario_id == scenario_id)
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
        select(ScenarioStep).where(ScenarioStep.id == step_id, ScenarioStep.scenario_id == scenario_id)
    )
    db_step = result.scalar_one_or_none()
    if not db_step:
        raise HTTPException(status_code=404, detail="步骤不存在")

    await db.delete(db_step)
    await db.commit()
    return {"message": "删除成功"}


@router.put("/{scenario_id}/steps/reorder")
async def reorder_steps(scenario_id: int, step_orders: List[dict], db: AsyncSession = Depends(get_db)):
    """
    批量更新步骤顺序
    step_orders: [{"step_id": 1, "step_order": 0}, {"step_id": 2, "step_order": 1}, ...]
    """
    for item in step_orders:
        result = await db.execute(
            select(ScenarioStep).where(
                ScenarioStep.id == item["step_id"],
                ScenarioStep.scenario_id == scenario_id
            )
        )
        db_step = result.scalar_one_or_none()
        if db_step:
            db_step.step_order = item["step_order"]

    await db.commit()
    return {"message": "排序更新成功"}


# ========== 数据集管理 ==========

@router.get("/{scenario_id}/dataset", response_model=Optional[TestDatasetResponse])
async def get_scenario_dataset(scenario_id: int, db: AsyncSession = Depends(get_db)):
    """获取场景的数据集"""
    result = await db.execute(
        select(TestDataset).where(TestDataset.scenario_id == scenario_id)
    )
    dataset = result.scalar_one_or_none()
    return dataset


@router.post("/{scenario_id}/dataset", response_model=TestDatasetResponse)
async def create_or_update_dataset(
    scenario_id: int,
    dataset_data: TestDatasetCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建或更新场景的数据集（Upsert）"""
    # 检查场景是否存在
    result = await db.execute(
        select(TestScenario).where(TestScenario.id == scenario_id)
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    # 检查是否已存在数据集
    result = await db.execute(
        select(TestDataset).where(TestDataset.scenario_id == scenario_id)
    )
    existing_dataset = result.scalar_one_or_none()

    if existing_dataset:
        # 更新
        existing_dataset.name = dataset_data.name
        existing_dataset.data_matrix = dataset_data.data_matrix.model_dump()
        existing_dataset.description = dataset_data.description
        await db.commit()
        await db.refresh(existing_dataset)
        return existing_dataset
    else:
        # 创建
        new_dataset = TestDataset(
            scenario_id=scenario_id,
            name=dataset_data.name,
            data_matrix=dataset_data.data_matrix.model_dump(),
            description=dataset_data.description
        )
        db.add(new_dataset)
        await db.commit()
        await db.refresh(new_dataset)
        return new_dataset


@router.delete("/{scenario_id}/dataset")
async def delete_dataset(scenario_id: int, db: AsyncSession = Depends(get_db)):
    """删除场景的数据集"""
    result = await db.execute(
        select(TestDataset).where(TestDataset.scenario_id == scenario_id)
    )
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
    db: AsyncSession = Depends(get_db)
):
    """
    解析上传的 CSV/Excel 文件，返回数据矩阵
    前端上传文件，后端解析并返回结构化数据
    """
    import csv
    import io
    import openpyxl

    content = await file.read()

    try:
        if file.filename.endswith('.csv'):
            # 解析 CSV
            decoded_content = content.decode('utf-8')
            reader = csv.reader(io.StringIO(decoded_content))
            rows = list(reader)
        elif file.filename.endswith(('.xlsx', '.xls')):
            # 解析 Excel
            wb = openpyxl.load_workbook(io.BytesIO(content))
            ws = wb.active
            rows = list(ws.values)
        else:
            raise HTTPException(status_code=400, detail="仅支持 CSV 或 Excel 文件")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")

    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="文件至少需要包含列名和一行数据")

    # 第一行作为列名（变量名）
    columns = [str(col) if col is not None else f"column_{i}" for i, col in enumerate(rows[0])]
    data_rows = rows[1:]

    return {
        "columns": columns,
        "rows": data_rows,
        "row_count": len(data_rows)
    }


# ========== Pytest 数据驱动执行 ==========

class InlineScenarioExecutionRequest(BaseModel):
    """内联场景执行请求（前端直接发送场景数据，不从数据库读取）"""
    steps: List[dict] = Field(..., description="步骤列表")
    data_matrix: DataMatrix = Field(..., description="数据矩阵")
    env_vars: Optional[Dict[str, Any]] = Field(default_factory=dict, description="环境变量")


@router.post("/{scenario_id}/run-pytest")
async def run_scenario_with_pytest(
    scenario_id: int,
    request: InlineScenarioExecutionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    使用 Pytest 引擎执行数据驱动测试

    接收前端传来的内联场景数据，直接执行，无需从数据库读取完整场景

    请求体格式：
    {
        "steps": [
            {
                "step_order": 1,
                "name": "登录",
                "method": "POST",
                "url": "{{base_url}}/api/login",
                "headers": {"Content-Type": "application/json"},
                "payload": {"username": "{{username}}", "password": "{{password}}"},
                "assert_rules": {"status_code": 200},
                "extractors": [
                    {"variableName": "token", "expression": "token", "extractorType": "jsonpath"}
                ]
            }
        ],
        "data_matrix": {
            "columns": ["username", "password"],
            "rows": [["admin", "admin123"], ["test", "test123"]]
        },
        "env_vars": {"base_url": "http://localhost:3000"}
    }
    """
    from services.pytest_engine import run_scenario_pytest

    # 检查场景是否存在（仅用于获取名称）
    result = await db.execute(
        select(TestScenario).where(TestScenario.id == scenario_id)
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    # 执行测试
    try:
        result = run_scenario_pytest(
            scenario_id=scenario_id,
            scenario_name=scenario.name,
            steps=request.steps,
            data_matrix=request.data_matrix.model_dump(),
            env_vars=request.env_vars
        )

        return {
            "success": result["success"],
            "total_iterations": result["total_iterations"],
            "passed": result.get("passed", 0),
            "failed": result.get("failed", 0),
            "duration": result["duration"],
            "report_url": result.get("report_url"),
            "error": result.get("error")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")
