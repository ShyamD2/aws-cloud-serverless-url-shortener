# Local Development & AWS Setup Guide

## 1. Prerequisites

Ensure the following tools are installed (verified in Phase 0):
- **AWS CLI v2** (`aws --version`)
- **Terraform >= 1.5.0** (`terraform version`)
- **Python 3.13** (`python --version`)
- **Git** (`git --version`)

---

## 2. Local Python Environment Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 2. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r application/requirements.txt
```

---

## 3. Running Unit Tests & Linters Locally

```bash
# Run unit tests with pytest
pytest -v

# Run Ruff linter and format checker
ruff check application/
ruff format --check application/

# Run safe local latency benchmark
python scripts/benchmark_safe.py
```

---

## 4. Terraform Setup & Local Validation

```bash
# Format check
terraform fmt -recursive terraform/

# Initialize and validate dev configuration
cd terraform/environments/dev
terraform init -backend=false
terraform validate
```
