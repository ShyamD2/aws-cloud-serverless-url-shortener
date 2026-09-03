# Project Environment & Configuration Baseline

This document serves as the single source of truth for the local development environment, AWS account, and region configuration. All subsequent phases reuse these exact parameters.

---

## AWS Configuration Context

| Parameter | Value | Notes |
| :--- | :--- | :--- |
| **AWS Account ID** | `********6081` (`197550036081`) | Masked in documentation; validated via STS |
| **AWS Region** | `ap-south-1` (Asia Pacific - Mumbai) | Default region configured in AWS CLI profile |
| **Caller Identity ARN** | `arn:aws:iam::197550036081:user/dev-cli-user` | IAM User identity |
| **IAM User** | `dev-cli-user` | Non-root developer user |
| **Authentication Status** | Verified & Active | Verified via `aws sts get-caller-identity` |

---

## Tooling & Environment Verification

| Tool | Installed | Version | Status / Notes |
| :--- | :---: | :--- | :--- |
| **AWS CLI** | Yes | `2.36.7` (Python 3.14.6) | Operational |
| **Terraform** | Yes | `1.15.8` (windows_amd64) | Operational |
| **Python** | Yes | `3.13.0` | Operational |
| **pip** | Yes | `26.2.1` | Operational |
| **Git** | Yes | `2.44.0.windows.1` | Operational |
| **Docker** | Yes | `29.7.2` | Operational |
| **Node.js** | Yes | `v21.6.1` | Operational |
| **npm** | Yes | `10.2.4` | Operational |
| **curl** | Yes | `8.21.0` (Windows) | Operational |
| **jq** | No | N/A | Windows environment; PowerShell `ConvertFrom-Json` & `python -m json.tool` available |

---

## Environment Constraints & Principles
1. **Region Pinning**: All cloud resources must be created in `ap-south-1`.
2. **Account Pinning**: All IAM policies, S3 bucket policies, and ARNs must align with account `197550036081`.
3. **No Secrets in Repo**: No credentials, access keys, or secrets are stored in this or any other committed file.
