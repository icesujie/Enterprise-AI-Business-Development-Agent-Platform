# Sari Arta Phase 1 MVP Demo Script

**Duration:** 5–7 minutes  
**Audience:** Business stakeholders, portfolio reviewers, and delivery partners  
**Data policy:** Use only the included synthetic records and `.example` contact details. Do not enter real customer information.

## 1. Demo objective

Demonstrate one complete, human-controlled business-development workflow:

```text
Website inquiry
→ CRM lead
→ AI qualification
→ human review
→ dashboard action queue
→ opportunity conversion
```

The key message is that AI assists commercial judgment but does not automatically qualify, reject, convert, price, or contact a customer.

## 2. Preparation

From the repository root:

```bash
make services-up
make demo-seed
make api-dev
```

In separate terminals:

```bash
make web-dev
```

```bash
cd apps/api
.venv/bin/python -m sari_api.worker
```

Open <http://localhost:3000>. The default demo mode uses the deterministic qualification provider and requires no OpenAI API key.

Demo workspace credentials:

- Email: `admin@sariarta.local`
- Password: `SariArtaDemo2026!`

The credentials are local demonstration values only and must never be used in production.

## 3. Suggested narrative and steps

### Step 1 — Submit a website inquiry (about 60 seconds)

1. Open the public Sari Arta website and briefly show its positioning and consultation CTA.
2. Open **Request Kitchen Consultation**.
3. Submit a new synthetic inquiry using values such as:
   - Name: `Jordan Demo`
   - Company: `Demo Sunrise Academy`
   - Country: `Indonesia`
   - Project type: `School kitchen`
   - Estimated kitchen size: `650 m² / 1,200 meals per service`
   - Expected timeline: `Campus opening in September 2027`
   - Message: `Synthetic demonstration inquiry for design, equipment, installation, and staff training. An indicative budget and floor plan are available for the discovery meeting.`
4. Point out that the public form creates a CRM record but does not automatically run AI or contact anyone.

Expected result: a confirmation screen and one new website-sourced lead.

### Step 2 — Review the created lead (about 60 seconds)

1. Sign in to the internal workspace.
2. Open **Leads** and find the new project.
3. Show its company/contact relationship, project details, source, tasks, and activity history.
4. Add a synthetic internal note or follow-up task if time permits.

Expected result: the website inquiry is visible as canonical PostgreSQL CRM data.

### Step 3 — Run AI qualification (about 90 seconds)

1. Open **AI Qualification** and select **Run AI qualification**.
2. Explain that FastAPI saves the Agent Run before queueing, Redis only transports the job, and the Worker uses bounded retries.
3. Show the correlation/reference ID connecting the request, Worker logs, and saved run.
4. Refresh if required, then show the A/B/C level, score, summary, factors, missing information, and recommended action.
5. Emphasize that hidden chain-of-thought is never displayed.

Expected result: a schema-validated assessment with `pending` human review.

If the live run is unavailable, use **Demo Meridian Health Campus** for a pending Level B result, or **Demo Nusantara Learning Foundation** for an approved Level A result.

### Step 4 — Make the human decision and review the dashboard (about 60 seconds)

1. Accept or reject the assessment explicitly.
2. Explain that acceptance records the score but does not change lead status automatically.
3. If accepted, update the lead to `qualified` only after reviewing the evidence.
4. Return to **Dashboard** and show new leads, review work, tasks, pipeline totals, and action links.

Expected result: the dashboard identifies the next useful sales action without AI controlling the pipeline.

### Step 5 — Convert to an opportunity (about 60 seconds)

1. Return to the qualified lead and select **Convert to opportunity**.
2. Confirm the project name, estimated value, currency, and expected close date.
3. Complete the conversion and open **Opportunities**.
4. Explain that conversion reuses the company/contact and prevents duplicates transactionally.

Expected result: one source-linked opportunity appears in the `discovery` stage.

## 4. Seeded fallback scenarios

| Synthetic record | Demo purpose |
|---|---|
| Demo Nusantara Learning Foundation | Qualified school kitchen, approved Level A assessment |
| Demo Meridian Health Campus | Urgent hospital kitchen, pending Level B assessment, overdue follow-up |
| Demo Garuda Components Manufacturing | New factory cafeteria lead with missing information |
| Demo Archipelago Food Services | Converted central-kitchen opportunity at proposal stage |

Run `make demo-seed` safely more than once. It creates the dataset once and never deletes or overwrites existing CRM records.

## 5. Demo guardrails

- Do not use real customer names, email addresses, phone numbers, drawings, budgets, or project claims.
- Do not claim that sample projects are completed Sari Arta references.
- Do not enable real OpenAI mode without approved environment and data-processing controls.
- Do not send external email, WhatsApp, proposals, or notifications.
- Keep AI output advisory and complete the human-review step.
- If AI or Redis is unavailable, continue the CRM demo and use a seeded assessment.

## 6. Successful demo checklist

- [ ] Public inquiry submitted.
- [ ] Lead found in the internal workspace.
- [ ] Company/contact relationship shown.
- [ ] AI result shown or seeded fallback used.
- [ ] Human review performed.
- [ ] Dashboard action queue reviewed.
- [ ] Qualified lead converted without duplicate records.
- [ ] No real data or external communication used.
