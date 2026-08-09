# Sari Arta Phase 1 MVP — Five-Minute Demo

**Audience:** Business stakeholders, portfolio reviewers, and delivery partners  
**Data policy:** Every named company, contact, domain, project, amount, and AI result below is synthetic. Never substitute real customer data during a demonstration.

## 1. Demo message

Sari Arta has one controlled lead-to-opportunity workspace:

```text
Website inquiry
→ CRM lead and linked company/contact
→ AI qualification
→ human review
→ follow-up task
→ opportunity conversion
```

AI recommends; a salesperson remains responsible for qualification, pipeline changes, pricing, commitments, and customer contact.

## 2. Preparation

From the repository root:

```bash
make services-up
make demo-seed
make api-dev
```

Start the web application and qualification Worker in separate terminals:

```bash
make web-dev
```

```bash
cd apps/api
.venv/bin/python -m sari_api.worker
```

Open <http://localhost:3000> and sign in with the local-only account:

```text
Email: admin@sariarta.local
Password: SariArtaDemo2026!
```

The default `AI_ENABLED=false` mode is deterministic and requires no API key.

## 3. Five-minute demonstration flow

### 0:00–0:45 — Public website and inquiry

1. Show the homepage positioning: **Indonesia Commercial Kitchen Engineering Partner**.
2. Open **Request Kitchen Consultation**.
3. Explain the captured fields: company, country, project type, size/capacity, timeline, and requirements.
4. For a live submission, use only this synthetic brief:

```text
Name: Jordan Demo
Company: Demo Sunrise Academy
Country: Indonesia
Project type: School kitchen
Kitchen size: 650 m² / 1,200 meals per service
Timeline: Campus opening in September 2027
Message: Synthetic inquiry for design, equipment, installation, and training. A floor plan and indicative budget are available for discovery.
```

Expected: one idempotent, rate-limited website inquiry becomes canonical CRM data. No AI run or customer message starts automatically.

### 0:45–1:30 — Lead creation and CRM context

1. Sign in and open **Leads**.
2. Open the new website lead, or use **Demo Nusantara Learning Foundation**.
3. Show the linked company and contact, source, project location, capacity, timeline, tasks, and append-only activity history.

Expected: sales can work manually even when AI or Redis is unavailable.

### 1:30–2:40 — AI qualification and human control

1. Open the **Qualification** tab.
2. Start an assessment for the new lead, or use a seeded result.
3. Show run status, A/B/C level, score, business summary, four qualification factors, missing information, recommended action, and review status.
4. Explain that the durable run is stored before Redis delivery, retries are bounded, interrupted runs are recovered, and users can cancel queued/running work.
5. Accept or reject a pending assessment. Hidden chain-of-thought is never stored or displayed.

Expected: the result is schema-validated and remains advisory until a human reviews it.

### 2:40–3:30 — Three qualification scenarios

| Scenario | Saved outcome | Demonstration point |
|---|---|---|
| Demo Nusantara Learning Foundation | Level A, 88, approved | School central-production kitchen with capacity, budget, timeline, decision group, and floor plan |
| Demo Meridian Health Campus | Level B, 62, pending | Credible hospital need with budget and final authority still missing |
| Demo Corner Bistro | Level C, 24, approved for nurture | Low-value single-equipment request without an engineering project or committed date |

Open each assessment briefly to show that different evidence produces different actions—not merely different scores.

### 3:30–4:15 — Follow-up workflow

1. Open **Follow-up**.
2. Show the overdue hospital budget-owner task and the upcoming school floor-plan review.
3. Open the low-value inquiry and show its low-priority, 14-day nurture task.
4. Explain that task status is deterministic CRM state and external messages are not sent automatically.

Expected: dashboard priorities are based on saved due dates, ownership, lead priority, and review state.

### 4:15–5:00 — Opportunity conversion and pipeline

1. Open the approved school lead and choose **Convert to opportunity**.
2. Confirm the project name, amount/currency, expected close date, owner, and project requirements.
3. Complete the conversion and open **Opportunities**.
4. If the live record was previously converted, use **Demo Archipelago Central Kitchen Delivery** at proposal stage.
5. Explain that conversion is transactional, reuses the company/contact, records activity, and prevents duplicate opportunities.

Expected: the source lead becomes `converted` and exactly one linked opportunity appears in the pipeline.

## 4. Direct fallback records

- School assessment: <http://localhost:3000/leads/d7200000-0000-4000-8000-000000000001?tab=qualification>
- Hospital assessment: <http://localhost:3000/leads/d7200000-0000-4000-8000-000000000002?tab=qualification>
- Low-value assessment: <http://localhost:3000/leads/d8200000-0000-4000-8000-000000000001?tab=qualification>
- Existing converted opportunity: <http://localhost:3000/opportunities/d7500000-0000-4000-8000-000000000001>

## 5. Safe fallback behavior

- Worker or Redis unavailable: continue CRM and use a seeded assessment.
- OpenAI unavailable: keep `AI_ENABLED=false` for deterministic demo mode.
- Run interrupted: the Worker recovery scan returns a stale durable run to the queue when attempts remain.
- Retry limit reached: the run becomes `failed` with a safe message and CRM remains usable.
- Cancellation requested: queued/running work becomes `cancelled`; a late provider result cannot overwrite it.
- Duplicate conversion: return the existing opportunity instead of creating another.

## 6. Acceptance checklist

- [ ] Public website and consultation form shown.
- [ ] Inquiry visible as a linked company/contact/lead.
- [ ] Level A, B, and C scenarios shown.
- [ ] Human qualification review explained or performed.
- [ ] Follow-up task queue shown.
- [ ] Qualified lead converted exactly once.
- [ ] Dashboard and pipeline update shown.
- [ ] No real data, live external communication, or unapproved AI processing used.
