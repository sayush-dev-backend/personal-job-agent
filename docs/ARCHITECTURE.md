# Architecture

## Technology stack

- Python
- Typer CLI
- Pydantic
- `pydantic-settings`
- SQLite
- Gemini API initially
- pytest
- LaTeX for resume generation

## Architectural style and principles

The project uses a modular monolithic architecture. A single application coordinates cohesive modules, while each specialized module owns its respective business logic.

- The central orchestrator coordinates workflows; it does not absorb specialized business logic.
- The LLM provider boundary allows Gemini to be replaced without changing workflow logic.
- The CLI is a thin interface and remains separate from business logic.
- Dependency injection is used where it improves substitution and testing.
- The initial implementation is synchronous.
- No unnecessary frameworks, multi-agent systems, or premature abstractions are introduced.
- Configuration and secrets come from environment-backed settings rather than source code.

## Resume architecture

- The master LaTeX resume is immutable.
- Each application receives a separate tailored LaTeX source file.
- The tailored source is compiled into an application-specific PDF.
- Application-specific LaTeX and PDF versions are preserved for history and auditability.
- The system must never fabricate skills, experience, qualifications, or achievements.

## Repository modules

| Module | Responsibility | Current state |
| --- | --- | --- |
| `src/agent/` | Central orchestration and workflow coordination. | `ApplicationOrchestrator` accepts storage and LLM dependencies and initializes infrastructure. |
| `src/cli/` | Typer commands and command-line startup. | Provides `version` and `init-db`; no business workflow logic. |
| `src/config/` | Validated environment-backed configuration. | `Settings` supports the Gemini key, provider, model, database path, and resume storage path. |
| `src/jd/` | Job-description models, extraction, analysis, retrieval, and service coordination. | Models, text/PDF/URL extractors, `JDService`, `JDAnalyzer`, and the repository contract exist. Retrieval supports lookup, newest-first listing, analysis inspection, and status/error inspection. |
| `src/resume/` | Future LaTeX resume management and PDF compilation. | Boundary only; tailoring not implemented. |
| `src/outreach/` | Future recruiter outreach preparation and sending. | Boundary only; email automation not implemented. |
| `src/llm/` | Provider-independent LLM contract and provider adapters. | `LLMProvider` protocol and Gemini adapter skeleton exist; API operations are not implemented. |
| `src/storage/` | SQLite access and persistence infrastructure. | Database bootstrap creates the initial `applications` table; `SQLiteJDRepository` persists job-description records. |
| `tests/` | Unit and integration coverage for the foundation. | Covers settings, CLI startup, orchestrator initialization, SQLite persistence, extraction, analysis, retries, and retrieval inspection. |

The `config/` directory contains configuration guidance, while `data/` is reserved for private runtime data and resume artifacts. Both remain outside application business logic.

## Relationships

The CLI loads configuration and assembles dependencies for the orchestrator. The orchestrator coordinates specialized modules, including the LLM provider and storage boundary. `JDService` selects an injected extractor, normalizes its output, and persists a pending `JobDescription` through the `JDRepository` contract. Its `create_and_analyze` workflow then delegates the persisted record to `JDAnalyzer`, while `analyze` can retry an existing record without repeating extraction. `JDAnalyzer` requests schema-shaped JSON through the provider boundary, validates it with Pydantic, applies controlled output and transient retries, and persists a completed or failed status without discarding the source record. `JDService.get_by_id`, `list_all`, `get_analysis`, and `get_status` inspect persisted records without invoking extraction or analysis. SQLite provides persistence behind `SQLiteJDRepository`; records currently use integer auto-increment IDs, and typed provider errors keep authentication failures distinct from retryable rate-limit and transient failures.
