# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-03

### Added
- **Phase 0 — Local Environment Baseline**: Verified tools (AWS CLI 2.36.7, Terraform 1.15.8, Python 3.13.0, Git 2.44.0). Captured credentials in `PROJECT_ENVIRONMENT.md` (`ap-south-1`, account `********6081`).
- **Phase 1 — System Architecture**: Produced `docs/architecture.md` with complete Mermaid request and async SQS telemetry flows.
- **Phase 2 — Project Structure**: Structured clean multi-component repository.
- **Phase 3 — Core URL Shortener (MVP)**: Implemented Base62 generation, RFC-compliant URL validation, DynamoDB conditional writes, and soft-deletion in `application/src/`.
- **Phase 4 — DynamoDB Design**: Single-table schema on `dev-urls` with native TTL on `expires_at` in `docs/database-design.md`.
- **Phase 5 — Asynchronous Analytics**: Decoupled click events via Amazon SQS (`dev-click-events`) and batch ingestion Lambda to S3 partitioned NDJSON (`docs/analytics.md`).
- **Phase 6 — Serverless SQL Queries**: Created `application/src/services/athena_queries.sql` and `docs/analytics-queries.md` utilizing Athena Partition Projection.
- **Phase 7 — Frontend Application**: Responsive, dependency-free vanilla HTML/JS/CSS client in `frontend/`.
- **Phase 8 — Modular Terraform & State Backend**: 9 reusable modules. Created remote state S3 bucket (`dev-tfstate-197550036081`) and DynamoDB lock table (`dev-tfstate-locks`).
- **Phase 9 — DevSecOps & Security**: IAM least-privilege policies, S3 encryption/public-block, and Checkov controls in `docs/security.md`.
- **Phase 10 — CI/CD Automation**: GitHub Actions workflows (`ci.yml`, `security.yml`, `terraform.yml`, `deploy.yml`) with automated rollback handling.
- **Phase 11 — CloudWatch Observability**: Alarms for 5XX errors, DLQ poison messages, and DynamoDB throttling; consolidated operations dashboard in `monitoring/`.
- **Phase 12 — FinOps & Cost Awareness**: Empirical AWS pricing model in `finops/cost-model.md` (\$1.88/1M requests), \$10.00 AWS Budget ceiling, and S3 lifecycle rules.
- **Phase 13 — Reliability Engineering**: Non-blocking redirect path, DLQ routing, and idempotent S3 storage in `docs/reliability.md`.
- **Phase 14 — Performance Profiling**: Latency benchmarks (p50: 2.04ms PutItem, 3.36ms GetItem) in `docs/performance.md`.
- **Phase 15 — Failure Testing Matrix**: Documented 10 real-world failure scenarios and automatic recovery paths in `docs/failure-testing.md`.
- **Phase 16 — Disaster Recovery**: < 15-minute IaC rebuild runbook in `docs/disaster-recovery.md`.
- **Phase 17 — Live AWS Verification**: Successfully deployed and validated real AWS DynamoDB table, SQS queue, and S3 storage in `ap-south-1` with 100% passing tests.
- **Phase 18 — Complete Project Documentation**: Natural, comprehensive `README.md`, setup guides, and runbooks.
