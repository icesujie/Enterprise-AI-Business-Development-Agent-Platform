# Marketing Generation Evaluation and UX Validation

**Status:** Phase 3.2.3.5 implemented for deterministic development evaluation; business acceptance is conditional  
**Baseline:** `marketing_generation_baseline.mock.v1.json`  
**Boundary:** Internal evaluation and human review only; no publishing, sending, scheduling, CRM write, or external automation

## 1. Purpose

This phase evaluates whether governed Marketing Content Agent outputs are useful for B2B marketing review, not merely schema-valid. It adds a repeatable business dataset, explicit quality measures, immutable human feedback, channel-specific previews, and a read-only internal evaluation projection. Automated scores are review aids and never approval decisions; no hidden model reasoning is stored or displayed.

## 2. Evaluation Flow

```text
Synthetic Business Scenario
→ Approved Public Evidence Fixture
→ Governed Marketing Provider
→ Schema / Claim / Citation Validation
→ Business Quality Evaluation
→ Channel Preview
→ Human Feedback
→ Exact-Version Approval
→ Human Edit Distance when an approved version exists
```

## 3. Versioned Business Dataset

`marketing_generation_cases.v1.json` contains ten synthetic cases: five scenarios, each paired in English and Chinese.

| Scenario | Content type | Audience / channel |
|---|---|---|
| Indonesia school kitchen project | Website Article | Schools / Website |
| School canteen renovation | TikTok Script | Schools / TikTok |
| Factory canteen | Instagram Reel Script | Factories / Instagram |
| Hospital / institutional kitchen | Facebook Post | Hospitals / Facebook |
| Central kitchen capacity planning | Email Draft | Central kitchens / Email |

All facts are synthetic public-marketing fixtures and contain no real customer-identifying data.

## 4. Quality Metrics

Every successful draft receives a deterministic projection stored at `content_generation_runs.validation_summary.quality_evaluation`.

| Metric | Meaning |
|---|---|
| Brand fit | Appropriate approved Sari Arta identity and positioning |
| Audience fit | Relevance to the intended institutional audience |
| Channel fit | Compliance with the selected channel structure |
| Clarity | Reviewable length and readable structure |
| CTA quality | Clear requested next action |
| Factual grounding | Model references map to retrieved citation chunks |
| Unsupported claims | Evidence/reference boundary failure; lower is better |
| Repetition | Penalizes repeated review segments |
| Content usefulness | Composite review-oriented utility |
| Human Edit Distance | Normalized difference from AI text to an exact approved human version; `0` unchanged, `1` fully different |

The scores do not determine legal, commercial, technical, or final brand approval.

## 5. Deterministic Baseline

| Measure | Result |
|---|---:|
| Brand fit | 90.0 |
| Audience fit | 90.0 |
| Channel fit | 95.0 |
| Clarity | 80.0 |
| CTA quality | 95.0 |
| Factual grounding | 100.0 |
| Unsupported claims | 0.0 |
| Repetition | 74.9 |
| Content usefulness | 91.5 |
| Overall | 90.71 |
| Structure validity | 100% |
| Citation completeness | 100% |

Future prompt, model, retrieval-threshold, knowledge-set, or content-schema changes must compare against the versioned Mock baseline. Latency is recorded per run but is not a fixed regression assertion.

## 6. Human Feedback Governance

`content_review_feedback` stores human-authored feedback bound to an exact version and SHA-256 checksum. Categories are `useful`, `too_generic`, `brand_tone_issue`, `weak_cta`, `insufficient_evidence`, `too_long`, and `channel_mismatch`.

Submission requires `content:review`. Records are tenant-scoped, protected by forced PostgreSQL RLS, append-only, and audit-linked. There is no update/delete API. The Marketing Agent has no review identity or authority and cannot edit or remove feedback.

## 7. Internal UX

The content detail page provides channel-appropriate previews:

- Website Article: title, summary, sections, CTA, references.
- TikTok / Reel: hook, scenes, visual direction, voiceover, on-screen text, CTA, caption where applicable.
- Facebook: headline, body, CTA, hashtags, references.
- Email: subject, preview text, greeting, body, CTA, closing, references.

The internal evaluation view shows outcome, evidence, provider/model, scores, feedback, citations, latency, correlation ID, usage/cost availability, and Human Edit Distance. It cannot publish or simulate delivery.

## 8. API and Persistence

- `POST /api/v1/content/assets/{asset_id}/feedback`: idempotent exact-version feedback; requires `content:review`.
- `GET /api/v1/content/assets/{asset_id}/evaluation`: tenant-scoped internal projection; requires `content:read`.
- `content_review_feedback`: immutable RLS-protected feedback.
- `content_generation_runs.validation_summary`: quality projection without hidden reasoning.

Human Edit Distance is returned only when the exact approved version is a human-authored successor descended from the AI-generated source. The response also identifies the generated version and approved human version. Direct AI-version approval, rollback approval, and missing human approval return no metric.

The fixed Phase 3.2 business-acceptance workflow and final GO criteria are defined in `marketing-content-business-acceptance.en.md`.

## 9. Optional Real-Provider Validation

Normal tests use Mock and incur no model cost. A real-provider run is explicit and limited to at most two cases:

```bash
cd apps/api
MARKETING_CONTENT_PROVIDER=openai \
OPENAI_API_KEY=... \
PYTHONPATH=src .venv/bin/python -m sari_api.marketing_generation_eval \
  --allow-paid-provider --max-cases 2
```

The output compares quality, grounding, structure, and latency. The current provider contract does not expose reliable token/cost usage, so it reports `not_available_from_current_provider_contract` instead of inventing a cost. Paid evaluation never runs automatically.

## 10. Security Boundary

Tenant isolation, forced RLS, RBAC, exact Marketing Agent binding, `public_marketing_v1`, approved/published/active public knowledge, pending production activation, and the prohibition on AI approval, CRM writes, publishing, scheduling, private knowledge, and external actions all remain unchanged.

## 11. Recommendation

**CONDITIONAL GO.** The platform is ready for controlled human business acceptance, but not production marketing use or the next autonomous/outbound capability.

Required improvements:

1. Sari Arta reviewers assess at least one English and Chinese draft for every content type and record feedback.
2. Create approved human successor versions so Human Edit Distance reflects real work.
3. Run at most two controlled OpenAI cases and compare quality, grounding, structure, and latency.
4. Review the 74.9 repetition score and validate final tone against approved brand guidance.

No subsequent phase starts automatically.
