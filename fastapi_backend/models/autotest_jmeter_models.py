"""
JMeter 模块数据模型 - 压测运行记录 / 实时快照 / 性能基线
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, func, Boolean
from fastapi_backend.core.database import Base


class JmeterBenchRun(Base):
    """JMeter 压测运行记录(支持真实 JMeter 引擎与快速预览模式)"""
    __tablename__ = "jmeter_bench_runs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_name = Column(String(255), nullable=False)
    config_json = Column(Text)  # 并发/时长/ramp_up/引擎类型等
    engine_type = Column(String(20), default="jmeter")  # 'mock' | 'jmeter'
    status = Column(String(20), default="pending")  # pending|running|success|failed|stopped
    task_id = Column(String(64), index=True)  # Celery task ID
    jmx_path = Column(String(500))
    jtl_path = Column(String(500))
    html_report_path = Column(String(500))
    summary_json = Column(Text)  # 聚合指标 JSON: p50/p95/p99/tps/error_rate
    error_msg = Column(Text)
    script_hash = Column(String(128), index=True)  # JMX 内容 SHA256,用于基线匹配
    regression = Column(Integer, default=0)  # 0=未回归,1=性能回归(超基线)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())


class JmeterBenchSample(Base):
    """单次采样的请求/响应详情(Stage F.4 修复 BUG 2 引入)。
    之前 sampler 详情被丢弃,导致前端"采样器列表"全 200 + 空响应。
    现在每条 JTL 记录都落库,前端通过 /runs/{id}/samples 查询。"""
    __tablename__ = "jmeter_bench_samples"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("jmeter_bench_runs.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    label = Column(String(500))  # 采样器名称(sampler label)
    method = Column(String(20))
    url = Column(Text)
    response_code = Column(String(20))  # 200/404/500 等
    response_message = Column(String(255))
    elapsed_ms = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    bytes_received = Column(Integer, default=0)
    bytes_sent = Column(Integer, default=0)
    success = Column(Boolean, default=True)  # JMeter 的 success 字段
    failure_message = Column(Text)
    request_data = Column(Text)  # 请求体(已截断 2000 字符)
    response_data = Column(Text)  # 响应体(已截断 2000 字符)
    request_headers = Column(Text)
    response_headers = Column(Text)
    thread_name = Column(String(255))
    ts = Column(DateTime, default=func.now(), index=True)  # 采样时间戳


class JmeterBenchSnapshot(Base):
    """实时进度快照,用于前端轮询图表"""
    __tablename__ = "jmeter_bench_snapshots"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("jmeter_bench_runs.id", ondelete="CASCADE"), index=True)
    ts = Column(DateTime, default=func.now())
    percent = Column(Integer, default=0)
    active_threads = Column(Integer, default=0)
    tps = Column(Float, default=0)
    avg_ms = Column(Float, default=0)
    p95_ms = Column(Float, default=0)
    error_rate = Column(Float, default=0)


class JmeterPerformanceBaseline(Base):
    """性能基线 - Stage E 使用,本迁移一并创建避免二次迁移"""
    __tablename__ = "jmeter_perf_baselines"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    script_hash = Column(String(128), index=True)  # 脚本内容 SHA256,自动匹配(留余量给 fallback hash)
    p95_threshold_ms = Column(Integer)
    p99_threshold_ms = Column(Integer)
    tps_threshold = Column(Float)
    error_rate_threshold = Column(Float)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
