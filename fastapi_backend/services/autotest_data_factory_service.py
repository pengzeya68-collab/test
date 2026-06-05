"""
测试数据工厂服务 - 生成测试数据
支持规则: fixed, enum, increment, uuid, timestamp, date_offset, phone, email, username, env_ref
"""
import random
import string
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


class DataFactoryEngine:
    """数据工厂生成引擎"""

    RULE_HANDLERS = {}

    def __init__(self, env_vars: Optional[Dict[str, Any]] = None):
        self.env_vars = env_vars or {}
        self._increment_counters: Dict[str, int] = {}
        self._counter_lock = threading.Lock()

    def generate_preview(self, fields: List[dict], row_count: int = 5) -> Dict[str, Any]:
        self._increment_counters.clear()  # 每次生成预览时重置计数器
        columns = [f["field_name"] for f in fields]
        rows = []
        for _ in range(min(row_count, 20)):
            row = []
            for field in fields:
                value = self._generate_value(field["rule_type"], field.get("rule_config") or {}, field["field_name"])
                row.append(value)
            rows.append(row)
        return {"columns": columns, "rows": rows}

    def generate_dataset(self, fields: List[dict], row_count: int = 10) -> Dict[str, Any]:
        self._increment_counters.clear()  # 每次生成数据集时重置计数器
        columns = [f["field_name"] for f in fields]
        rows = []
        for _ in range(row_count):
            row = []
            for field in fields:
                value = self._generate_value(field["rule_type"], field.get("rule_config") or {}, field["field_name"])
                row.append(value)
            rows.append(row)
        return {"columns": columns, "rows": rows, "row_count": len(rows)}

    def _generate_value(self, rule_type: str, config: dict, field_name: str = "") -> Any:
        if rule_type == "fixed":
            return config.get("value", "")
        elif rule_type == "enum":
            options = config.get("options", [])
            return random.choice(options) if options else ""
        elif rule_type == "increment":
            prefix = config.get("prefix", "")
            start = config.get("start", 1)
            step = config.get("step", 1)
            key = field_name or "default"
            with self._counter_lock:
                if key not in self._increment_counters:
                    self._increment_counters[key] = start
                else:
                    self._increment_counters[key] += step
                return f"{prefix}{self._increment_counters[key]}"
        elif rule_type == "uuid":
            version = config.get("version", 4)
            raw = str(uuid.uuid4())
            if version == "simple":
                return raw.replace("-", "")
            elif version == "short":
                return raw[:8]
            return raw
        elif rule_type == "timestamp":
            fmt = config.get("format", "seconds")
            offset_seconds = config.get("offset_seconds", 0)
            ts = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)
            if fmt == "seconds":
                return int(ts.timestamp())
            elif fmt == "milliseconds":
                return int(ts.timestamp() * 1000)
            elif fmt == "iso":
                return ts.isoformat()
            elif fmt == "datetime":
                return ts.strftime("%Y-%m-%d %H:%M:%S")
            else:
                return ts.strftime(fmt)
        elif rule_type == "date_offset":
            fmt = config.get("format", "date")
            offset_days = config.get("offset_days", 0)
            dt = datetime.now(timezone.utc) + timedelta(days=offset_days)
            if fmt == "date":
                return dt.strftime("%Y-%m-%d")
            elif fmt == "datetime":
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                return dt.strftime(fmt)
        elif rule_type == "phone":
            prefixes = ["130", "131", "132", "133", "134", "135", "136", "137", "138", "139",
                        "150", "151", "152", "153", "155", "156", "157", "158", "159",
                        "180", "181", "182", "183", "184", "185", "186", "187", "188", "189"]
            prefix = config.get("prefix", "")
            if prefix:
                prefix_val = random.choice([p for p in prefixes if p.startswith(prefix[:3])]) if len(prefix) >= 3 else random.choice(prefixes)
            else:
                prefix_val = random.choice(prefixes)
            return prefix_val + ''.join(random.choices(string.digits, k=8))
        elif rule_type == "email":
            domains = config.get("domains", config.get("domain", "test.com"))
            username_prefix = config.get("username_prefix", "testuser")
            domain = random.choice(domains) if isinstance(domains, list) else domains
            return f"{username_prefix}{random.randint(1000, 9999)}@{domain}"
        elif rule_type == "username":
            prefixes = config.get("prefixes", config.get("prefix", "testuser"))
            prefix = random.choice(prefixes) if isinstance(prefixes, list) else prefixes
            suffix_length = config.get("suffix_length", 4)
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=suffix_length))
            return f"{prefix}_{suffix}"
        elif rule_type == "env_ref":
            var_name = config.get("variable_name", "")
            default = config.get("default") if "default" in config else ""
            val = self.env_vars.get(str(var_name))
            return val if val is not None else default
        else:
            return config.get("value", "")


data_factory = DataFactoryEngine()