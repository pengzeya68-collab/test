"""
JMeter engine - 通过 subprocess 调用真实 JMeter 5.6.3 执行 .jmx 脚本。
生成 HTML 报告 + .jtl 结果文件,解析 .jtl 聚合 p50/p95/p99/tps。
"""

import asyncio
import csv
import logging
import os
import xml.etree.ElementTree as ET
from typing import Optional

from fastapi_backend.core.jmeter_settings import (
    JMETER_BIN, JAVA_HOME, JMETER_REPORT_DIR, JMETER_TASK_TIMEOUT,
)

_logger = logging.getLogger(__name__)


class JmeterEngine:
    """通过 subprocess 调用真实 JMeter 5.6.3"""

    @staticmethod
    async def run(jmx_content: str, run_id: str, props: Optional[dict] = None) -> dict:
        """执行 JMeter 脚本,返回结果路径与 stdout/stderr

        Args:
            jmx_content: .jmx 文件内容
            run_id: 唯一运行 ID,用作报告目录名
            props: JMeter 属性 (-J key=value)

        Returns:
            dict: exit_code, stdout, stderr, jmx_path, jtl_path, report_dir, process
        """
        run_dir = os.path.join(JMETER_REPORT_DIR, run_id)
        os.makedirs(run_dir, exist_ok=True)
        jmx_path = os.path.join(run_dir, "script.jmx")
        jtl_path = os.path.join(run_dir, "result.jtl")
        report_dir = os.path.join(run_dir, "report")

        with open(jmx_path, "w", encoding="utf-8") as f:
            f.write(jmx_content)

        cmd = [JMETER_BIN, "-n", "-t", jmx_path, "-l", jtl_path, "-e", "-o", report_dir]
        if props:
            for k, v in props.items():
                cmd.extend(["-J", f"{k}={v}"])

        env = os.environ.copy()
        if JAVA_HOME:
            env["JAVA_HOME"] = JAVA_HOME
            env["PATH"] = f"{JAVA_HOME}/bin:{env.get('PATH', '')}"

        _logger.info("[JMeter] 启动子进程: run_id=%s, cmd=%s", run_id, " ".join(cmd))
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=run_dir,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=JMETER_TASK_TIMEOUT
            )
        except asyncio.TimeoutError:
            _logger.warning("[JMeter] 任务超时,终止子进程: run_id=%s", run_id)
            await JmeterEngine.stop(process)
            raise RuntimeError(f"JMeter 任务超时({JMETER_TASK_TIMEOUT}s)")

        result = {
            "exit_code": process.returncode,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            "jmx_path": jmx_path,
            "jtl_path": jtl_path,
            "report_dir": report_dir,
            "process": process,
        }
        _logger.info(
            "[JMeter] 子进程结束: run_id=%s, exit_code=%s",
            run_id, process.returncode,
        )
        return result

    @staticmethod
    async def stop(process: asyncio.subprocess.Process) -> None:
        """优雅停止:SIGTERM → 等 5s → SIGKILL"""
        if process.returncode is not None:
            return
        try:
            process.terminate()
            await asyncio.wait_for(process.wait(), timeout=5)
        except asyncio.TimeoutError:
            _logger.warning("[JMeter] SIGTERM 超时,执行 SIGKILL")
            process.kill()
            await process.wait()


class JtlParser:
    """解析 .jtl 结果文件(CSV/XML),聚合 p50/p95/p99/tps/error_rate"""

    @staticmethod
    def parse(jtl_path: str) -> dict:
        if not os.path.exists(jtl_path):
            return {"error": "jtl not found", "total": 0}

        # 先嗅探格式:CSV 还是 XML
        with open(jtl_path, "r", encoding="utf-8") as f:
            head = f.read(2048)
            if head.lstrip().startswith("<?xml") or head.lstrip().startswith("<"):
                return JtlParser._parse_xml(jtl_path)
            f.seek(0)
            samples = JtlParser._parse_csv(f)

        return JtlParser._aggregate(samples)

    @staticmethod
    def _parse_csv(f) -> list:
        """JMeter 默认 CSV 列:timeStamp,elapsed,label,responseCode,responseMessage,
        threadName,dataType,success,failureMessage,bytes,sentBytes,grpThreads,
        allThreads,Latency,IdleTime,Connect"""
        samples = []
        reader = csv.DictReader(f)
        for row in reader:
            try:
                samples.append({
                    "elapsed": int(row.get("elapsed", 0)),
                    "success": str(row.get("success", "true")).lower() == "true",
                    "label": row.get("label", ""),
                    "ts": int(row.get("timeStamp", 0)),
                })
            except (ValueError, TypeError):
                continue
        return samples

    @staticmethod
    def _parse_xml(jtl_path: str) -> dict:
        tree = ET.parse(jtl_path)
        root = tree.getroot()
        samples = []
        # XML 格式: <sampleResult t="123" s="true" lb="label" ts="1234567890"/>
        for s in root.iter("sampleResult"):
            try:
                samples.append({
                    "elapsed": int(s.attrib.get("t", 0)),
                    "success": s.attrib.get("s", "true").lower() == "true",
                    "label": s.attrib.get("lb", ""),
                    "ts": int(s.attrib.get("ts", 0)),
                })
            except (ValueError, TypeError):
                continue
        # 兼容旧版本 <httpSample> 标签
        for s in root.iter("httpSample"):
            try:
                samples.append({
                    "elapsed": int(s.attrib.get("t", 0)),
                    "success": s.attrib.get("s", "true").lower() == "true",
                    "label": s.attrib.get("lb", ""),
                    "ts": int(s.attrib.get("ts", 0)),
                })
            except (ValueError, TypeError):
                continue
        return JtlParser._aggregate(samples)

    @staticmethod
    def _aggregate(samples: list) -> dict:
        if not samples:
            return {"total": 0, "tps": 0, "avg_ms": 0, "p95_ms": 0, "error_rate": 0}

        elapsed = sorted(s["elapsed"] for s in samples)
        success_count = sum(1 for s in samples if s["success"])
        total = len(samples)
        ts_min = min(s["ts"] for s in samples)
        ts_max = max(s["ts"] for s in samples)
        duration_s = max((ts_max - ts_min) / 1000.0, 0.001)

        def percentile(p: float) -> int:
            idx = int(total * p)
            if idx >= total:
                idx = total - 1
            return elapsed[idx]

        return {
            "total": total,
            "success": success_count,
            "failure": total - success_count,
            "error_rate": round((total - success_count) / total * 100, 2),
            "tps": round(total / duration_s, 2),
            "avg_ms": round(sum(elapsed) / total, 2),
            "p50_ms": percentile(0.5),
            "p95_ms": percentile(0.95),
            "p99_ms": percentile(0.99),
            "min_ms": elapsed[0],
            "max_ms": elapsed[-1],
        }
