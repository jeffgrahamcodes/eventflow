
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
├── tests/                # Test suite mirrors src/ structure
├── docs/                 # Architecture diagrams and ADRs
├── pyproject.toml        # Project config, dependencies, tool settings
└── CONTRIBUTING.md       # Branching strategy and commit conventions
```
