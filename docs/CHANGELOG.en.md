# Project Changelog

**Project:** Enterprise AI Business Development Agent Platform  
**Primary record:** English  
**Translation:** `CHANGELOG.zh-CN.md`

This changelog records major product, architecture, security, and business-capability milestones. Dates are based on the available repository history. It intentionally excludes low-level commits, routine refactoring, bug fixes, and test-only changes.

## 2026-08-07 — Phase 0: Foundation and Architecture Design

### Added capabilities

- Defined the product vision for an enterprise AI business development platform.
- Established Sari Arta commercial-kitchen engineering as the first validation business.
- Created the technical architecture, database design, REST API design, AI Agent direction, MVP scope, and development rules.
- Defined bilingual engineering-documentation and business-review practices.

### Architecture impact

- Selected Next.js, FastAPI, PostgreSQL, OpenAI Agents SDK, n8n, and Docker as the technology direction.
- Established PostgreSQL as the canonical business system of record.
- Chose a modular-monolith approach with deterministic services controlling transactions.
- Defined human approval, auditability, tenant isolation, and narrow AI tool boundaries.

### Business impact

- Converted the initial idea into an implementable, reviewable delivery plan.
- Defined the first complete workflow: capture lead, qualify, follow up, and convert to opportunity.
- Reduced early platform scope so one developer or a small team could deliver a usable MVP.

## 2026-08-08 to 2026-08-09 — Phase 1: Sari Arta MVP

### Added capabilities

- Launched the bilingual public Sari Arta website and structured inquiry workflow.
- Added authenticated CRM pages for companies, contacts, leads, tasks, activities, and opportunities.
- Added lead search, filtering, editing, status management, ownership, and company/contact relationships.
- Added dashboard metrics, follow-up workflow, and transactional lead-to-opportunity conversion.
- Added structured A/B/C AI lead qualification with business summaries, key factors, next actions, and human acceptance or rejection.
- Added durable Agent Runs, bounded retries, cancellation, recovery, correlation IDs, audit events, synthetic demo data, and local backup verification.

### Architecture impact

- Implemented the Next.js/FastAPI/PostgreSQL modular application and Docker Compose runtime.
- Added Redis-backed asynchronous agent execution without making Redis canonical business state.
- Added idempotent public intake, optimistic concurrency, Row Level Security, authorization, and audit foundations.
- Kept AI provider failure separate from manual CRM operation.

### Business impact

- Delivered the first usable Sari Arta lead-to-opportunity workflow.
- Enabled sales users to organize inquiries, follow up work, and opportunities in one workspace.
- Demonstrated AI qualification without allowing AI to change lead status or make commercial commitments autonomously.

## 2026-08-09 to 2026-08-10 — Phase 2: Multi-Agent Framework

### Added capabilities

- Added Agent Registry records for domains, agents, versioned configurations, capabilities, localization, and tenant activation.
- Registered the Sari Arta Commercial Kitchen Agent under `commercial_kitchen`.
- Added the IVC Facility Business Development Agent under `laboratory_animal_facility`.
- Added English, Chinese, and Bahasa Indonesia qualification outputs for domain demonstrations.
- Added the Agent Playground for switching agents and comparing structured qualification results without modifying CRM data.

### Architecture impact

- Separated reusable agent capabilities from domain-specific configuration.
- Introduced governed domain packages instead of hard-coding every new industry into the Phase 1 workflow.
- Preserved the existing Sari Arta workflow while adding isolated multidomain demonstrations.

### Business impact

- Proved that the platform could support more than one B2B industry.
- Turned the project from a single-domain demonstration into a reusable agent framework.
- Created a portfolio-ready way to demonstrate domain specialization safely.

## 2026-08-12 — Phase 2.5.1: Enterprise Knowledge Management

### Added capabilities

- Added tenant/domain knowledge collections, documents, metadata, lifecycle status, and optional agent bindings.
- Added document upload, listing, search, review, approval, rejection, activation, and archive interfaces.
- Added synthetic Commercial Kitchen and IVC knowledge examples.

### Architecture impact

- Established a separate governed knowledge control plane.
- Applied deny-by-default tenant, domain, agent, and collection access boundaries.
- Kept document management independent from conversational RAG.

### Business impact

- Gave business administrators a controlled place to prepare enterprise knowledge.
- Prevented unreviewed uploads from becoming agent evidence automatically.

## 2026-08-14 — Phase 2.5.2: Knowledge Processing Pipeline

### Added capabilities

- Added extraction for PDF, DOCX, Markdown, and UTF-8 text.
- Added text cleaning, deterministic chunking, metadata preservation, and citation-ready source references.
- Added an embedding-provider abstraction with OpenAI-compatible and deterministic development paths.
- Added pgvector storage preparation and asynchronous processing status.

### Architecture impact

- Converted approved document versions into tenant/domain/agent-isolated AI-ready assets.
- Preserved document, version, page, section, language, and chunk identity across processing.
- Kept future embedding providers behind a stable application boundary.

### Business impact

- Made approved enterprise documents technically usable for future evidence-based AI functions.
- Reduced the risk that generated answers would lose their source context.

## 2026-08-14 — Phase 2.5.3: Knowledge Governance

### Added capabilities

- Added immutable version history and explicit current, published, and active version pointers.
- Added replacement versions, safe rollback, archive, restore, and binding-status changes.
- Separated upload, edit, submit-review, approve, publish, activate, archive, restore, process, and audit permissions.
- Added knowledge audit timelines with actor, timestamp, action, target, and before/after metadata.

### Architecture impact

- Upgraded document storage into a governed enterprise lifecycle.
- Added optimistic concurrency and exact-version approval/publication controls.
- Ensured approval no longer implied publication or activation.

### Business impact

- Made it possible to prove who changed, approved, published, or rolled back business knowledge.
- Reduced the risk of agents using outdated or unapproved documents.

## 2026-08-16 — Phase 2.6: Knowledge Retrieval Foundation

### Added capabilities

- Added `POST /api/v1/knowledge/search` for agent-scoped pgvector similarity search.
- Added active, published, approved-version, agent-binding, language, and processing-status filters.
- Added complete document/version/page/section/chunk citations and an explicit insufficient-evidence outcome.
- Added Recall@K, Precision@K, Hit@1, MRR, citation, latency, security, and bilingual-consistency evaluation.
- Added repeatable regression fixtures and the internal `/knowledge/search` testing interface with visible thresholds and scores.
- Added the subsequent read-only Commercial Kitchen Knowledge Assistant using the validated retrieval boundary.

### Architecture impact

- Enforced authorization before embedding or model calls.
- Combined application authorization with PostgreSQL RLS and deny-by-default agent binding.
- Separated formal evidence from below-threshold diagnostics.
- Established cited, sufficient/insufficient/conflicting evidence handling for grounded answers.

### Business impact

- Enabled staff to find approved enterprise evidence with traceable sources.
- Created a measurable quality baseline for future embedding, chunking, threshold, and provider changes.
- Demonstrated safe knowledge-grounded assistance without CRM writes or autonomous actions.

## 2026-08-16 — Phase 3.1: Public Consultation Agent

### Added capabilities

- Added the separate English/Chinese Commercial Kitchen Consultation Agent to the public website.
- Added guided project discovery, contact collection, explicit consent, source attribution, validation, and duplicate protection.
- Reused the existing CRM lead workflow with source `website_ai_assistant`.

### Architecture impact

- Created a strict public-agent trust boundary separate from the internal Knowledge Assistant.
- Limited the public assistant to public information with no internal knowledge, CRM read, pricing, or communication tools.
- Added separate rate limiting, abuse controls, and an opt-in external model path.

### Business impact

- Turned the public website into a guided lead-generation experience.
- Allowed prospects to prepare a useful project brief while preserving human sales review and consent.

## Current Status

The platform has evolved from a single business demo into a reusable enterprise AI Business Development Platform. It now combines an operational CRM workflow, multidomain agent framework, governed enterprise knowledge lifecycle, evaluated retrieval, read-only grounded assistance, and a separated public consultation experience. External communication automation, autonomous sales actions, and advanced orchestration remain future controlled phases.
