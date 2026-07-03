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


def _extract_method(sampler_data: str) -> str:
    """从 samplerData 文本中提取 HTTP 方法。samplerData 形如 'GET http://...'
    或 'POST http://...'。"""
    if not sampler_data:
        return ""
    first = sampler_data.strip().split(None, 1)[0].upper() if sampler_data.strip() else ""
    return first if first in {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"} else ""


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

        # 默认 jmeter.save.saveservice 不存响应体/请求体/URL,会导致采样器详情全空
        # 显式开启 response_data + samplerData + URL,这样 JTL 才会包含这些列
        # 这些 -J 只影响本次 run,不污染全局 jmeter.properties
        save_props = {
            "jmeter.save.saveservice.output_format": "csv",
            "jmeter.save.saveservice.response_data": "true",
            "jmeter.save.saveservice.response_data.on_error": "true",
            "jmeter.save.saveservice.samplerData": "true",
            "jmeter.save.saveservice.requestHeaders": "true",
            "jmeter.save.saveservice.url": "true",
            "jmeter.save.saveservice.responseHeaders": "true",
            "jmeter.save.saveservice.responseMessage": "true",
            "jmeter.save.saveservice.assertion_results": "none",
        }
        cmd = [JMETER_BIN, "-n", "-t", jmx_path, "-l", jtl_path, "-e", "-o", report_dir]
        for k, v in save_props.items():
            cmd.extend(["-J", f"{k}={v}"])
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
                samples = JtlParser._parse_xml_full(jtl_path)
            else:
                f.seek(0)
                samples = JtlParser._parse_csv_full(f)

        return JtlParser._aggregate(samples)

    @staticmethod
    def parse_with_samples(jtl_path: str) -> tuple:
        """解析 JTL 并返回 (聚合指标, 详细样本列表)。
        详细样本包含 response_code/url/response_data/sampler_data,供前端展示采样器详情。
        """
        if not os.path.exists(jtl_path):
            return ({"error": "jtl not found", "total": 0}, [])

        with open(jtl_path, "r", encoding="utf-8") as f:
            head = f.read(2048)
            if head.lstrip().startswith("<?xml") or head.lstrip().startswith("<"):
                samples = JtlParser._parse_xml_full(jtl_path)
            else:
                f.seek(0)
                samples = JtlParser._parse_csv_full(f)

        return JtlParser._aggregate(samples), samples

    @staticmethod
    def _parse_csv(f) -> list:
        """兼容旧调用:仅返回聚合用 4 字段"""
        return [
            {
                "elapsed": int(s.get("elapsed", 0)),
                "success": s.get("success", True),
                "label": s.get("label", ""),
                "ts": s.get("ts", 0),
            }
            for s in JtlParser._parse_csv_full(f)
        ]

    @staticmethod
    def _parse_csv_full(f) -> list:
        """完整解析 CSV 行的所有字段,包含响应体/请求体/URL。
        JMeter 默认列(开启 -J saveservice.response_data=true 后):
        timeStamp,elapsed,label,responseCode,responseMessage,threadName,dataType,
        success,failureMessage,bytes,sentBytes,grpThreads,allThreads,URL,Latency,
        IdleTime,Connect,samplerData,requestHeaders,responseHeaders,responseData
        """
        samples = []
        reader = csv.DictReader(f)
        for row in reader:
            try:
                response_data = row.get("responseData") or row.get("ResponseData") or ""
                sampler_data = row.get("samplerData") or row.get("SamplerData") or ""
                # 限制 body 长度,避免大响应把内存吃光
                if len(response_data) > 2000:
                    response_data = response_data[:2000] + "..."
                if len(sampler_data) > 2000:
                    sampler_data = sampler_data[:2000] + "..."
                samples.append({
                    "elapsed": int(row.get("elapsed", 0) or 0),
                    "success": str(row.get("success", "true")).lower() == "true",
                    "label": row.get("label", "") or "",
                    "ts": int(row.get("timeStamp", 0) or 0),
                    # 详情字段(原本被丢弃,导致采样器列表全空)
                    "response_code": row.get("responseCode", "") or "",
                    "response_message": row.get("responseMessage", "") or "",
                    "thread_name": row.get("threadName", "") or "",
                    "url": row.get("URL") or row.get("url") or "",
                    "method": row.get("method") or _extract_method(row.get("samplerData", "") or ""),
                    "bytes": int(row.get("bytes", 0) or 0),
                    "sent_bytes": int(row.get("sentBytes", 0) or 0),
                    "latency": int(row.get("Latency", 0) or 0),
                    "connect": int(row.get("Connect", 0) or 0),
                    "failure_message": row.get("failureMessage", "") or "",
                    "request_data": sampler_data,
                    "response_data": response_data,
                    "request_headers": row.get("requestHeaders", "") or "",
                    "response_headers": row.get("responseHeaders", "") or "",
                })
            except (ValueError, TypeError):
                continue
        return samples

    @staticmethod
    def _parse_xml(jtl_path: str) -> dict:
        """兼容旧调用:仅返回聚合指标"""
        tree = ET.parse(jtl_path)
        root = tree.getroot()
        samples = JtlParser._iter_xml_samples(root)
        return JtlParser._aggregate(samples)

    @staticmethod
    def _parse_xml_full(jtl_path: str) -> list:
        """完整解析 XML 格式的 JTL,包含响应体/请求体。"""
        tree = ET.parse(jtl_path)
        root = tree.getroot()
        return JtlParser._iter_xml_samples(root, include_details=True)

    @staticmethod
    def _iter_xml_samples(root, include_details: bool = False) -> list:
        """遍历 XML 中所有 sampleResult/httpSample 节点。
        XML 格式: <sampleResult t="elapsed_ms" s="true/false" rc="200" rm="OK"
        lb="label" ts="timestamp" by="bytes" sby="sentBytes" tn="threadName"
        dt="dataType" de="dataEncoding" ng="grpThreads" na="allThreads" hn="hostname">
          <httpSample ...>
        </sampleResult>
        """
        samples = []
        for s in root.iter("sampleResult"):
            try:
                item = {
                    "elapsed": int(s.attrib.get("t", 0) or 0),
                    "success": s.attrib.get("s", "true").lower() == "true",
                    "label": s.attrib.get("lb", "") or "",
                    "ts": int(s.attrib.get("ts", 0) or 0),
                }
                if include_details:
                    response_data = ""
                    request_data = ""
                    if s.text and include_details:
                        response_data = s.text[:2000] + ("..." if len(s.text) > 2000 else "")
                    request_headers = s.attrib.get("requestHeaders", "") or ""
                    response_headers = s.attrib.get("responseHeaders", "") or ""
                    # XML 的 responseData 经常作为子节点
                    for sub in s:
                        if sub.tag == "responseData" and sub.text:
                            response_data = sub.text[:2000] + ("..." if len(sub.text) > 2000 else "")
                        elif sub.tag == "samplerData" and sub.text:
                            request_data = sub.text[:2000] + ("..." if len(sub.text) > 2000 else "")
                    item.update({
                        "response_code": s.attrib.get("rc", "") or "",
                        "response_message": s.attrib.get("rm", "") or "",
                        "thread_name": s.attrib.get("tn", "") or "",
                        "url": s.attrib.get("url") or s.attrib.get("URL") or "",
                        "method": _extract_method(request_data),
                        "bytes": int(s.attrib.get("by", 0) or 0),
                        "sent_bytes": int(s.attrib.get("sby", 0) or 0),
                        "latency": int(s.attrib.get("lt", 0) or 0),
                        "connect": int(s.attrib.get("ct", 0) or 0),
                        "failure_message": s.attrib.get("fm", "") or "",
                        "request_data": request_data,
                        "response_data": response_data,
                        "request_headers": request_headers,
                        "response_headers": response_headers,
                    })
                samples.append(item)
            except (ValueError, TypeError):
                continue
        # 兼容旧版本 <httpSample> 标签(没 sampleResult 包裹)
        for s in root.iter("httpSample"):
            try:
                item = {
                    "elapsed": int(s.attrib.get("t", 0) or 0),
                    "success": s.attrib.get("s", "true").lower() == "true",
                    "label": s.attrib.get("lb", "") or "",
                    "ts": int(s.attrib.get("ts", 0) or 0),
                }
                if include_details:
                    response_data = s.attrib.get("responseData", "") or ""
                    request_data = s.attrib.get("samplerData", "") or ""
                    if len(response_data) > 2000:
                        response_data = response_data[:2000] + "..."
                    if len(request_data) > 2000:
                        request_data = request_data[:2000] + "..."
                    item.update({
                        "response_code": s.attrib.get("rc", "") or "",
                        "response_message": s.attrib.get("rm", "") or "",
                        "thread_name": s.attrib.get("tn", "") or "",
                        "url": s.attrib.get("url") or s.attrib.get("URL") or "",
                        "method": _extract_method(request_data),
                        "bytes": int(s.attrib.get("by", 0) or 0),
                        "sent_bytes": int(s.attrib.get("sby", 0) or 0),
                        "latency": int(s.attrib.get("lt", 0) or 0),
                        "connect": int(s.attrib.get("ct", 0) or 0),
                        "failure_message": s.attrib.get("fm", "") or "",
                        "request_data": request_data,
                        "response_data": response_data,
                        "request_headers": s.attrib.get("requestHeaders", "") or "",
                        "response_headers": s.attrib.get("responseHeaders", "") or "",
                    })
                samples.append(item)
            except (ValueError, TypeError):
                continue
        return samples

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
