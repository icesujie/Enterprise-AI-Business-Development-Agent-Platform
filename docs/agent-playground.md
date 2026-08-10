# Phase 2.3 Agent Playground

## Purpose / 用途

The Agent Playground is an authenticated demonstration interface for comparing business-development
agents without creating or changing CRM records.

Agent Playground 是一个需要登录的多领域智能体演示界面。它允许用户比较不同商务拓展智能体，
但不会创建或修改 CRM 客户、联系人、线索或商机。

Route: `/agent-playground`

## Available agents

| Domain | Agent | Input |
|---|---|---|
| `commercial_kitchen` | Sari Arta Commercial Kitchen Agent | Project type, location, capacity, budget and timeline |
| `laboratory_animal_facility` | IVC Facility Business Development Agent | Organization, facility type, species/research, capacity, technical requirements and timeline |

Each interface provides editable synthetic sample content. Users may remove fields to demonstrate
missing-information detection.

## Execution flow

```text
Authenticated user selects agent and language
→ Next.js Server Action validates the session
→ FastAPI creates an idempotent agent_playground_qualification Agent Run
→ Redis Worker dispatches the selected registered Agent configuration
→ Mock or OpenAI Agents SDK provider returns schema-validated output
→ Next.js polls the durable Agent Run
→ UI displays the normalized result
```

The result includes score, A/B/C level, business summary, missing information, risks, and recommended
next actions. Human-facing output supports `en`, `zh-CN`, and `id`.

## Isolation and safety

- Playground runs use the existing `agent_runs` table; no new business table is required.
- Every run is bound to the selected active Agent configuration and tenant.
- No company, contact, lead, assessment, opportunity, or task is created.
- No RAG, unrestricted tools, email, WhatsApp, publishing, or external communication is available.
- Results are marked `demo_only=true` and `human_review_required=true`.
- Hidden chain-of-thought is not requested, stored, or displayed.
- Provider failures use the existing bounded retry, cancellation, recovery, logging, and safe-error path.

## API

`POST /api/v1/agent-playground/runs` creates a durable run and requires `leads:qualify` plus an
`Idempotency-Key`. `GET /api/v1/agent-runs/{run_id}` returns status and the normalized result.

Real OpenAI execution follows the existing `AI_ENABLED` and `OPENAI_API_KEY` configuration. Without
an API key, deterministic mock mode keeps the complete demo available.
