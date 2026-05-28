"""
性能测试报告 - 路由层
POST /api/auto-test/report/generate → 生成 Word 性能测试报告
"""
import io
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List
from urllib.parse import quote

from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.services.performance_report_service import generate_performance_report, _call_ai_analysis

router = APIRouter(prefix="/api/auto-test/report", tags=["性能测试报告"])


@router.post("/generate")
async def generate_report(body: Dict[str, Any] = Body(...)):
    """
    生成性能测试报告 (docx)

    Request Body:
    {
        "report_name": "TestMaster 性能测试报告",
        "test_env": {"domain": "https://api.example.com", "env_name": "生产环境"},
        "author": "亚哥",
        "env_config": {
            "CPU": "8核",
            "内存": "16GB",
            "操作系统": "Linux / Windows Server 2022",
            "JDK版本": "OpenJDK 17",
            "压测工具": "TestMaster (JMeter引擎)",
            "网络环境": "内网千兆",
            "数据库": "MySQL 8.0 / PostgreSQL 15"
        },
        "scenarios": [
            {
                "name": "登录接口压测",
                "url": "/api/login",
                "method": "POST",
                "target_qps": 500,
                "actual_qps": 480,
                "concurrency": 100,
                "threads": 100,
                "ramp_up": 30,
                "loops": 10,
                "duration": 300,
                "avg_ms": 450,
                "p50_ms": 320,
                "p90_ms": 680,
                "p95_ms": 1200,
                "p99_ms": 2800,
                "stddev_ms": 150,
                "max_ms": 3500,
                "min_ms": 80,
                "error_rate": 0.5,
                "total_requests": 10000,
                "failed_requests": 50,
                "result": "通过",
                "test_start": "2026-05-28 10:00:00",
                "test_end": "2026-05-28 10:05:00"
            }
        ],
        "summary": {
            "total_requests": 50000,
            "total_failed": 250,
            "overall_error_rate": 0.5,
            "overall_result": "通过",
            "notes": "系统表现稳定"
        },
        "error_types": {"连接超时": 30, "HTTP 500": 15, "HTTP 503": 5}
    }
    """
    report_name = body.get("report_name", "TestMaster 性能测试报告")
    test_env = body.get("test_env", {"domain": "", "env_name": "生产环境"})
    scenarios = body.get("scenarios", [])
    summary = body.get("summary")
    author = body.get("author", "TestMaster")
    error_types = body.get("error_types")
    env_config = body.get("env_config")
    rt_distribution = body.get("rt_distribution")
    throughput_trend = body.get("throughput_trend")
    status_distribution = body.get("status_distribution")

    if not scenarios:
        raise HTTPException(status_code=400, detail="请提供至少一个测试场景")

    ai_suggestions = ""
    try:
        ai_suggestions = await _call_ai_analysis(scenarios, summary or {}, test_env)
    except Exception as e:
        ai_suggestions = ""
        print(f"[Report] AI分析调用失败: {e}")

    try:
        docx_bytes = generate_performance_report(
            report_name=report_name,
            test_env=test_env,
            scenarios=scenarios,
            summary=summary,
            author=author,
            error_types=error_types,
            ai_suggestions=ai_suggestions,
            env_config=env_config,
            rt_distribution=rt_distribution,
            throughput_trend=throughput_trend,
            status_distribution=status_distribution,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")

    filename = f'{report_name}.docx'
    encoded = quote(filename, safe='')

    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.post("/preview")
async def preview_report_data(body: Dict[str, Any] = Body(...)):
    """预览报告数据（不生成 docx，仅返回数据摘要）"""
    scenarios = body.get("scenarios", [])

    total_requests = sum(s.get("total_requests", 0) for s in scenarios)
    total_failed = sum(s.get("failed_requests", 0) for s in scenarios)
    passed = sum(1 for s in scenarios if s.get("result") in ("通过", "pass"))

    return {
        "total_scenarios": len(scenarios),
        "total_requests": total_requests,
        "total_failed": total_failed,
        "passed_count": passed,
        "failed_count": len(scenarios) - passed,
        "scenarios": [
            {
                "name": s.get("name"),
                "actual_qps": s.get("actual_qps"),
                "avg_ms": s.get("avg_ms"),
                "p50_ms": s.get("p50_ms"),
                "p90_ms": s.get("p90_ms"),
                "p95_ms": s.get("p95_ms"),
                "p99_ms": s.get("p99_ms"),
                "stddev_ms": s.get("stddev_ms"),
                "error_rate": s.get("error_rate"),
                "result": s.get("result"),
            }
            for s in scenarios
        ],
    }