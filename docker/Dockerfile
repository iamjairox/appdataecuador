# GovData Intelligence Platform - imagen de la aplicacion
# Python 3.13 + Playwright (navegadores instalados) para los modulos de scraping.

FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias de sistema necesarias para Playwright, pdfplumber/Camelot
# (poppler/ghostscript) y compilacion de paquetes con extensiones C.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ghostscript \
    libgl1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src
COPY README.md ./
RUN pip install --upgrade pip && pip install -e .

# Instala los navegadores de Playwright (chromium) y sus dependencias de SO.
RUN playwright install --with-deps chromium

COPY scripts ./scripts
COPY config ./config
COPY alembic.ini ./

ENV APP_ENV=production

CMD ["python", "scripts/run_pipeline.py"]
