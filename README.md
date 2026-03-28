# EventFlow

A production-grade, event-driven order processing platform built on AWS 
serverless — and a developer platform layered on top of it.

EventFlow demonstrates event-driven architecture using Python, Pydantic v2, 
and AWS (EventBridge, SQS, Lambda, DynamoDB). It is designed as a reference 
implementation, not a tutorial project.

## Architecture

*Diagram coming in Sprint 3 — AWS infrastructure phase.*

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (package manager)
- Git

### Installation

Clone the repo and install dependencies:
```bash
git clone git@github.com:jeffgrahamcodes/eventflow.git
cd eventflow
uv sync --extra dev
```

### Run the tests
```bash
uv run pytest
```

### Run the linter
```bash
uv run ruff check .
```

### Run the type checker
```bash
uv run mypy src/
```

### Project Structure
```
eventflow/
├── src/
│   └── eventflow/        # Application source
│       └── events/       # Domain event models
├── tests/                # Test suite mirrors src/ structure
├── docs/
│   ├── adr/              # Architecture Decision Records
│   └── diagrams/         # Event flow and architecture diagrams
├── infra/                # AWS CDK infrastructure (Sprint 3)
├── pyproject.toml        # Project config, dependencies, tool settings
└── CONTRIBUTING.md       # Branching strategy and commit conventions
```

## Architecture Decisions

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](docs/adr/ADR-001-event-schema-design.md) | Event Schema Design | Accepted |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12 |
| Event schemas | Pydantic v2 |
| Package manager | uv |
| Linter / formatter | ruff |
| Type checker | mypy |
| Testing | pytest |
| Cloud | AWS (EventBridge, SQS, Lambda, DynamoDB) — Sprint 3 |
| IaC | AWS CDK (TypeScript) — Sprint 3 |