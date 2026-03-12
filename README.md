# AWS Production Platform

[![CI/CD Pipeline](https://github.com/elishambiro/aws-production-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/elishambiro/aws-production-platform/actions/workflows/ci.yml)
[![Terraform](https://img.shields.io/badge/Terraform-1.7-purple?logo=terraform)](https://www.terraform.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11-green?logo=python)](https://www.python.org/)

A production-ready infrastructure platform demonstrating modern DevOps practices using AWS services (via LocalStack), Terraform IaC, Docker, and a full observability stack.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Actions CI/CD                  │
│  Terraform Validate → Build & Test → Push to Docker Hub │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    Docker Compose                        │
│                                                          │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │  Flask   │───▶│  LocalStack  │    │  Prometheus   │  │
│  │  App     │    │  (AWS Mock)  │    │  (Metrics)    │  │
│  │ :5000    │    │    :4566     │    │    :9090      │  │
│  └────┬─────┘    │              │    └──────┬────────┘  │
│       │          │  S3          │           │           │
│       │          │  DynamoDB    │    ┌──────▼────────┐  │
│       └─────────▶│  SQS        │    │    Grafana    │  │
│                  │  IAM         │    │  (Dashboard)  │  │
│                  └──────────────┘    │    :3000      │  │
│                                      └───────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Category | Technology |
|---|---|
| **IaC** | Terraform |
| **Cloud (Local)** | LocalStack (AWS S3, DynamoDB, SQS, IAM) |
| **Containers** | Docker, Docker Compose |
| **App** | Python, Flask |
| **Monitoring** | Prometheus, Grafana |
| **CI/CD** | GitHub Actions |
| **Testing** | pytest |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Terraform >= 1.0

### Run locally

```bash
# Clone the repo
git clone https://github.com/elishambiro/aws-production-platform.git
cd aws-production-platform

# Start all services
docker compose up -d

# Wait ~30 seconds for LocalStack and Terraform to initialize, then:
curl http://localhost:5000/health
```

### Services

| Service | URL | Description |
|---|---|---|
| Flask App | http://localhost:5000 | REST API |
| Prometheus | http://localhost:9090 | Metrics |
| Grafana | http://localhost:3000 | Dashboards (admin/admin) |
| LocalStack | http://localhost:4566 | AWS Mock |

## API Endpoints

```
GET  /health       → Health check
GET  /metrics      → Prometheus metrics
GET  /items        → List all items (DynamoDB)
POST /items        → Create item (DynamoDB + SQS)
DELETE /items/:id  → Delete item
```

### Example

```bash
# Create an item
curl -X POST http://localhost:5000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "example", "value": "hello"}'

# List items
curl http://localhost:5000/items
```

## Infrastructure (Terraform)

```hcl
# Provisions:
aws_s3_bucket          → Asset storage with versioning
aws_dynamodb_table     → Items table (on-demand billing)
aws_sqs_queue          → Async message queue
aws_iam_role           → Least-privilege access policy
```

Run Terraform manually:
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## CI/CD Pipeline

```
push to master
      │
      ▼
┌─────────────────┐
│ Terraform       │  fmt check + validate
│ Validate        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Build & Test    │  docker build → stack up → pytest
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Push to         │  tag with SHA + latest
│ Docker Hub      │
└─────────────────┘
```

## Monitoring

Grafana comes pre-configured with:
- HTTP request rate per endpoint
- Request latency (p95)
- Total items created counter
- Error rate

Access at http://localhost:3000 (admin/admin)

## Running Tests

```bash
pip install pytest requests
docker compose up -d
pytest tests/ -v
```
