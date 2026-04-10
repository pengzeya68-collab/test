"""
零代码接口自动化测试平台
FastAPI 主入口

特点：
- 零代码配置：通过表单填写添加接口用例
- 分组管理：树形结构组织接口
- 测试计划：组合多个用例批量执行
- 自动生成测试报告：保存历史执行记录
- 变量替换：支持环境变量占位符 {{base_url}}
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_backend.core.config import settings
from fastapi_backend.core.database import engine, Base

# 导入路由
from fastapi_backend.routers.groups import router as groups_router
from fastapi_backend.routers.cases import router as cases_router
from fastapi_backend.routers.environments import router as envs_router
from fastapi_backend.routers.plans import router as plans_router
from fastapi_backend.routers.execution import router as execution_router

# 创建数据库表（首次运行）
async def create_tables():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(groups_router)
app.include_router(cases_router)
app.include_router(envs_router)
app.include_router(plans_router)
app.include_router(execution_router)


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "API is running"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5001,
        reload=True
    )
