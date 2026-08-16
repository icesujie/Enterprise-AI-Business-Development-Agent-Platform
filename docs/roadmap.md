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
- [x] Governed Knowledge Retrieval API with active-version filtering and exact citations
- [x] Retrieval quality evaluation, bilingual consistency baseline, and internal search test interface
- [x] Read-only Knowledge Assistant with validated citations and insufficient/conflicting-evidence behavior
- [x] Governed Marketing Content Agent with typed drafts, public evidence, and human approval
- [x] Marketing generation business evaluation baseline, immutable human feedback, and channel-specific review previews
- [x] Fixed ten-case bilingual Marketing Content business-acceptance workspace and GO checklist
- [ ] Final human business acceptance for Phase 3.2 Marketing Content Agent — pending/deferred; does not block Phase 3.2.4A technical foundations
- [ ] Proposal Assistant with structured editable drafts
- [ ] Proposal versioning and print-ready export
- [x] Evaluation cases for retrieval quality and grounded answer safety

**Entry condition:** Phase 1 is accepted and lead/opportunity data is reliable.

**Exit criteria:** Users can obtain cited answers and create reviewable content or proposal drafts without the AI inventing unsupported business facts, prices, or commitments.

## Phase 3 — Business Automation

**Goal:** Reduce repetitive follow-up work while keeping external communication controlled.

- [x] Phase 3.1 bilingual public Commercial Kitchen Consultation Agent with consented CRM intake
- [ ] Phase 3.2.4 Organic & AI Search Visibility Foundation
  - [x] Phase 3.2.4A Organic & AI Search Technical Foundation
- [ ] WhatsApp integration
- [ ] Email integration and controlled automation
- [ ] CRM follow-up workflows
- [ ] n8n operational workflows
- [ ] Delivery status, retry, idempotency, and failure handling
- [ ] Consent, opt-out, template, and communication-policy enforcement

**Entry condition:** Phase 2 outputs and human-review workflows are stable.

**Exit criteria:** Approved communications can be delivered reliably, duplicated events do not produce duplicate messages, and users can recover failed workflows without corrupting CRM state.

### Phase 3.2.4 — Organic & AI Search Visibility Foundation

**Status:** In progress. **Phase 3.2.4A — Organic & AI Search Technical Foundation** is implemented and validated. Later governed public-content publication and visibility measurement remain future work.

**Purpose:** Turn approved public enterprise knowledge and human-approved governed marketing content into discoverable public website content for traditional organic search and provider-neutral AI-powered search experiences. This milestone follows the governed Marketing Content Agent and its generation evaluation, and precedes outbound channel automation.

Planned scope:

1. **Technical discoverability:** crawlable and indexable public architecture, sitemap, canonical URLs, metadata, robots/crawler policy, and server-rendered public content.
2. **Structured content:** appropriate machine-readable metadata for the organization, solutions, projects/case studies, articles, products/services, breadcrumbs, and other eligible public pages.
3. **AI-search readiness:** clear factual pages, consistent entities, project/case evidence, service and location information, machine-readable metadata, and public-knowledge provenance without coupling to one AI-search provider.
4. **Search-oriented content architecture:** governed Solution, Industry, Project/Case Study, Guide, FAQ, and business-question pages. AI may assist their creation, but a human must approve the exact content version before publication.
5. **Visibility and attribution planning:** future measurement of organic traffic, identifiable AI-search referrals, landing-page performance, consultation-agent conversion, and CRM lead-source attribution. Analytics is not part of this planning milestone.

Intended acquisition flow:

```text
Approved Public Knowledge
→ Governed Marketing Content
→ Public Website Content
→ Search / AI Search Discovery
→ Website Visitor
→ Public Consultation Agent
→ CRM Lead
→ Qualification Agent
→ Sales Follow-up
```

Search-visible content may originate only from explicitly public knowledge and approved marketing content. It must never expose internal pricing, supplier information, private customer information, internal SOP, CRM data, or confidential commercial information.

#### Phase 3.2 dependency rules

Phase 3.2 engineering, security/governance, and technical evaluation are complete. Business acceptance is pending/deferred, and production activation remains disabled. Final acceptance still requires an approved real Sari Arta Brand Guideline, final English and Chinese review, real Human Edit Distance, and a controlled OpenAI comparison.

The deferred acceptance does **not** block:

- Phase 3.2.4A Organic & AI Search technical foundations;
- sitemap and robots/crawler readiness;
- structured-data infrastructure;
- metadata architecture;
- public-page architecture;
- search-attribution design.

The deferred acceptance **does** block:

- production Marketing Content Agent activation;
- automatic website-content generation;
- automatic content publication;
- social publishing;
- external marketing communication based on generated content.

Phase 3.2.4A must remain a technical foundation only. It must not generate, approve, publish, or externally distribute marketing content.

#### Phase 3.2.4A implementation result

The public website now has an explicit crawl boundary; canonical bilingual metadata; Organization,
WebSite and Breadcrumb structured data; a publication-aware sitemap policy; reviewed Googlebot,
Bingbot and OAI-SearchBot rules; private-route `noindex` defense in depth; disabled-by-default
IndexNow readiness; and minimal, backward-compatible search-acquisition attribution. Search Console,
Bing Webmaster, production-domain verification, real public-content approval, analytics, and any
publication trigger remain manual or future production tasks. See
`docs/organic-ai-search-foundation.en.md` and its Chinese translation.

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
2.5.1 Enterprise Knowledge Management, Phase 2.5.2 Knowledge Processing, Phase 2.5.3
Knowledge Governance, Phase 2.6.1 Knowledge Retrieval, Phase 2.6.2 Retrieval Evaluation,
Phase 2.6.3 Read-Only Knowledge Assistant, Phase 3.1 Public Consultation Agent, Phase
3.2 Business Acceptance Preparation, and Phase 3.2.4A Organic & AI Search Technical Foundation
are implemented for controlled development evaluation. Phase 3.2 engineering, security/governance,
and technical evaluation are complete; business acceptance is pending/deferred and production
activation is disabled. The control plane manages tenant- and domain-scoped
collections, immutable version history, explicit current/published/active pointers, human approval,
separate publication, safe rollback, agent bindings, and a tenant-scoped audit timeline through
`/knowledge`. The read-only retrieval API returns agent-authorized evidence chunks and exact citations
from the active published version. The Commercial Kitchen Knowledge Assistant adds read-only cited
answers with deterministic insufficient/conflicting evidence behavior; existing CRM, Playground, and
qualification workflows are unchanged. IVC production retrieval, external actions, and production
activation remain disabled.

The separate public consultation widget collects a bilingual structured project brief and creates an
unassigned `website_ai_assistant` lead only after explicit contact consent. It has no internal
knowledge/CRM read access, pricing capability or external action tools. General business automation
and Phase 3 external channels remain unimplemented.

The Marketing Content Agent creates typed English/Chinese drafts only from approved public-marketing
evidence. Generated versions enter the existing human review workflow and cannot be approved,
published, scheduled, sent, or written into CRM by the agent. Development/demo activation is enabled;
production remains pending.

The deterministic business baseline covers five scenarios, all five supported content types, and paired English/Chinese cases. Human feedback and channel previews are available internally. Business acceptance remains deferred pending an approved real Brand Guideline, final bilingual review, real Human Edit Distance, and a controlled OpenAI comparison. This deferral does not block Phase 3.2.4A technical search foundations, but it continues to block production generation, automatic publication, social publishing, and generated-content external communication.

The next task should be selected only after reviewing the Phase 3.2.4A production-domain checklist.
Phase 2–4 architecture may retain simple compatibility boundaries; later production capabilities
still require their documented acceptance gates, while explicitly independent technical foundations
may proceed according to the dependency rules above.

## Progress update rules

- Mark an item complete only after implementation and relevant validation both succeed.
- A partially working UI or isolated API is not a completed business capability.
- Record material scope changes in this file and the affected design document.
- Update `docs/mvp-scope.md` when Phase 1 acceptance behavior changes.
- Update `AGENTS.md` when development authority or approval rules change.
- Never mark a phase complete based only on generated code or a scripted mock.
