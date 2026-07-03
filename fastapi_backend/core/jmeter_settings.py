"""
JMeter runtime settings loaded from environment (via systemd EnvironmentFile).

独立模块,避免污染 Settings 类。JMETER_HOME/JAVA_HOME 等运行时变量
通过 systemd EnvironmentFile=/opt/testmaster/.env 注入,无需进入 pydantic Settings。
"""

import os
import logging

_logger = logging.getLogger(__name__)

JMETER_HOME = os.getenv("JMETER_HOME", "/opt/jmeter")
JAVA_HOME = os.getenv("JAVA_HOME", "/usr/lib/jvm/java-17-openjdk-amd64")
JMETER_BIN = os.getenv("JMETER_BIN", os.path.join(JMETER_HOME, "bin", "jmeter"))
JMETER_REPORT_DIR = os.getenv("JMETER_REPORT_DIR", "/tmp/jmeter_reports")
JMETER_MAX_CONCURRENT = int(os.getenv("JMETER_MAX_CONCURRENT", "2"))
JMETER_TASK_TIMEOUT = int(os.getenv("JMETER_TASK_TIMEOUT", "1800"))
JMETER_ENGINE_ENABLED = os.getenv("JMETER_ENGINE_ENABLED", "false").lower() == "true"


def is_jmeter_available() -> bool:
    """检查 JMeter 可执行文件是否存在且 JMETER_ENGINE_ENABLED 开启"""
    if not JMETER_ENGINE_ENABLED:
        return False
    if not os.path.exists(JMETER_BIN):
        _logger.warning("JMETER_ENGINE_ENABLED=true 但 %s 不存在", JMETER_BIN)
        return False
    return True


_logger.info(
    "JMeter settings: home=%s, bin=%s, report_dir=%s, max_concurrent=%d, timeout=%ds, enabled=%s",
    JMETER_HOME, JMETER_BIN, JMETER_REPORT_DIR, JMETER_MAX_CONCURRENT,
    JMETER_TASK_TIMEOUT, JMETER_ENGINE_ENABLED,
)
