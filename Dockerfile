# TestMaster FastAPI Backend - Production Dockerfile
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录并设权限（直接用 root 运行避免权限问题）
RUN mkdir -p /app/instance /app/fastapi_backend/autotest_data/reports \
    && chmod -R 777 /app/instance /app/fastapi_backend/autotest_data

EXPOSE 5001

# 开发/小规模部署用单 worker 避免 SQLite 锁冲突和调度器重复
CMD ["uvicorn", "fastapi_backend.main:app", "--host", "0.0.0.0", "--port", "5001"]
