# Project Roadmap

## Enterprise AI Business Development Agent Platform

**Reference business:** Sari Arta, Indonesia commercial-kitchen engineering  
**Delivery model:** One developer or a small team  
**Status convention:** `[x]` completed, `[ ]` not completed  
**Scope authority:** This roadmap defines phase boundaries. `docs/mvp-scope.md` defines the current Phase 1 acceptance scope.

## Roadmap principles

- Complete one usable business workflow before adding more agents or channels.
- Keep PostgreSQL as the business system of record.
- Keep manual sales operation available when AI or automation is unavailable.
- Require human review for consequential AI output and every external commercial action.
- Do not begin a later phase merely because its supporting architecture already exists.
- Validate each phase with working software and acceptance evidence before marking it complete.

## Phase 0 — Foundation

**Goal:** Establish the design and development rules needed to begin implementation safely.

- [x] Git repository
- [x] Technical architecture design
- [x] Database design
- [x] API design
- [x] AI Agent design
- [x] MVP scope
- [x] Development rules in `AGENTS.md`

**Exit criteria:** The system boundaries, MVP scope, core data model, API direction, AI responsibilities, security constraints, and human-approval rules are documented.

**Status:** Complete.

## Phase 1 — MVP

**Goal:** Build the first usable AI business-development assistant for daily lead work.

### Required capabilities

- [x] Project foundation and local Docker environment
- [ ] Authentication for `admin` and `sales`
- [ ] PostgreSQL schema and migrations
- [ ] FastAPI backend API
- [ ] Manual and website lead capture
- [ ] Customer-company and contact records
- [ ] Lead list, detail, filtering, ownership, status, priority, and notes
- [ ] Follow-up tasks and activity history
- [ ] Lead-to-opportunity conversion with a simple opportunity list
- [ ] Dashboard with actionable sales metrics
- [ ] Asynchronous AI run execution and status
- [ ] AI Lead Qualification Agent
- [ ] Human acceptance or rejection of AI qualification
- [ ] Minimum authorization, validation, audit, logging, rate limiting, backup, and health checks
- [ ] Seeded synthetic demonstration data
- [ ] Critical-path tests and a repeatable demo

### Phase 1 acceptance workflow

```text
Sign in
→ capture a lead
→ organize company, contact, and project details
→ create a follow-up task
→ run AI qualification
→ review and accept/reject the result
→ convert a qualified lead into an opportunity
→ see the updated dashboard and activity history
```

### Exit criteria

- A salesperson can complete the workflow without developer assistance.
- The CRM remains usable when the AI provider is unavailable.
- AI qualification returns validated structured output and never changes business status automatically.
- Authorization prevents ordinary users from performing admin-only actions.
- The critical workflow passes automated tests.
- The application runs through the documented Docker-based setup.
- A portfolio demonstration can complete the workflow in five to seven minutes.

**Current status:** Not started.

## Phase 2 — AI Enhancement

**Goal:** Use approved Sari Arta knowledge to improve answers, content, and proposal preparation.

- [ ] Knowledge-document upload and approval
- [ ] Text extraction, chunking, embeddings, and pgvector retrieval
- [ ] RAG Knowledge Assistant with citations and insufficient-evidence behavior
- [ ] Content Generation Agent with human approval
- [ ] Proposal Assistant with structured editable drafts
- [ ] Proposal versioning and print-ready export
- [ ] Evaluation cases for retrieval quality and grounded generation

**Entry condition:** Phase 1 is accepted and lead/opportunity data is reliable.

**Exit criteria:** Users can obtain cited answers and create reviewable content or proposal drafts without the AI inventing unsupported business facts, prices, or commitments.

## Phase 3 — Business Automation

**Goal:** Reduce repetitive follow-up work while keeping external communication controlled.

- [ ] WhatsApp integration
- [ ] Email integration and controlled automation
- [ ] CRM follow-up workflows
- [ ] n8n operational workflows
- [ ] Delivery status, retry, idempotency, and failure handling
- [ ] Consent, opt-out, template, and communication-policy enforcement

**Entry condition:** Phase 2 outputs and human-review workflows are stable.

**Exit criteria:** Approved communications can be delivered reliably, duplicated events do not produce duplicate messages, and users can recover failed workflows without corrupting CRM state.

## Phase 4 — Advanced Agent System

**Goal:** Add higher-autonomy capabilities only after the underlying data, tools, and governance are proven.

- [ ] Customer Research Agent
- [ ] Multi-agent orchestration
- [ ] Agent handoffs where justified
- [ ] MCP integration
- [ ] Additional model-provider support such as Qwen or approved local models
- [ ] Agent evaluation, cost, latency, and safety controls

**Entry condition:** Earlier phases have stable typed tools, reliable audit history, tested approval controls, and a demonstrated business need.

**Exit criteria:** Advanced agents improve measured business outcomes without bypassing permissions, human approval, source validation, or operational cost limits.

## Current development focus

Only **Phase 1 — MVP** is authorized for implementation.

Phase 2–4 architecture may retain simple compatibility boundaries, but their product features must not be implemented until the preceding phase is accepted or the project owner explicitly changes the roadmap.

## Progress update rules

- Mark an item complete only after implementation and relevant validation both succeed.
- A partially working UI or isolated API is not a completed business capability.
- Record material scope changes in this file and the affected design document.
- Update `docs/mvp-scope.md` when Phase 1 acceptance behavior changes.
- Update `AGENTS.md` when development authority or approval rules change.
- Never mark a phase complete based only on generated code or a scripted mock.
