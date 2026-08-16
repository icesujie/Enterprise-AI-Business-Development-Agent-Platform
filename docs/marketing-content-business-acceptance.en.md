# Phase 3.2 Marketing Content Business Acceptance

**Status:** Prepared for controlled human acceptance; final GO not yet achieved  
**Acceptance dataset:** `phase_3_2_business_acceptance_v1`  
**Workspace:** `/marketing-content/acceptance`  
**Boundary:** Internal review only; no publishing, sending, scheduling, campaign automation, or CRM write

## 1. Purpose

This acceptance step determines whether governed Marketing Content Agent drafts are usable by Sari Arta business reviewers. It does not introduce another approval system. Every edit, review submission, decision, feedback record, and approval continues through the existing Content Governance lifecycle and RBAC controls.

## 2. Fixed Acceptance Set

The fixed set contains ten synthetic, non-sensitive cases. Each of the five supported content types has one English and one Chinese case.

| # | Content type | English scenario | Chinese scenario |
|---:|---|---|---|
| 1–2 | Website Article | Indonesia school central kitchen project | 印度尼西亚学校中央厨房项目 |
| 3–4 | TikTok Script | School canteen renovation | 学校食堂翻新 |
| 5–6 | Instagram Reel Script | Factory canteen | 工厂员工食堂 |
| 7–8 | Facebook Post | Hospital and institutional kitchen | 医院及机构厨房 |
| 9–10 | Email Draft | Central kitchen capacity planning | 中央厨房产能规划 |

The source file is `apps/api/src/sari_api/evaluation_data/marketing_business_acceptance_cases.v1.json`. Requests are tagged in existing `content_requests.constraints` with the dataset and case identifier. No acceptance-only database table or parallel lifecycle is used.

## 3. Reviewer Workflow

```text
Fixed Mock Draft
→ Open exact governed asset
→ Record structured human feedback
→ Edit and create immutable human successor
→ Submit exact version and checksum for review
→ Independent approver approves or rejects
→ Acceptance summary updates
```

The content author and approver must be different users. A creator cannot approve their own asset. Reviewers use the existing controls on `/marketing-content/{asset_id}`:

1. **Record feedback** against the exact current version.
2. **Save as new version** to preserve the AI draft and create a human successor.
3. **Submit for review** with the exact version/checksum.
4. Sign in as an independent user with `content:approve` and **Approve** or **Reject**.

Rejection, editing, rollback, and approval retain the existing immutable history and audit trail.

## 4. Human Edit Distance

Human Edit Distance is calculated only when all conditions are true:

- the asset has an `ai_generated` version produced by a generation run;
- the approved version has origin `human`;
- the approved version is a successor descended from that generated version;
- the exact human successor is the asset's approved version.

The UI displays the percentage changed, generated version number, and approved human version number. Approving the AI version directly, approving a rollback, or having no approved human successor returns no metric. The system never fabricates a zero value for missing human review.

## 5. Acceptance Summary

`GET /api/v1/content/acceptance` and `/marketing-content/acceptance` show:

- total, prepared, reviewed, approved, and rejected cases;
- average real Human Edit Distance;
- generated and approved human version pointers;
- common feedback categories;
- averaged deterministic quality metrics;
- Brand Guideline validation state;
- OpenAI comparison state.

The projection is tenant-scoped, requires `content:read`, and derives from existing governed requests, assets, versions, decisions, feedback, and generation runs.

## 6. Brand Guideline Checkpoint

**Brand Guideline Validation: Pending.**

No approved real Sari Arta Brand Guideline has been supplied for this milestone. Synthetic positioning and deterministic brand-fit scoring are not final brand approval. The system must not claim final brand validation until an authorized Sari Arta reviewer approves a real guideline through the governed knowledge process.

For Phase 3.2 final GO, the business owner must either:

1. complete validation against an approved real Brand Guideline; or
2. explicitly accept the missing guideline as a documented prerequisite before production activation.

No brand rules are invented by this acceptance package.

## 7. Controlled OpenAI Comparison

Mock remains the default and the acceptance preparation action is disabled whenever the configured Marketing Content provider is not `mock`. Preparing the fixed ten-case set therefore cannot intentionally trigger a paid provider.

A real-provider comparison is manual, explicit, and limited to the first paired English/Chinese cases:

```bash
cd apps/api
MARKETING_CONTENT_PROVIDER=openai \
OPENAI_API_KEY=... \
PYTHONPATH=src .venv/bin/python -m sari_api.marketing_generation_eval \
  --allow-paid-provider --max-cases 2
```

The reviewer compares quality, grounding, structure validity, latency, and provider/model. The current provider contract reports usage/cost as unavailable when it cannot provide reliable values. Never place the API key in source control, screenshots, acceptance notes, or chat.

Current state: **Not run**. It may be explicitly deferred only with a documented business reason.

## 8. Final GO Criteria

Phase 3.2 receives final GO only when:

- all ten acceptance cases are reviewed;
- no unsupported factual claims remain;
- citation completeness remains 100%;
- tenant, RBAC, knowledge-policy, and agent boundaries have no failures;
- human reviewers consider all five content types usable;
- at least one real Human Edit Distance is recorded and the paired versions are visible;
- both English and Chinese outputs are accepted;
- Brand Guideline validation is completed or explicitly accepted as a known prerequisite;
- the controlled one-English/one-Chinese OpenAI comparison is completed or explicitly deferred with a documented reason.

Final GO is a human business decision. Automated scores cannot approve content or the phase.

## 9. Exact Manual Acceptance Steps

1. Keep `MARKETING_CONTENT_PROVIDER=mock` and start the normal API, Worker, Web, PostgreSQL, Redis, and approved synthetic public-knowledge demo services.
2. Sign in as the content author and open `http://localhost:3000/marketing-content/acceptance`.
3. Select **Prepare 10 acceptance drafts** once. Refresh until all ten cases show an asset link. The action is idempotent and skips existing or running cases.
4. Open each case with **Open review**.
5. Verify channel structure, claims, evidence, citations, CTA, English/Chinese quality, and business usefulness.
6. Record at least one structured feedback category, with an optional reviewer note.
7. Edit the draft and select **Save as new version**. Do not overwrite or approve the original AI version.
8. Select **Submit for review** for the exact human successor.
9. Sign in as a different authorized approver. Approve or reject the exact reviewed version and checksum.
10. Return to `/marketing-content/acceptance` and verify counts, version pointers, Human Edit Distance, common feedback, and quality summary.
11. Complete or explicitly document the Brand Guideline prerequisite.
12. Optionally run the controlled two-case OpenAI comparison and document the result or deferral reason.
13. Confirm every final GO criterion. Only then may the project owner mark Phase 3.2 accepted and update the CHANGELOG.

Do not start Phase 3.2.4 automatically.
