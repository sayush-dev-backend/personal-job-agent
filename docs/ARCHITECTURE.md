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
| `src/jd/` | Future job-description ingestion and analysis. | Boundary only; workflow not implemented. |
| `src/resume/` | Future LaTeX resume management and PDF compilation. | Boundary only; tailoring not implemented. |
| `src/outreach/` | Future recruiter outreach preparation and sending. | Boundary only; email automation not implemented. |
| `src/llm/` | Provider-independent LLM contract and provider adapters. | `LLMProvider` protocol and Gemini adapter skeleton exist; API operations are not implemented. |
| `src/storage/` | SQLite access and persistence infrastructure. | Database bootstrap creates the initial `applications` table. |
| `tests/` | Unit and integration coverage for the foundation. | Covers settings, CLI startup, orchestrator initialization, and SQLite initialization. |

The `config/` directory contains configuration guidance, while `data/` is reserved for private runtime data and resume artifacts. Both remain outside application business logic.

## Relationships

The CLI loads configuration and assembles dependencies for the orchestrator. The orchestrator coordinates specialized modules, including the LLM provider and storage boundary. Future JD, resume, and outreach workflows will depend on interfaces and validated models rather than CLI-specific code. SQLite provides initial persistence, and the LLM provider protocol isolates workflow code from Gemini-specific details.
