from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import json

from auto_test_platform.database import get_session
from auto_test_platform.models import ApiGroup, ApiCase

router = APIRouter(prefix="/import", tags=["导入导出"])

def extract_postman_cases(items, target_group_id, current_group_id=None):
    cases = []
    for item in items:
        # 如果是文件夹，可以选择递归创建 ApiGroup，为了简化，目前所有接口放到指定的 target_group_id 下
        if "item" in item:
            cases.extend(extract_postman_cases(item["item"], target_group_id, current_group_id))
        elif "request" in item:
            req = item["request"]
            method = req.get("method", "GET")
            url = ""
            if isinstance(req.get("url"), dict):
                url = req["url"].get("raw", "")
            elif isinstance(req.get("url"), str):
                url = req["url"]
            
            name = item.get("name", "未命名接口")
            
            headers = []
            for h in req.get("header", []):
                headers.append({"key": h.get("key", ""), "value": h.get("value", "")})
            
            body_type = "none"
            payload = ""
            if "body" in req:
                if req["body"].get("mode") == "raw":
                    body_type = "raw"
                    payload = req["body"].get("raw", "")
                elif req["body"].get("mode") == "formdata":
                    body_type = "form-data"
            
            cases.append({
                "group_id": target_group_id,
                "name": name,
                "method": method,
                "url": url,
                "headers": json.dumps(headers),
                "body_type": body_type,
                "payload": payload,
                "content_type": "application/json",
                "form_data": "[]",
                "extractors": "[]",
                "assertions": '[{"target": "status_code", "operator": "==", "expected": "200"}]',
            })
    return cases

@router.post("/postman")
async def import_postman(
    file: UploadFile = File(...),
    target_group_id: Optional[int] = Form(None),
    dry_run: bool = Form(False),
    session: AsyncSession = Depends(get_session)
):
    try:
        content = await file.read()
        collection = json.loads(content.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")

    if "item" not in collection:
        raise HTTPException(status_code=400, detail="无效的 Postman Collection 格式")
        
    # 如果没有指定 group_id，默认使用或创建一个根分组
    if not target_group_id:
        result = await session.execute(select(ApiGroup).where(ApiGroup.name == "Postman 导入"))
        group = result.scalar_one_or_none()
        if not group:
            group = ApiGroup(name="Postman 导入", parent_id=0)
            session.add(group)
            await session.commit()
            await session.refresh(group)
        target_group_id = group.id

    cases = extract_postman_cases(collection["item"], target_group_id)
    
    if dry_run:
        return {"cases": cases}
        
    imported_count = 0
    for case_data in cases:
        db_case = ApiCase(**case_data)
        session.add(db_case)
        imported_count += 1
        
    await session.commit()
    return {"imported_count": imported_count, "message": "导入成功"}

@router.post("/swagger")
async def import_swagger(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    target_group_id: Optional[int] = Form(None),
    dry_run: bool = Form(False),
    session: AsyncSession = Depends(get_session)
):
    import httpx
    
    swagger_data = None
    if file:
        content = await file.read()
        try:
            swagger_data = json.loads(content.decode("utf-8"))
        except:
            raise HTTPException(status_code=400, detail="文件解析失败，请确保是合法的 JSON")
    elif url:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10.0)
                swagger_data = resp.json()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"从 URL 获取失败: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="请提供文件或 URL")

    paths = swagger_data.get("paths", {})
    if not paths:
         raise HTTPException(status_code=400, detail="找不到 paths 节点，可能不是有效的 Swagger/OpenAPI 数据")

    # 如果没有指定 group_id，默认使用或创建一个根分组
    if not target_group_id:
        result = await session.execute(select(ApiGroup).where(ApiGroup.name == "Swagger 导入"))
        group = result.scalar_one_or_none()
        if not group:
            group = ApiGroup(name="Swagger 导入", parent_id=0)
            session.add(group)
            await session.commit()
            await session.refresh(group)
        target_group_id = group.id

    cases = []
    base_path = swagger_data.get("basePath", "")
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                continue
                
            full_url = "{{base_url}}" + base_path + path
            name = details.get("summary", f"{method.upper()} {path}")
            
            # TODO: 可以进一步解析 parameters 和 responses 生成更复杂的请求体和断言
            
            cases.append({
                "group_id": target_group_id,
                "name": name,
                "method": method.upper(),
                "url": full_url,
                "headers": "[]",
                "body_type": "raw",
                "payload": "{}",
                "content_type": "application/json",
                "form_data": "[]",
                "extractors": "[]",
                "assertions": '[{"target": "status_code", "operator": "==", "expected": "200"}]',
            })

    if dry_run:
        return {"cases": cases}
        
    imported_count = 0
    for case_data in cases:
        db_case = ApiCase(**case_data)
        session.add(db_case)
        imported_count += 1
        
    await session.commit()
    return {"imported_count": imported_count, "message": "导入成功"}