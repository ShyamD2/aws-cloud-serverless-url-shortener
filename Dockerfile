# Multi-stage production-ready Dockerfile
# Stage 1: Base Python environment
FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install application dependencies
COPY application/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Stage 2: Testing & CI Target
FROM base AS test
COPY application ./application
COPY pytest.ini ./pytest.ini
CMD ["pytest", "-v"]

# Stage 3: Containerized Lambda runtime target
FROM public.ecr.aws/lambda/python:3.13 AS lambda
COPY application/requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt
COPY application/src ${LAMBDA_TASK_ROOT}/src
CMD ["src.handlers.redirect.lambda_handler"]
