"""
测试数据工厂路由

路径前缀: /api/auto-test/data-factory
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import (
    TestDataTemplate,
    TestDataTemplateField,
    AutoTestScenario,
    AutoTestDataset,
)
from fastapi_backend.models.models import User
from fastapi_backend.schemas.autotest import (
    TestDataTemplateCreate,
    TestDataTemplateUpdate,
    TestDataTemplateResponse,
    GeneratedDatasetResponse,
)

router = APIRouter(
    prefix="/api/auto-test/data-factory",
    tags=["AutoTest-数据工厂"],
)


@router.get("/templates", response_model=List[TestDataTemplateResponse])
async def list_templates(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TestDataTemplate)
        .options(selectinload(TestDataTemplate.fields))
        .where(TestDataTemplate.user_id == current_user.id)
        .order_by(TestDataTemplate.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/templates/{template_id}", response_model=TestDataTemplateResponse)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TestDataTemplate)
        .options(selectinload(TestDataTemplate.fields))
        .where(TestDataTemplate.id == template_id, TestDataTemplate.user_id == current_user.id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.post("/templates", response_model=TestDataTemplateResponse)
async def create_template(
    data: TestDataTemplateCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if data.scenario_id:
        scenario_check = await db.execute(
            select(AutoTestScenario).where(
                AutoTestScenario.id == data.scenario_id,
                AutoTestScenario.user_id == current_user.id,
            )
        )
        if not scenario_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"关联的场景(ID={data.scenario_id})不存在")

    template = TestDataTemplate(
        name=data.name,
        description=data.description,
        user_id=current_user.id,
        scenario_id=data.scenario_id,
        row_count=data.row_count,
    )
    db.add(template)
    await db.flush()

    for idx, field_data in enumerate(data.fields):
        field = TestDataTemplateField(
            template_id=template.id,
            field_name=field_data.field_name,
            field_label=field_data.field_label,
            rule_type=field_data.rule_type,
            rule_config=field_data.rule_config,
            sort_order=field_data.sort_order or idx,
        )
        db.add(field)

    await db.commit()
    await db.refresh(template)

    result = await db.execute(
        select(TestDataTemplate)
        .options(selectinload(TestDataTemplate.fields))
        .where(TestDataTemplate.id == template.id)
    )
    return result.scalar_one()


@router.put("/templates/{template_id}", response_model=TestDataTemplateResponse)
async def update_template(
    template_id: int,
    data: TestDataTemplateUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TestDataTemplate)
        .options(selectinload(TestDataTemplate.fields))
        .where(TestDataTemplate.id == template_id, TestDataTemplate.user_id == current_user.id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if data.name is not None:
        template.name = data.name
    if data.description is not None:
        template.description = data.description
    if data.scenario_id is not None:
        if data.scenario_id:
            scenario_check = await db.execute(
                select(AutoTestScenario).where(
                    AutoTestScenario.id == data.scenario_id,
                    AutoTestScenario.user_id == current_user.id,
                )
            )
            if not scenario_check.scalar_one_or_none():
                raise HTTPException(status_code=400, detail=f"关联的场景(ID={data.scenario_id})不存在")
        template.scenario_id = data.scenario_id
    if data.row_count is not None:
        template.row_count = data.row_count

    if data.fields is not None:
        for field in template.fields:
            await db.delete(field)
        await db.flush()
        for idx, field_data in enumerate(data.fields):
            field = TestDataTemplateField(
                template_id=template.id,
                field_name=field_data.field_name,
                field_label=field_data.field_label,
                rule_type=field_data.rule_type,
                rule_config=field_data.rule_config,
                sort_order=field_data.sort_order or idx,
            )
            db.add(field)

    await db.commit()
    await db.refresh(template)

    result = await db.execute(
        select(TestDataTemplate)
        .options(selectinload(TestDataTemplate.fields))
        .where(TestDataTemplate.id == template_id)
    )
    return result.scalar_one()


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TestDataTemplate).where(TestDataTemplate.id == template_id, TestDataTemplate.user_id == current_user.id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    await db.delete(template)
    await db.commit()
    return {"message": "模板已删除"}


@router.post("/templates/{template_id}/preview")
async def preview_template(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TestDataTemplate)
        .options(selectinload(TestDataTemplate.fields))
        .where(TestDataTemplate.id == template_id, TestDataTemplate.user_id == current_user.id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    fields_data = [
        {
            "field_name": f.field_name,
            "rule_type": f.rule_type,
            "rule_config": f.rule_config or {},
        }
        for f in template.fields
    ]

    from fastapi_backend.services.autotest_data_factory_service import DataFactoryEngine

    engine = DataFactoryEngine()
    result_data = engine.generate_preview(fields_data, row_count=template.row_count)
    return {
        "template_id": template_id,
        "template_name": template.name,
        "columns": result_data["columns"],
        "rows": result_data["rows"],
        "row_count": len(result_data["rows"]),
    }


@router.post("/templates/{template_id}/generate")
async def generate_dataset(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TestDataTemplate)
        .options(selectinload(TestDataTemplate.fields))
        .where(TestDataTemplate.id == template_id, TestDataTemplate.user_id == current_user.id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    fields_data = [
        {
            "field_name": f.field_name,
            "rule_type": f.rule_type,
            "rule_config": f.rule_config or {},
        }
        for f in template.fields
    ]

    from fastapi_backend.services.autotest_data_factory_service import DataFactoryEngine

    engine = DataFactoryEngine()
    generated = engine.generate_dataset(fields_data, row_count=template.row_count)

    if template.scenario_id:
        result = await db.execute(
            select(AutoTestScenario).where(
                AutoTestScenario.id == template.scenario_id, AutoTestScenario.user_id == current_user.id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=400, detail=f"关联的场景(ID={template.scenario_id})不存在，请先绑定有效场景"
            )

        result = await db.execute(select(AutoTestDataset).where(AutoTestDataset.scenario_id == template.scenario_id))
        existing = result.scalar_one_or_none()
        if existing:
            existing.name = f"{template.name}_数据集"
            existing.data_matrix = {"columns": generated["columns"], "rows": generated["rows"]}
        else:
            dataset = AutoTestDataset(
                scenario_id=template.scenario_id,
                name=f"{template.name}_数据集",
                data_matrix={"columns": generated["columns"], "rows": generated["rows"]},
            )
            db.add(dataset)
        await db.commit()
        await db.refresh(existing or dataset)
        dataset_id = (existing or dataset).id
    else:
        dataset_id = None

    return GeneratedDatasetResponse(
        dataset_id=dataset_id or 0,
        name=f"{template.name}_数据集",
        columns=generated["columns"],
        rows=generated["rows"],
        row_count=len(generated["rows"]),
    )


@router.post("/datasets/{dataset_id}/bind-scenario/{scenario_id}")
async def bind_dataset_to_scenario(
    dataset_id: int,
    scenario_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AutoTestScenario).where(AutoTestScenario.id == scenario_id, AutoTestScenario.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="场景不存在")

    result = await db.execute(
        select(AutoTestDataset)
        .join(AutoTestScenario, AutoTestDataset.scenario_id == AutoTestScenario.id)
        .where(AutoTestDataset.id == dataset_id, AutoTestScenario.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")

    dataset.scenario_id = scenario_id
    await db.commit()
    return {"message": "数据集已绑定到场景", "dataset_id": dataset_id, "scenario_id": scenario_id}


@router.post("/datasets/{dataset_id}/run")
async def run_dataset_driven(
    dataset_id: int,
    payload: Dict[str, Any] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AutoTestDataset)
        .options(selectinload(AutoTestDataset.scenario).selectinload(AutoTestScenario.steps))
        .join(AutoTestScenario, AutoTestDataset.scenario_id == AutoTestScenario.id)
        .where(AutoTestDataset.id == dataset_id, AutoTestScenario.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")
    if not dataset.scenario or dataset.scenario_id <= 0:
        raise HTTPException(status_code=400, detail="数据集未绑定到有效场景")

    env_id = payload.get("env_id") if payload else None

    from fastapi_backend.services.autotest_scenario_runner import run_scenario_data_driven

    exec_result = await run_scenario_data_driven(
        scenario_id=dataset.scenario_id,
        env_id=env_id,
        user_id=current_user.id,
    )
    return {
        "success": exec_result.get("failed_iterations", 0) == 0,
        "total_iterations": exec_result.get("total_iterations", 0),
        "success_iterations": exec_result.get("success_iterations", 0),
        "failed_iterations": exec_result.get("failed_iterations", 0),
        "total_duration": exec_result.get("total_duration", 0),
    }


@router.get("/scenarios")
async def list_scenarios_for_factory(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AutoTestScenario)
        .where(AutoTestScenario.user_id == current_user.id)
        .order_by(AutoTestScenario.created_at.desc())
    )
    scenarios = result.scalars().all()
    return [{"id": s.id, "name": s.name, "description": s.description} for s in scenarios]


@router.get("/rule-types")
async def get_rule_types(current_user: User = Depends(get_current_active_user)):
    return {
        "rule_types": [
            {"type": "fixed", "label": "固定值", "config_fields": ["value"]},
            {"type": "enum", "label": "枚举值", "config_fields": ["options"]},
            {"type": "increment", "label": "递增数字", "config_fields": ["prefix", "start", "step"]},
            {"type": "uuid", "label": "UUID", "config_fields": ["version"]},
            {"type": "timestamp", "label": "时间戳", "config_fields": ["format", "offset_seconds"]},
            {"type": "date_offset", "label": "日期偏移", "config_fields": ["format", "offset_days"]},
            {"type": "phone", "label": "随机手机号", "config_fields": ["prefix"]},
            {"type": "email", "label": "随机邮箱", "config_fields": ["domains", "username_prefix"]},
            {"type": "username", "label": "随机用户名", "config_fields": ["prefixes", "suffix_length"]},
            {"type": "env_ref", "label": "引用环境变量", "config_fields": ["variable_name", "default"]},
        ]
    }
