# Contributing to EventFlow

## Branching Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code only. Never commit directly. |
| `develop` | Integration branch. All features merge here first. |
| `feature/EF-XXX-short-description` | One branch per Linear ticket. |

## Workflow

1. Branch off `develop`:
```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/EF-XXX-short-description
```

2. Do your work. Commit with the ticket ID in the message:
```bash
   git commit -m "EF-XXX: What you did"
```

3. Push and open a PR into `develop`:
```bash
   git push -u origin feature/EF-XXX-short-description
```

4. Merge to `main` only when a sprint is complete and the build is clean.

## Commit Message Format
```
EF-XXX: Short description in imperative mood

Optional longer explanation if needed.
```

Examples:
- `EF-003: Add order lifecycle event flow diagram`
- `EF-005: Build Pydantic event models with full type hints`
