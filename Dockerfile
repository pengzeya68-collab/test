ARG ALLURE_VERSION=2.32.0

FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt


FROM python:3.11-slim-bookworm

ARG ALLURE_VERSION

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    gnupg \
    ca-certificates \
    default-jre-headless \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    && install -d /usr/share/postgresql-common/pgdg \
    && curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client-16 \
    && ln -sf /usr/lib/postgresql/16/bin/pg_dump /usr/bin/pg_dump \
    && ln -sf /usr/lib/postgresql/16/bin/psql /usr/bin/psql \
    && curl -sL https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.tgz -o /tmp/allure.tgz \
    && tar -xzf /tmp/allure.tgz -C /opt/ \
    && ln -s /opt/allure-${ALLURE_VERSION}/bin/allure /usr/local/bin/allure \
    && rm /tmp/allure.tgz \
    && apt-get purge -y gnupg \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY . .

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser \
    && mkdir -p /app/instance /app/fastapi_backend/autotest_data/reports /app/backups \
    && chown -R appuser:appuser /app/instance /app/fastapi_backend/autotest_data /app/backups

USER appuser

EXPOSE 5001

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:5001/api/health || exit 1

CMD ["uvicorn", "fastapi_backend.main:app", "--host", "0.0.0.0", "--port", "5001"]
