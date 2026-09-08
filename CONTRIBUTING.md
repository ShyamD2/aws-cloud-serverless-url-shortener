# Contributing to AWS Cloud Serverless URL Shortener & Analytics

Thank you for your interest in contributing to this project! We welcome contributions from developers of all skill levels, from fixing typos in documentation to implementing new serverless capabilities.

---

## 1. Code of Conduct

All contributors and maintainers are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please treat everyone with respect and empathy.

---

## 2. Getting Started & Local Development

You do **not** need an active AWS account or credit card to contribute to this project! All core services use mocked AWS interfaces via `moto` and can be tested locally.

### 2.1 Prerequisites
- **Python >= 3.13**
- **Git**
- **Terraform >= 1.5.0** (optional, only needed for IaC changes)
- **Docker** (optional, for LocalStack emulation)

### 2.2 Local Setup
```bash
# 1. Fork the repository on GitHub, then clone your fork:
git clone https://github.com/<your-username>/aws-cloud-serverless-url-shortener.git
cd aws-cloud-serverless-url-shortener

# 2. Create and activate a Python virtual environment:
python -m venv .venv
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# 3. Install dependencies (runtime + testing):
python -m pip install --upgrade pip
pip install -r application/requirements.txt
```

---

## 3. Development Workflow & Quality Gates

Before submitting a Pull Request, ensure your changes pass all quality checks:

### 3.1 Run Unit Tests
```bash
# Run the complete test suite (41 tests):
pytest -v
```

### 3.2 Run Code Formatting & Linting
We use **[Ruff](https://docs.astral.sh/ruff/)** for fast, consistent linting and formatting:
```bash
# Check code style:
ruff check application/

# Check formatting:
ruff format --check application/

# Auto-format code if needed:
ruff format application/
```

### 3.3 Validate Terraform (If Modifying IaC)
```bash
# Check Terraform formatting:
terraform fmt -check -recursive terraform/

# Validate Dev environment without backend:
cd terraform/environments/dev
terraform init -backend=false
terraform validate
```

---

## 4. Submitting a Pull Request (PR)

1. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```
2. **Commit your changes**:
   Write clear, concise commit messages following conventional commits:
   - `feat: add QR code generation for short URLs`
   - `fix: handle edge case in URL protocol parsing`
   - `docs: improve Athena partition projection explanation`
3. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
4. **Open a Pull Request**:
   Go to GitHub and click **"New Pull Request"**. Fill out the PR template thoroughly.

---

## 5. Great Ideas for Contribution ("Good First Issues")

Looking for something to work on? Here are starter ideas that would add real value:

- [ ] **QR Code Generator Endpoint**: Add a `GET /urls/{short_code}/qr` endpoint that generates and returns a base64 or PNG QR code.
- [ ] **Bulk Shortening API**: Add a `POST /api/urls/bulk` endpoint to create up to 25 short links in a single request.
- [ ] **Custom Expiration Presets**: Support human-friendly strings like `1h`, `24h`, `7d`, `30d` in the request body.
- [ ] **Redis / ElastiCache Caching Layer**: Add a toggleable in-memory caching wrapper for the redirect Lambda.
- [ ] **Frontend Dark/Light Mode Switcher**: Add a toggle button on the web UI to switch themes.
