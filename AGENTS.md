# Project Development Rules

## 1. Project overview

This repository contains the Enterprise AI Business Development Agent Platform.

The first delivery is a usable internal MVP for Sari Arta, an Indonesian commercial-kitchen engineering business. Phase 1 supports the workflow:

```text
Capture lead → review and qualify → convert to opportunity
```

The current goal is not to build a general enterprise SaaS platform. Optimize for:

- Real business use.
- Fast, maintainable implementation.
- A credible portfolio demonstration.
- Clear AI-agent capability.
- Delivery by one developer or a small team.

The project owner has delegated ordinary technical design, MVP tradeoffs, database/API details, page structure, testing strategy, and implementation order to the AI engineering agent. Make reasonable documented decisions and continue without requesting technical review unless a decision would trigger one of the explicit approval conditions in section 9.

Use these documents as the design baseline:

- `docs/roadmap.md` — authoritative phase boundaries and progress.
- `docs/mvp-scope.md` — current delivery boundary and implementation order.
- `docs/technical-architecture.md` — long-term architecture direction.
- `docs/database-design.md` — long-term data model.
- `docs/api-design.md` — long-term API design.
- `docs/review-guide.zh-CN.md` — Chinese business review guidance.

When the enterprise documents conflict with the roadmap or MVP scope, follow `docs/roadmap.md` and then `docs/mvp-scope.md` unless a human explicitly changes the current scope.

## 2. Business context

Sari Arta sells commercial-kitchen engineering solutions. Its sales process involves:

- Receiving inquiries from potential customers.
- Recording companies, contacts, project locations, timelines, and requirements.
- Determining whether a project is commercially qualified.
- Following up through tasks and sales activities.
- Reusing approved company, product, capability, and case-study knowledge.
- Preparing a professional project proposal.

Commercial-kitchen projects may involve incomplete requirements, multiple stakeholders, technical documents, substantial values, and long sales cycles. The system must help salespeople work faster without allowing AI to invent prices, delivery commitments, technical guarantees, or contractual terms.

Human users remain responsible for:

- Customer relationships.
- Qualification acceptance.
- Commercial judgment.
- Pricing and discounts.
- Technical validation.
- Proposal approval.
- External communication.

## 3. Role of the AI engineering agent

Act as a senior product-minded engineering agent responsible for turning approved requirements into small, correct, reviewable changes.

For each task:

1. Read the relevant repository instructions and design documents.
2. Inspect the existing implementation before proposing or making changes.
3. Identify the smallest vertical slice that satisfies the request.
4. Preserve existing behavior unless the task explicitly changes it.
5. Implement within the current MVP boundary.
6. Add or update tests and documentation in proportion to risk.
7. Run relevant non-destructive validation.
8. Report what changed, what was verified, and any unresolved decision.

Do not act as an autonomous salesperson or business decision-maker. For ordinary product details, use the defaults in `docs/mvp-scope.md` and document any additional reasonable assumption. Stop only when missing information affects real customer data, external communication, pricing, contractual or technical commitments, material cost, production deployment, or AI safety.

## 4. Development principles

### 4.1 MVP before platform

- Build only what supports the current lead-to-proposal workflow.
- Prefer one clear implementation over a configurable framework.
- Prefer explicit workflows over generic workflow builders.
- Prefer one Sari Arta workspace over tenant-management features.
- Prefer one tested model-provider path over dynamic multi-model routing.
- Postpone extensibility until a repeated business need is demonstrated.

Retaining a simple future-compatible boundary is acceptable. Building the future feature is not.

### 4.2 Modular monolith

- Use one Next.js frontend and one FastAPI backend.
- Keep backend modules separated by business capability.
- Use one PostgreSQL database as the business system of record.
- Use an asynchronous worker for long-running work.
- Keep n8n outside core business-rule and transaction ownership.
- Do not introduce microservices or Kubernetes without explicit approval.

### 4.3 Business data over prompt state

- PostgreSQL is the canonical source for leads, opportunities, tasks, knowledge metadata, agent runs, and proposals.
- Agent memory, prompts, traces, Redis, and n8n executions are not canonical business state.
- Do not store unique business facts only in logs, queues, browser state, model context, or workflow definitions.

### 4.4 Deterministic services control transactions

- AI may classify, summarize, retrieve, recommend, and draft.
- Application services validate and perform business reads and writes.
- AI tools must be narrow, typed wrappers around application services.
- Agents must not receive generic SQL, shell, unrestricted HTTP, secret-reading, or unrestricted file tools.
- Validate structured AI output before saving or showing it as a business result.

### 4.5 Human control and manual fallback

- AI features must not block manual CRM operation.
- AI output must be visibly labeled and editable where appropriate.
- Unsupported or low-confidence results must be allowed to escalate to a human.
- Proposal output remains a draft until human confirmation.
- Failure of an AI provider or n8n must not corrupt CRM state.

### 4.6 Security and privacy by default

- Apply least privilege.
- Validate authorization server-side.
- Treat user text, uploaded documents, retrieved content, and provider output as untrusted.
- Minimize data sent to external AI or integration providers.
- Never place secrets in source code, prompts, logs, fixtures, screenshots, or committed environment files.
- Use synthetic or anonymized data for development and tests.

### 4.7 Simple operations

- Prefer Docker Compose for the MVP deployment.
- Prefer managed PostgreSQL and private object storage in production.
- Make background work observable and retryable.
- Add health checks, structured logs, and tested restore procedures before real use.
- Back up the database and uploaded object files separately.
- Do not add infrastructure solely for theoretical scale.

## 5. Coding standards

These standards apply once application implementation begins.

### 5.1 General

- Keep changes small, cohesive, and easy to review.
- Use descriptive names based on business language.
- Avoid premature abstraction and speculative extension points.
- Remove dead code instead of commenting it out.
- Do not leave unexplained TODOs in production paths.
- Keep configuration outside business logic.
- Store timestamps in UTC and expose RFC 3339 values.
- Use UUIDs for externally visible business identifiers.
- Use exact decimal types for money and always store currency.
- Never use floating-point values for commercial amounts.
- Use structured logging; do not log secrets, tokens, raw credentials, or unnecessary customer data.

### 5.2 Frontend

- Use Next.js with TypeScript strict mode.
- Prefer server-rendered data loading for authenticated pages.
- Use client components only when interaction requires them.
- Access business data through FastAPI; never connect the frontend directly to PostgreSQL.
- Generate or maintain frontend API types from the OpenAPI contract.
- Keep server data separate from local UI state.
- Validate forms in the UI for usability and again in the API for correctness.
- Provide loading, empty, success, and error states.
- Meet a practical WCAG 2.1 AA accessibility target.
- Clearly label AI-generated content, citations, confidence, and review status.

### 5.3 Backend

- Use modern Python with complete type hints for public functions and service boundaries.
- Use FastAPI request/response schemas and strict validation.
- Keep route handlers thin.
- Put authorization, business transitions, and transaction boundaries in application services.
- Keep persistence behind repository or data-access boundaries.
- Use SQLAlchemy 2.x-style access and Alembic migrations unless a later approved decision replaces them.
- Do not hold database transactions open during model, file-processing, n8n, or external-provider calls.
- Make retry-sensitive writes idempotent.
- Use optimistic concurrency for records that users may edit simultaneously.
- Return safe, structured errors with a correlation ID.

### 5.4 Database

- Use PostgreSQL and pgvector for the MVP.
- Use lowercase `snake_case` names.
- Add foreign keys and database constraints for important invariants.
- Add indexes for demonstrated query patterns, not speculation.
- Every schema change requires a migration.
- Migrations must preserve existing data and support the deployed application transition.
- Never edit an already-applied migration.
- Do not use destructive schema or data operations without explicit human approval and a recovery plan.
- Store files in private object storage; store only metadata and references in PostgreSQL.

### 5.5 AI agents

- Use the OpenAI Agents SDK as the orchestration layer.
- Implement one explicit Phase 1 workflow:
  - Lead Qualification Agent.
- Add the Knowledge Assistant, Content Generation Agent, and Proposal Assistant only in Phase 2.
- Keep instructions, tools, schemas, and model configuration versionable.
- Expose only tools required by the current workflow.
- Set time, token, tool-call, and retry limits.
- Record agent run status, model/provider, duration, structured result, and safe failure details.
- Require citations for knowledge-based factual answers.
- Treat “insufficient evidence” as a valid result.
- Do not expose hidden model reasoning.
- Test agents using representative, anonymized Sari Arta cases.
- Do not add a coordinator agent, handoffs, autonomous follow-up, dynamic model routing, or local inference infrastructure in Version 1 without approval.

### 5.6 API

- Place MVP REST endpoints under `/api/v1`.
- Use JSON with `snake_case` fields.
- Use cursor pagination for growing collections.
- Require idempotency keys for retry-sensitive commands.
- Use `ETag`/`If-Match` or explicit versions for concurrency-sensitive updates.
- Follow a Problem Details-compatible error structure.
- Do not expose arbitrary prompts, system instructions, tools, SQL, storage keys, or model selection to ordinary API callers.
- Keep the OpenAPI document accurate and review contract changes for compatibility.

### 5.7 Testing and quality

- Add unit tests for business rules and state transitions.
- Add repository/integration tests for PostgreSQL behavior.
- Add API tests for authentication, authorization, validation, idempotency, and error responses.
- Add agent contract tests for structured output, tool permissions, citations, and safe failure.
- Add a small number of end-to-end tests for the critical lead-to-proposal path.
- Every bug fix should include a regression test when practical.
- Run the narrowest relevant checks during iteration and the broader affected suite before handoff.
- Do not claim verification that was not actually run.

### 5.8 Documentation

- Update design or operational documentation when behavior, data, API contracts, deployment, or security assumptions change.
- Keep English technical documents as the implementation baseline.
- Update the Chinese review guide when a change materially affects business review.
- Record important architecture decisions and tradeoffs rather than relying on chat history.

## 6. Technology stack

### Application

- Frontend: Next.js and TypeScript.
- Backend: FastAPI and Python.
- Database: PostgreSQL with pgvector.
- AI orchestration: OpenAI Agents SDK.
- Automation: n8n for limited notifications and reminders.
- Packaging/deployment: Docker and Docker Compose for MVP.

### Supporting services

- Redis for the asynchronous job queue when implementation begins.
- Private S3-compatible object storage for uploaded and generated files.
- One approved model-provider path for Version 1.
- Structured application logs and basic health monitoring.

### Testing and tooling direction

- Python tests: pytest.
- Frontend unit/component tests: the repository-selected TypeScript test runner and Testing Library.
- End-to-end tests: Playwright.
- Python lint/format: Ruff.
- Python type checking: mypy or Pyright, selected once and used consistently.
- TypeScript lint/format: ESLint and the repository-selected formatter.

Pin runtime and dependency versions when the project is scaffolded. Do not introduce competing tools for the same responsibility without a documented reason.

## 7. Current MVP objectives

Version 1 must provide:

- One seeded Sari Arta workspace.
- Secure admin and sales access.
- Manual and website lead capture.
- Customer-company and contact records.
- Lead list, detail, status, priority, ownership, tasks, and activity history.
- Structured AI lead qualification with human review.
- Lead-to-opportunity conversion.
- Simple opportunity list and stage visibility.
- Dashboard with actionable lead, task, and opportunity metrics.
- Agent-run status and safe retry.
- Dockerized production deployment, separate database/file backups, logs, and health checks.

Version 1 does not include:

- Self-service or configurable SaaS tenancy.
- Full WhatsApp, email, or social inbox synchronization.
- Autonomous external sending or follow-up.
- RAG knowledge ingestion and Knowledge Assistant.
- Content Generation Agent.
- Proposal Assistant and proposal generation.
- n8n business automation.
- Customer Research Agent.
- Multi-agent coordination or handoffs.
- Dynamic multi-model routing.
- Local-model GPU infrastructure.
- Advanced pricing, contracts, ERP, accounting, analytics, or compliance automation.
- Kubernetes or multi-region deployment.

When uncertain whether a feature belongs in Version 1, treat it as postponed and consult `docs/mvp-scope.md`.

## 8. Rules for autonomous development

### 8.1 Actions allowed without additional approval

When the user has requested implementation, the AI engineering agent may:

- Read repository files and inspect the current worktree.
- Create or modify files directly required by the requested MVP task.
- Add tests for changed behavior.
- Run non-destructive linters, formatters, type checks, tests, local builds, and read-only diagnostics.
- Run migrations against an isolated local or test database.
- Create reversible development fixtures using synthetic data.
- Update relevant documentation.
- Refactor the smallest necessary area when required to implement or test the requested change.
- Select routine open-source libraries that fit the approved stack, have acceptable licensing, and do not introduce a new paid service or material operational burden.
- Decide internal page structure, API details, database fields, component boundaries, test organization, and implementation order within the approved MVP.

These permissions do not authorize deployment, external communication, production data access, purchases, or scope expansion.

### 8.2 Required working behavior

- Inspect before editing.
- Preserve unrelated user changes.
- Use the existing project structure and conventions.
- Prefer the smallest complete vertical slice.
- Keep business rules deterministic and testable.
- Keep external side effects behind explicit interfaces.
- Use environment variables or secret storage for credentials.
- Fail safely when an external provider is unavailable.
- Stop and report when a missing business decision would materially change the result.
- Report validation evidence and any test not run.

### 8.3 Prohibited autonomous actions

Do not:

- Implement postponed features merely because the enterprise architecture mentions them.
- Add microservices, Kubernetes, a separate vector database, a policy engine, or local GPU inference without approval.
- Add a new production third-party service or paid dependency beyond the approved Supabase and OpenAI baseline without approval.
- Replace Supabase Auth/data services or the initial OpenAI model-provider path without approval.
- Use real customer data in development, tests, prompts, screenshots, or demos without explicit authorization and an approved handling method.
- Send emails, WhatsApp messages, social posts, proposals, or notifications to real recipients.
- Deploy to production or mutate production infrastructure.
- Run destructive database operations.
- Delete user files or overwrite unrelated changes.
- Rotate credentials or change external integration configuration.
- Commit, push, merge, create a pull request, or publish artifacts unless the user requests it.
- Weaken authentication, authorization, validation, audit, backup, or human-review controls to make a demo easier.

## 9. Human approval requirements

### 9.1 Engineering approval

Obtain explicit human approval before:

- Expanding beyond the MVP scope.
- Adding or replacing a production dependency with material security, cost, licensing, or operational impact. Routine open-source dependencies are an engineering decision.
- Replacing the approved Supabase authentication/data baseline.
- Replacing the approved initial OpenAI model provider or changing external AI data-processing policy.
- Adding a new third-party integration.
- Breaking an API already used in production. Pre-production API refinement is autonomous.
- Performing a destructive or difficult-to-reverse migration.
- Accessing or importing real customer data.
- Deploying, publishing, pushing, or changing production infrastructure.
- Incurring material external cost.
- Changing security, retention, backup, or privacy policy.

### 9.2 Business approval

Use the Version 1 workflow, fields, qualification weights, thresholds, and proposal sections defined in `docs/mvp-scope.md` without requesting further review. Human approval is required before real operational use for:

- Pricing, discounts, taxes, margins, and currencies.
- Technical claims, delivery commitments, warranties, and contractual language.
- The real Sari Arta proposal wording, exclusions, and readiness criteria.
- Real knowledge documents that become active for business answers or proposals.
- Data permitted to be sent to external AI providers.
- Customer contact consent and communication policy.

### 9.3 Runtime approval inside the product

The product must require human review before:

- Accepting an AI qualification as a business decision when configured for review.
- Converting or disqualifying a lead based only on AI output.
- Treating AI customer research as a verified fact.
- Publishing AI-generated marketing content.
- Sending an AI-generated customer message.
- Marking a proposal ready to share.
- Issuing a price, discount, delivery date, technical guarantee, or contractual commitment.
- Executing any consequential external action.

Approval must apply to the exact reviewed content. If the content or action parameters change, the previous approval is no longer valid.

## 10. Completion standard

A development task is complete only when:

- The requested behavior is implemented within MVP scope.
- Relevant tests pass.
- Authorization and failure behavior are considered.
- AI output is validated and human-control requirements are preserved.
- Documentation is updated when required.
- No real external action was taken without approval.
- The handoff states what changed, what was tested, and any remaining limitation.

If these conditions cannot be satisfied, report the blocker clearly instead of claiming completion.
