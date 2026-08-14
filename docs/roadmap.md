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
- [x] Authentication for `admin` and `sales`
- [x] PostgreSQL schema and migrations
- [x] FastAPI backend API
- [x] Manual and website lead capture
- [x] Customer-company and contact records
- [x] Lead list, detail, filtering, ownership, status, priority, and notes
- [x] Follow-up tasks and activity history
- [x] Lead-to-opportunity conversion with a simple opportunity list
- [x] Dashboard with actionable sales metrics
- [x] Asynchronous AI run execution and status
- [x] AI Lead Qualification Agent
- [x] Human acceptance or rejection of AI qualification
- [x] Minimum authorization, validation, audit, logging, rate limiting, backup, and health checks
- [x] Seeded synthetic demonstration data
- [x] Critical-path tests and a repeatable demo

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

**Current status:** Phase 1 application acceptance is complete through M8. The critical workflow,
Agent Run reliability, synthetic A/B/C scenarios, five-minute demonstration, structured
logging/audit, local backup/restore verification, and browser smoke path are complete. Real
production launch remains a separate human-approved activity with environment-specific gates in
`docs/production-readiness-checklist.md`.

## Phase 2 — AI Enhancement

**Goal:** Use approved Sari Arta knowledge to improve answers, content, and proposal preparation.

- [x] Agent Registry MVP with domains, agents, versioned configurations, and capability bindings
- [x] Register the existing Sari Arta qualification agent as `commercial_kitchen`
- [x] Add a non-executable Laboratory Animal Facility / IVC validation package
- [x] Define English, Chinese, and Bahasa Indonesia agent-localization contracts
- [x] Implement the IVC qualification demo workflow with three synthetic multilingual cases
- [x] Add the unified Agent Playground for Commercial Kitchen and IVC demonstrations
- [x] Knowledge-document upload and approval foundation
- [x] Text extraction, chunking, embeddings, pgvector retrieval, and citation foundation
- [x] Enterprise collections, document versions, lifecycle approval, and agent bindings
- [x] Approved-version processing for PDF, DOCX, text, and Markdown with agent-isolated pgvector chunks
- [x] Enterprise document governance with version history, rollback, separate approval/publication, audit timeline, and split permissions
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

**M8 Phase 1 acceptance, Phase 2.3 Agent Playground, Phase 2.5 Knowledge Foundation, Phase
2.5.1 Enterprise Knowledge Management, Phase 2.5.2 Knowledge Processing, and Phase 2.5.3
Knowledge Governance are implemented.** The control plane manages tenant- and domain-scoped
collections, immutable version history, explicit current/published/active pointers, human approval,
separate publication, safe rollback, agent bindings, and a tenant-scoped audit timeline through
`/knowledge`. It remains separated from the retrieval data plane: no Knowledge Assistant generates
answers and existing CRM, Playground, and qualification workflows are unchanged. IVC production
retrieval, external actions, and production activation remain disabled. Approved exact versions can
be processed into agent-isolated, citable pgvector chunks, but no conversational assistant or
user-facing retrieval exists.

Phase 2–4 architecture may retain simple compatibility boundaries, but their product features must not be implemented until the preceding phase is accepted or the project owner explicitly changes the roadmap.

## Progress update rules

- Mark an item complete only after implementation and relevant validation both succeed.
- A partially working UI or isolated API is not a completed business capability.
- Record material scope changes in this file and the affected design document.
- Update `docs/mvp-scope.md` when Phase 1 acceptance behavior changes.
- Update `AGENTS.md` when development authority or approval rules change.
- Never mark a phase complete based only on generated code or a scripted mock.
