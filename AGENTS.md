# Project Development Rules

## 1. Project and authority

This repository contains the Enterprise AI Business Development Agent Platform. Sari Arta, an
Indonesian commercial-kitchen engineering business, is the first operating domain. The platform now
includes CRM, domain agents, governed knowledge, read-only assistance, public consultation, governed
marketing drafts, and a technical search-discovery foundation.

Optimize for real business use, maintainability, a credible demonstration, and delivery by one
developer or a small team. Make routine technical decisions autonomously within the current roadmap.
Human approval is required only for the material actions listed in section 9.

Authority order:

1. Explicit current user instruction.
2. This `AGENTS.md`.
3. `docs/PROJECT_CONTEXT.en.md` for current state and boundaries.
4. `docs/roadmap.md` when phase scope or implementation order is relevant.
5. The task-specific English design document.

English engineering documents control implementation when documents conflict.

## 2. Lightweight context loading

For a normal task, read only:

1. `AGENTS.md`.
2. `docs/PROJECT_CONTEXT.en.md`.
3. At most one directly relevant English design document, unless the task genuinely spans more.
4. Directly relevant source files and targeted tests.

Do not automatically read:

- Chinese translations;
- `CHANGELOG` or completed-phase history;
- the full roadmap when current scope is already clear;
- unrelated architecture or domain documents;
- entire test suites, historical migrations, evaluation fixtures, or demo data;
- generated artifacts, dependency directories, lockfiles, or binary assets.

Use `rg` to locate code, then read the smallest useful ranges. Read a broader file or document only
when a concrete dependency, security boundary, contract, or conflict requires it. Briefly state why
before materially expanding the review scope.

Do not repeat project history in progress updates or handoffs. Reference the project context instead.

## 3. Business and safety boundary

Sari Arta sells commercial-kitchen engineering solutions. The system captures inquiries, organizes
companies and contacts, qualifies leads, manages follow-up and opportunities, reuses approved
knowledge, and prepares governed drafts.

Human users remain responsible for customer relationships, qualification decisions, pricing,
discounts, technical validation, delivery commitments, contracts, proposal approval, publishing,
and external communication.

AI may classify, summarize, retrieve, recommend, and draft. It must not invent prices, technical
specifications, customer cases, compliance claims, delivery commitments, or contractual terms.

Use synthetic or explicitly approved data in development, tests, prompts, screenshots, and demos.
Never expose secrets, credentials, private customer data, or hidden model reasoning.

## 4. Architecture principles

- Use the existing Next.js frontend, FastAPI backend, PostgreSQL/pgvector database, Redis workers,
  OpenAI Agents SDK boundary, n8n boundary, and Docker packaging.
- Keep a modular monolith unless microservices are explicitly approved.
- PostgreSQL is canonical business state. Prompts, Redis, browser state, traces, and n8n are not.
- Deterministic application services validate and perform transactions.
- AI tools must be narrow and typed; never expose generic SQL, shell, unrestricted HTTP, secrets, or
  unrestricted files.
- Do not hold database transactions open during model, file, queue, or provider calls.
- Preserve manual CRM operation when AI or external providers fail.
- Enforce tenant isolation, RBAC, object authorization, PostgreSQL RLS, auditability, idempotency,
  correlation IDs, and deny-by-default knowledge/agent bindings.
- Authorize before embedding, retrieval, model, or external-provider calls.
- Public agents and pages must never gain access to internal knowledge, CRM reads, pricing, or private
  business tools through convenience shortcuts.
- Do not introduce microservices, Kubernetes, a separate vector database, local GPU infrastructure,
  or dynamic multi-model routing without explicit approval.

## 5. Implementation standards

### General

- Inspect before editing and preserve unrelated user changes.
- Implement the smallest complete vertical slice and preserve existing behavior unless requested.
- Use descriptive business names, UTC timestamps, UUID business IDs, and exact decimal money values
  with currency.
- Keep configuration outside business logic and secrets outside source, logs, fixtures, and prompts.
- Use structured safe errors and logs with correlation IDs.
- Remove dead code; avoid speculative abstractions and unexplained production TODOs.

### Frontend

- Use Next.js, strict TypeScript, accessible components, and FastAPI for all business data.
- Prefer server-rendered authenticated data; use client components only for interaction.
- Validate forms in both UI and API.
- Provide loading, empty, success, and error states.
- Clearly label AI output, evidence, confidence, and review status.

### Backend and API

- Use typed FastAPI schemas, thin routes, application services, repository boundaries, SQLAlchemy 2.x,
  and Alembic migrations.
- Keep REST endpoints under `/api/v1`, JSON fields in `snake_case`, and OpenAPI accurate.
- Use idempotency for retry-sensitive commands and optimistic concurrency for editable records.
- Return safe Problem Details-compatible errors; do not expose arbitrary prompts, tools, SQL, model
  choice, storage keys, or provider internals.

### Database and agents

- Every schema change needs a new non-destructive migration; never edit an applied migration.
- Add constraints and indexes for real invariants and query patterns.
- Store files in private object storage and references in PostgreSQL.
- Keep agent instructions, tools, schemas, provider configuration, and results versionable.
- Validate structured AI output; treat insufficient evidence as valid; require citations for factual
  knowledge answers.
- Record safe agent status, provider/model, timing, outcome, and failure details.

## 6. Proportional validation

### Small change

Run only the narrowest relevant checks:

- targeted regression/unit tests;
- lint for affected Python or frontend files;
- type checking when a typed contract changed;
- a focused browser or API check when the behavior is user-facing.

Do not run full suites, production builds, Docker builds, or broad migration checks by default.

### Sub-phase completion

Run the affected application's full tests, lint, and type checks. Run a production frontend build
only for routing, rendering, dependency, or build-configuration changes. Run database integration and
migration checks only when persistence changed.

### Milestone or release acceptance

Run full affected regression suites, production build, migration-from-clean-state checks, critical
end-to-end paths, and Docker/deployment validation where relevant. Security, RLS, backup/restore, and
production-readiness checks belong here or in explicitly high-risk tasks.

Do not claim checks that were not run. Keep successful output summarized; include detailed logs only
for actionable failures.

## 7. Documentation policy

- English `*.en.md` files are the active engineering baseline during implementation.
- Existing Chinese documents remain valid review snapshots; do not read or update them for routine
  development.
- Synchronize a complete Chinese translation only at a sub-phase/milestone acceptance point, when a
  business review needs it, or when the user explicitly requests it.
- High-risk security, privacy, approval, pricing, contractual, or production-policy changes should be
  translated for the corresponding human review before activation.
- Do not update design documents for implementation details already clear in code and tests.
- Do not update `PROJECT_CONTEXT` or `CHANGELOG` for bug fixes, minor UI changes, routine refactors,
  dependencies, or test-only work.
- Update `PROJECT_CONTEXT.en.md` only for a material capability, architecture boundary, phase status,
  or production gate. Update `CHANGELOG` only for completed meaningful milestones.
- Preserve identifiers, diagrams, tables, code blocks, API paths, and terminology when translation is
  eventually synchronized.

## 8. Autonomous development

When implementation is requested, the engineering agent may inspect the worktree; modify directly
required files; add targeted tests; run proportional non-destructive validation; use isolated local
migrations and synthetic fixtures; update required English documentation; and make routine choices
within the approved stack.

Do not autonomously:

- expand beyond the current task or roadmap boundary;
- add a material paid, licensed, security-sensitive, or operational dependency;
- replace approved Supabase authentication/data or the approved AI-provider policy;
- access/import real customer data;
- send emails, WhatsApp messages, social posts, proposals, or notifications to real recipients;
- deploy, publish, push, merge, create a PR, or mutate production infrastructure;
- run destructive database/file operations or overwrite unrelated work;
- weaken authentication, authorization, validation, audit, backup, privacy, or human review;
- activate production Marketing Content generation or automatic publication while its business
  acceptance remains deferred.

## 9. Human approval requirements

Obtain explicit approval before:

- material scope expansion or a new third-party integration;
- a production dependency or provider-policy change with security, cost, licensing, or operational
  impact;
- destructive/difficult-to-reverse migration;
- real customer data access or external AI data-policy change;
- production deployment, infrastructure mutation, publication, external sending, or material cost;
- changes to security, retention, privacy, backup, pricing, contracts, technical commitments, or
  communication consent policy.

The product must require human review of the exact content before accepting consequential AI
qualification decisions, publishing marketing content, sending customer communications, sharing a
proposal, issuing commercial/technical commitments, or executing any external action. If reviewed
content changes, its approval becomes invalid.

## 10. Completion standard

A task is complete when the requested bounded behavior is implemented, relevant proportional checks
pass, authorization and failure behavior are considered, manual fallback and human controls remain
intact, required English documentation is current, and the handoff concisely states changes, checks,
limitations, and any deferred milestone-level translation or validation.
