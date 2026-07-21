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
    JMETER_BIN,
    JAVA_HOME,
    JMETER_REPORT_DIR,
    JMETER_TASK_TIMEOUT,
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

        # JMeter 5.6.3 的设计矛盾:
        #   - CSV 输出 hardcoded 只有 16 列(timeStamp..Connect),
        #     不会输出 samplerData/responseData/requestHeaders/responseHeaders
        #   - HTML Dashboard (jmeter -e -o) **只接受 CSV** 输入
        #     (5.6.3 源码报 "Report generation requires csv output format")
        #   - XML 输出包含所有 body 字段,但 -e -o 不兼容
        # 解决: 强制 XML 输出,放弃 JMeter 内置 HTML Dashboard,
        # 改用前端自研图表(TrendChart/BenchRunner 已有完整可视化)。
        # samples 详情落库后,前端通过 /runs/{id}/samples 读取并展示完整 body。
        # 备注: 即使 -J saveservice.response_data=true 也无效,JMeter CSV 写盘时
        # 仍按 hardcoded 16 列输出。
        save_props = {
            "jmeter.save.saveservice.output_format": "xml",
            "jmeter.save.saveservice.response_data": "true",
            "jmeter.save.saveservice.response_data.on_error": "true",
            "jmeter.save.saveservice.samplerData": "true",
            "jmeter.save.saveservice.requestHeaders": "true",
            "jmeter.save.saveservice.url": "true",
            "jmeter.save.saveservice.responseHeaders": "true",
            "jmeter.save.saveservice.responseMessage": "true",
            "jmeter.save.saveservice.assertion_results": "none",
        }
        # 关键: JMeter 启动时从 user.dir 解析 jmeter.properties,
        # 但本任务 cwd=run_dir 不是 jmeter bin,会找不到 jmeter.properties,
        # 导致 -J saveservice.* 也不生效。显式 -p 指定 jmeter.properties 路径。
        jmeter_props = os.path.join(os.path.dirname(JMETER_BIN), "jmeter.properties")
        # 关键: 删除已有的 report_dir(若存在),避免 -e -o 报 "Report generation requires csv"。
        # 我们不用 -e -o,改用 XML jtl + 前端自研图表。
        cmd = [JMETER_BIN, "-n", "-t", jmx_path, "-l", jtl_path, "-p", jmeter_props]
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
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=JMETER_TASK_TIMEOUT)
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
            run_id,
            process.returncode,
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
                samples.append(
                    {
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
                    }
                )
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

        JMeter 5.6.3 实际输出格式(无 sampleResult 包裹):
        <httpSample t="..." s="true" rc="200" rm="OK" lb="label" ts="..." by="486" sby="112">
          <responseHeader class="java.lang.String">...完整 headers...</responseHeader>
          <requestHeader class="java.lang.String">...完整 headers...</requestHeader>
          <responseData class="java.lang.String">{...JSON 响应体...}</responseData>
          <cookies class="java.lang.String"></cookies>
          <method class="java.lang.String">GET</method>
          <queryString class="java.lang.String"></queryString>
          <java.net.URL>https://...</java.net.URL>
        </httpSample>
        """
        samples = []

        # 提取 httpSample 子节点 body 字段的辅助函数
        def _extract_sub_nodes(s) -> dict:
            out = {
                "response_data": "",
                "request_data": "",
                "request_headers": "",
                "response_headers": "",
                "method": "",
                "url": "",
            }
            for sub in s:
                tag = sub.tag
                text = sub.text or ""
                if tag == "responseData" and text:
                    out["response_data"] = text[:2000] + ("..." if len(text) > 2000 else "")
                elif tag == "samplerData" and text:
                    out["request_data"] = text[:2000] + ("..." if len(text) > 2000 else "")
                elif tag == "requestHeader" and text:
                    out["request_headers"] = text[:2000] + ("..." if len(text) > 2000 else "")
                elif tag == "responseHeader" and text:
                    out["response_headers"] = text[:2000] + ("..." if len(text) > 2000 else "")
                elif tag == "method" and text:
                    out["method"] = text
                elif tag == "java.net.URL" and text:
                    out["url"] = text
            return out

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
                    item.update(
                        {
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
                        }
                    )
                samples.append(item)
            except (ValueError, TypeError):
                continue
        # 兼容 JMeter 5.6 默认输出格式(无 sampleResult 包裹,直接 httpSample)
        # 关键: 必须解析子节点(responseData/requestHeader/responseHeader/method/java.net.URL)
        for s in root.iter("httpSample"):
            try:
                item = {
                    "elapsed": int(s.attrib.get("t", 0) or 0),
                    "success": s.attrib.get("s", "true").lower() == "true",
                    "label": s.attrib.get("lb", "") or "",
                    "ts": int(s.attrib.get("ts", 0) or 0),
                }
                if include_details:
                    # 优先从子节点提取 body 字段(JMeter 5.6 默认输出)
                    sub_data = _extract_sub_nodes(s)
                    # attrib 中的 URL/responseData 兜底
                    response_data = sub_data["response_data"] or s.attrib.get("responseData", "") or ""
                    request_data = sub_data["request_data"] or s.attrib.get("samplerData", "") or ""
                    if len(response_data) > 2000:
                        response_data = response_data[:2000] + "..."
                    if len(request_data) > 2000:
                        request_data = request_data[:2000] + "..."
                    method = sub_data["method"] or _extract_method(request_data)
                    url = sub_data["url"] or s.attrib.get("url") or s.attrib.get("URL") or ""
                    request_headers = sub_data["request_headers"] or s.attrib.get("requestHeaders", "") or ""
                    response_headers = sub_data["response_headers"] or s.attrib.get("responseHeaders", "") or ""
                    item.update(
                        {
                            "response_code": s.attrib.get("rc", "") or "",
                            "response_message": s.attrib.get("rm", "") or "",
                            "thread_name": s.attrib.get("tn", "") or "",
                            "url": url,
                            "method": method,
                            "bytes": int(s.attrib.get("by", 0) or 0),
                            "sent_bytes": int(s.attrib.get("sby", 0) or 0),
                            "latency": int(s.attrib.get("lt", 0) or 0),
                            "connect": int(s.attrib.get("ct", 0) or 0),
                            "failure_message": s.attrib.get("fm", "") or "",
                            "request_data": request_data,
                            "response_data": response_data,
                            "request_headers": request_headers,
                            "response_headers": response_headers,
                        }
                    )
                samples.append(item)
            except (ValueError, TypeError):
                continue
        return samples

    @staticmethod
    def _aggregate(samples: list) -> dict:
        """聚合指标 + 详细统计(供前端 BenchRunner.vue 完整展示)
        返回字段:
          - 基础: total/success/failure/error_rate/tps/avg_ms/p50/p95/p99/min/max
          - 按接口: per_url
          - 状态码: status_distribution
          - 响应时间分布: rt_distribution
          - 吞吐量趋势: throughput_trend
          - 错误详情: errors
        """
        if not samples:
            return {
                "total": 0,
                "success": 0,
                "failure": 0,
                "error_rate": 0,
                "tps": 0,
                "avg_ms": 0,
                "p50_ms": 0,
                "p95_ms": 0,
                "p99_ms": 0,
                "min_ms": 0,
                "max_ms": 0,
                "per_url": [],
                "status_distribution": {},
                "rt_distribution": {},
                "throughput_trend": [],
                "errors": [],
            }

        elapsed = sorted(s["elapsed"] for s in samples)
        success_count = sum(1 for s in samples if s["success"])
        total = len(samples)
        ts_min = min(s["ts"] for s in samples) if samples else 0
        ts_max = max(s["ts"] for s in samples) if samples else 0
        duration_s = max((ts_max - ts_min) / 1000.0, 0.001)

        def percentile(p: float) -> int:
            idx = int(total * p)
            if idx >= total:
                idx = total - 1
            return elapsed[idx]

        # 1) per_url: 按 (label|url) 聚合
        per_url_map = {}
        for s in samples:
            label = s.get("label") or s.get("url") or "unknown"
            key = label
            if key not in per_url_map:
                per_url_map[key] = {
                    "name": label,
                    "method": s.get("method", "GET") or "GET",
                    "url": s.get("url", "") or "",
                    "count": 0,
                    "success": 0,
                    "failed": 0,
                    "elapsed_total": 0,
                    "elapsed_list": [],
                }
            entry = per_url_map[key]
            entry["count"] += 1
            if s.get("success"):
                entry["success"] += 1
            else:
                entry["failed"] += 1
            entry["elapsed_total"] += s["elapsed"]
            entry["elapsed_list"].append(s["elapsed"])

        per_url = []
        for entry in per_url_map.values():
            cnt = entry["count"]
            elapsed_sorted = sorted(entry["elapsed_list"])

            def _pct(arr, p):
                if not arr:
                    return 0
                idx = int(len(arr) * p)
                if idx >= len(arr):
                    idx = len(arr) - 1
                return arr[idx]

            per_url.append(
                {
                    "name": entry["name"],
                    "method": entry["method"],
                    "url": entry["url"],
                    "count": cnt,
                    "success": entry["success"],
                    "failed": entry["failed"],
                    "success_rate": round(entry["success"] / cnt * 100, 2) if cnt > 0 else 0,
                    "avg_ms": round(entry["elapsed_total"] / cnt, 2) if cnt > 0 else 0,
                    "min_ms": elapsed_sorted[0] if elapsed_sorted else 0,
                    "max_ms": elapsed_sorted[-1] if elapsed_sorted else 0,
                    "p50_ms": _pct(elapsed_sorted, 0.5),
                    "p95_ms": _pct(elapsed_sorted, 0.95),
                    "p99_ms": _pct(elapsed_sorted, 0.99),
                }
            )

        # 2) status_distribution: 按响应码计数
        status_distribution = {}
        for s in samples:
            rc = s.get("response_code", "0") or "0"
            try:
                rc_int = int(rc)
            except (ValueError, TypeError):
                rc_int = 0
            status_distribution[rc_int if rc_int else rc] = status_distribution.get(rc_int if rc_int else rc, 0) + 1

        # 3) rt_distribution: 响应时间分布(<10/10-50/50-100/100-500/500-1000/1000-3000/>3000ms)
        rt_buckets = [
            ("<10ms", 0, 10),
            ("10-50ms", 10, 50),
            ("50-100ms", 50, 100),
            ("100-500ms", 100, 500),
            ("500-1000ms", 500, 1000),
            ("1000-3000ms", 1000, 3000),
            (">3000ms", 3000, float("inf")),
        ]
        rt_distribution = {label: 0 for label, _, _ in rt_buckets}
        for s in samples:
            e = s["elapsed"]
            for label, lo, hi in rt_buckets:
                if lo <= e < hi:
                    rt_distribution[label] += 1
                    break

        # 4) throughput_trend: 5秒窗口
        trend_buckets = {}
        for s in samples:
            sec = int(s["ts"] / 1000)
            bucket = (sec // 5) * 5
            if bucket not in trend_buckets:
                trend_buckets[bucket] = {"t": bucket, "count": 0}
            trend_buckets[bucket]["count"] += 1
        # 从最早 sample 时间开始算 (相对时间)
        if trend_buckets:
            first_sec = min(trend_buckets.keys())
            throughput_trend = []
            for t in sorted(trend_buckets.keys()):
                e = trend_buckets[t]
                # 改为相对时间 (从0开始)
                rel = t - first_sec
                throughput_trend.append(
                    {
                        "t": rel,
                        "count": e["count"],
                        "tps": round(e["count"] / 5.0, 2),
                    }
                )
        else:
            throughput_trend = []

        # 5) errors: 失败详情(最多 50 条,按时间倒序)
        errors = []
        for s in sorted(samples, key=lambda x: x.get("ts", 0), reverse=True):
            if not s.get("success"):
                errors.append(
                    {
                        "name": s.get("label", "") or "",
                        "method": s.get("method", "GET") or "GET",
                        "url": s.get("url", "") or "",
                        "status": int(s.get("response_code", "0") or 0),
                        "response_message": s.get("response_message", "") or "",
                        "elapsed_ms": s.get("elapsed", 0) or 0,
                        "error": s.get("failure_message", "") or s.get("response_message", "") or "请求失败",
                        "request_body": s.get("request_data", "") or "",
                        "response_body": s.get("response_data", "") or "",
                    }
                )
                if len(errors) >= 50:
                    break

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
            "per_url": per_url,
            "status_distribution": status_distribution,
            "rt_distribution": rt_distribution,
            "throughput_trend": throughput_trend,
            "errors": errors,
        }
