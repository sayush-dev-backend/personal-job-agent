# Project Overview

## Vision

Personal Job Search Agent is a modular assistant for preparing, reviewing, and tracking job applications. It is designed to reduce repetitive application work while keeping the user in control of claims, generated materials, and outreach.

## Problem

Preparing applications across many job descriptions requires repeated comparison of requirements, resume editing, recruiter-message drafting, attachment preparation, and status tracking. The agent will centralize these activities and preserve an auditable version of each application.

## Primary user

The initial user is the project owner, using the system for personal job searches. The architecture should remain modular enough to support later evolution without assuming a multi-user product today.

## Core capabilities

Phase 1 is intended to support:

- Job description ingestion and analysis.
- Resume tailoring based on a job description.
- Recruiter email personalization.
- Resume attachment and email preparation.
- Human approval before any outreach is sent.
- Application history and tracking.

The master resume remains the source of truth. Application-specific resumes and generated communication are separate artifacts and must not introduce unsupported claims.

## Phases

### Phase 1 — Personal application workflow

Phase 1 covers the core workflow from a job description through tailored application materials, approved recruiter outreach preparation, and application tracking. It includes the foundation already established in the repository and the future JD, resume, outreach, and tracking capabilities listed above.

### Phase 2 — Discovery and broader outreach

Phase 2 is deferred until Phase 1 is complete. Its planned scope includes startup and YC founder discovery and LinkedIn outreach.

## Current out of scope

The current implementation is project foundation only. The following are not implemented:

- Job description analysis.
- Resume tailoring or PDF compilation workflows.
- Recruiter email generation or sending.
- LinkedIn integration or automation.
- Startup or YC founder discovery.
- A web dashboard.
- Autonomous sending without human approval.
- Multi-agent orchestration.
