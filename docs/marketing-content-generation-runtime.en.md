# Governed Marketing Content Generation Runtime

## 1. Status and scope

Phase 3.2.3.4 enables the Sari Arta Marketing Content Agent to create governed drafts from approved public-marketing knowledge. Development activation is enabled; production activation remains `pending` at zero-percent rollout.

The runtime does not publish, schedule, send, modify CRM data, approve content, or expose IVC marketing generation.

## 2. Runtime flow

```text
Content Request
→ RBAC and tenant authorization
→ Agent Registry development activation
→ public_marketing_v1 policy
→ approved public knowledge retrieval
→ evidence validation
→ typed generation provider
→ output and citation validation
→ immutable AI content version
→ Generated
→ Human Review
```

Authorization is performed in the API before queueing and again in the worker before embedding, retrieval, or model calls. Revoked or mismatched access fails closed.

## 3. Provider boundary

`MarketingContentProvider` defines a provider-neutral `generate(request, evidence)` contract.

- `mock`: deterministic, grounded development and test output.
- `openai`: no-tools OpenAI Agents SDK adapter with typed output and bounded execution.
- Future Qwen or approved private/local adapters can implement the same contract without changing governance or persistence.

Configuration:

```env
MARKETING_CONTENT_PROVIDER=mock
MARKETING_CONTENT_MODEL=gpt-5-mini
MARKETING_CONTENT_TOP_K=5
```

Using `openai` requires `OPENAI_API_KEY`. Mock remains the safe default.

## 4. Structured content contracts

| Type | Required structure |
|---|---|
| Website article | title, summary, sections, CTA, references |
| TikTok script | title, hook, scenes, voiceover, on-screen text, CTA, references |
| Instagram Reel script | title, hook, scenes, caption, CTA, references |
| Facebook post | headline, body, CTA, hashtags, references |
| Email draft | subject, preview, greeting, body sections, CTA, closing, references |

English and Chinese are supported. Each reference must name a retrieved chunk. Application validation rejects a mismatched content type, unknown chunk, missing references, and unsupported protected claims such as prices, capacities, certifications, warranties, or delivery statements.

## 5. Knowledge and evidence boundary

Retrieval reuses the existing governed pgvector implementation. Formal evidence must satisfy all of the following:

- same tenant, commercial-kitchen domain, and exact Marketing Agent;
- active development activation and generation capability;
- `public_marketing_v1` policy;
- collection visibility `public_marketing`;
- allowed public knowledge class;
- approved document and version;
- published and active exact-version pointers;
- enabled exact-agent binding and completed processing;
- language, embedding model, and similarity threshold.

Requests involving pricing, discounts, suppliers, warranties, guarantees, or equivalent Chinese terms return `insufficient_evidence` before embedding or model use. Weak or conflicting evidence also produces no draft.

## 6. Persistence and governance

The asynchronous workflow uses `agent_runs` and `content_generation_runs`. The latter links the request, agent configuration, provider/model, evidence state, chunk references, validation summary, duration, and exact output version.

A successful run creates:

- one `content_asset` in `generated` status;
- one immutable `content_version` with origin `ai_generated`;
- complete safe citation metadata without source body duplication in audit logs;
- request and Agent Run completion state;
- an append-only generation audit event.

The requesting human remains the content owner/creator for accountability. Agent identity is carried by the asset and generation run. The agent has no review, approval, archive, publishing, communication, scheduling, or CRM-write authority.

## 7. API and UI

- `POST /api/v1/content/requests/{request_id}/generate` — idempotent `202` start; requires `content:generate`.
- `GET /api/v1/content/generation-runs/{run_id}` — tenant-scoped status and result.
- `/marketing-content/new` — governed AI request form plus manual fallback.
- `/marketing-content/generation/{run_id}` — auto-refreshing run, evidence, citation, insufficient-evidence, and error display.
- `/marketing-content/{asset_id}` — existing human review and approval workflow.

## 8. Evaluation baseline

The repeatable synthetic fixture covers grounded website, TikTok, Facebook, bilingual paired generation, insufficient evidence, forbidden pricing, invented-case prevention, and internal-knowledge rejection. The deterministic baseline records 100% grounding, citation completeness, insufficient-evidence handling, structural validity, and bilingual reference consistency, with 0% unsupported claims.

This baseline validates contracts and safeguards; production release still requires approved real public knowledge and a separate human release decision.

## 9. Local demonstration

Run migrations and load the repeatable synthetic demo knowledge:

```bash
make services-up
make migrate
make demo-seed
```

`make demo-seed` creates three synthetic `public_marketing` knowledge collections for the Marketing Content Agent and processes them with the configured embedding provider. The records are explicitly marked synthetic and not approved for real business use.

Open `http://localhost:3000/marketing-content/new`, choose one of the five content types, complete an English or Chinese request, and select **Generate governed AI draft**. The default mock provider needs no API key. The result page shows evidence status, model/provider, correlation ID, latency, complete citations, and the exact immutable generated version. Continue to the content detail page to exercise the existing human-review workflow.

To validate the real provider adapter in a controlled development environment, set:

```env
MARKETING_CONTENT_PROVIDER=openai
MARKETING_CONTENT_MODEL=gpt-5-mini
OPENAI_API_KEY=...
```

Then restart the API Worker. This does not activate production or grant publishing authority.
