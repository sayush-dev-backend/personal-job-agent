# Architecture Decision Log

This document records established architecture decisions. All decisions below have status **Accepted**. Dates are intentionally not recorded.

## ADR-001: Build Phase 1 before Phase 2

**Decision:** Complete the personal application workflow in Phase 1 before implementing Phase 2 discovery and broader outreach capabilities.

**Reasoning:** The core application workflow establishes the data, resume, approval, and tracking foundations required by later discovery and outreach features.

**Status:** Accepted

## ADR-002: CLI before a web dashboard

**Decision:** Deliver the command-line interface before building a web dashboard.

**Reasoning:** A CLI is sufficient for initial personal use and keeps the first delivery focused on business capabilities rather than presentation infrastructure.

**Status:** Accepted

## ADR-003: Gemini as the initial LLM provider

**Decision:** Use the Gemini API as the initial LLM provider.

**Reasoning:** Gemini is the selected initial provider for the project's analysis and generation capabilities.

**Status:** Accepted

## ADR-004: Provider abstraction for future model replacement

**Decision:** Access LLM functionality through a provider abstraction rather than coupling business logic directly to Gemini.

**Reasoning:** A replaceable boundary allows another provider to be introduced without rewriting workflow logic.

**Status:** Accepted

## ADR-005: SQLite for initial persistence

**Decision:** Use SQLite for initial application persistence.

**Reasoning:** SQLite provides durable local storage with minimal operational overhead for a personal, initially single-user application.

**Status:** Accepted

## ADR-006: LaTeX as the canonical resume source

**Decision:** Treat LaTeX as the canonical source format for resumes.

**Reasoning:** The existing resume workflow is based on LaTeX and requires controlled generation of application-specific source and PDF artifacts.

**Status:** Accepted

## ADR-007: Master resume must remain immutable

**Decision:** Never modify the master LaTeX resume during application-specific tailoring.

**Reasoning:** An immutable source preserves the authoritative resume and makes each tailored application reproducible and auditable.

**Status:** Accepted

## ADR-008: Human approval before sending outreach

**Decision:** Require explicit human approval before recruiter outreach is sent.

**Reasoning:** The user must review generated claims, tone, recipients, attachments, and final content before an external message is transmitted.

**Status:** Accepted

## ADR-009: No LinkedIn automation in Phase 1

**Decision:** Exclude LinkedIn automation from Phase 1.

**Reasoning:** LinkedIn outreach belongs to the deferred Phase 2 scope and should not expand the initial implementation boundary.

**Status:** Accepted

## ADR-010: Avoid unnecessary multi-agent frameworks

**Decision:** Do not introduce LangChain, LangGraph, or similar multi-agent frameworks without a demonstrated requirement.

**Reasoning:** The initial system is a modular monolith with a central orchestrator; additional orchestration frameworks would add complexity before the product requires it.

**Status:** Accepted
