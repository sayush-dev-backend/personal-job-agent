# Personal Job Search Agent

Modular Python CLI foundation for job-description ingestion, analysis, retrieval, resume optimization, recruiter outreach, and application tracking.

## Status

JD ingestion, persistence, analysis workflows, and retrieval/inspection APIs are implemented. Resume tailoring, email sending, application tracking, and LinkedIn integration are not yet implemented. The current CLI exposes only startup commands; JD workflow commands remain future work.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
```

Set values in `.env` or in the environment. Secrets are represented with `SecretStr` and are never included in configuration output.

## Run

```bash
job-agent --help
job-agent version
job-agent init-db
```

The CLI is a thin entry point. `ApplicationOrchestrator` coordinates future workflows, while JD, resume, outreach, LLM, and storage modules own their respective boundaries. The LLM contract is provider-independent; Gemini is the initial adapter.

The JD service supports text, PDF, and URL ingestion, persisted analysis status/error inspection, lookup by ID, and newest-first listing through its Python API. The current SQLite schema uses integer auto-increment IDs.

The master LaTeX resume and generated application artifacts belong under the configured resume storage path. Runtime data is ignored by Git.

## Test

```bash
pytest
```

Tests use temporary directories and do not require a Gemini API key or network access.
