FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BIVE_ENV=production \
    BIVE_STORAGE=/data/bive.sqlite3

WORKDIR /app

RUN adduser --disabled-password --gecos "" --home /home/bive bive \
    && mkdir -p /data \
    && chown -R bive:bive /data /app

COPY pyproject.toml README.md LICENSE NOTICE ./
COPY requirements ./requirements
COPY src ./src
COPY schemas ./schemas
COPY docs ./docs
COPY scripts ./scripts

RUN pip install --no-cache-dir --upgrade pip==24.0 setuptools==69.5.1 wheel==0.43.0 \
    && pip install --no-cache-dir --no-build-isolation --constraint requirements/constraints.txt '.[api]' \
    && python -c "import bive; import bive.api"

USER bive
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/readyz', timeout=3).read()"
CMD ["bive-api"]
