# Enterprise AI Business Development Agent Platform

## REST API Design

> Chinese translation: [api-design.zh-CN.md](api-design.zh-CN.md). This English document is the primary engineering baseline.

**Reference business:** Sari Arta, Indonesia commercial kitchen engineering  
**Backend:** FastAPI  
**Base path:** `/api/v1`  
**Contract format:** OpenAPI 3.1  
**Document version:** 1.0

> 中文审阅入口：[中文架构审阅指南](</Users/sujie/Documents/ChatGPT/Enterprise AI Business Development Agent Platform/docs/review-guide.zh-CN.md>)。重点参考其中“API 设计怎么审核”、术语对照和审核清单。

## Phase 2.5 API addendum

The implemented `/api/v1/knowledge` surface supports tenant-scoped sources, exact domain/agent
bindings, multipart document upload, immutable approval/rejection, durable ingestion state, retry,
and cited vector retrieval. `knowledge:manage` is admin-only; `knowledge:retrieve` is available to
authorized admin and sales users but still requires an enabled tenant-agent knowledge policy.
Retrieval returns evidence candidates or `insufficient_evidence`; it is not a conversational answer
endpoint. Complete contracts and security predicates are in `docs/knowledge-foundation-design.en.md`.

## 1. API goals

The API is the only supported business interface for the Next.js application, workers, AI agent tools, n8n, and external channels. It provides tenant isolation, consistent authorization, idempotent mutation, asynchronous workflow status, auditable approvals, and stable contracts that do not expose database or provider internals.

This is a resource-oriented REST API. Commands are used only when an operation is a meaningful state transition, such as qualifying a lead, approving a proposal, or cancelling an agent run.

## 2. Global conventions

### 2.1 URLs and media types

- Production example: `https://api.example.com/api/v1`
- JSON media type: `application/json`
- UTF-8 throughout.
- Resource names are plural nouns with lowercase kebab-free paths.
- JSON field names use `snake_case`.
- UUIDs are opaque strings.
- Timestamps are RFC 3339 UTC, for example `2026-08-07T09:30:00Z`.
- Dates use `YYYY-MM-DD`.
- Countries use ISO 3166-1 alpha-2; currencies use ISO 4217.
- Phone numbers use E.164.

### 2.2 Required and standard headers

| Header | Use |
|---|---|
| `Authorization: Bearer <token>` | Required except public capture, health, and provider webhooks |
| `X-Tenant-Id: <uuid>` | Required for a multi-tenant user session; validated against token membership |
| `X-Request-Id` | Optional client correlation ID; server returns one even when absent |
| `Idempotency-Key` | Required for retry-sensitive create/command operations |
| `If-Match: "<version>"` | Required for concurrency-sensitive updates |
| `Accept-Language` | Response localization preference where supported |
| `Traceparent` | W3C distributed trace propagation |

`X-Tenant-Id` selects one of the caller's authorized memberships; it does not grant tenant access.

### 2.3 Status codes

| Code | Meaning |
|---|---|
| `200` | Successful read, update, or synchronous command |
| `201` | Resource created |
| `202` | Asynchronous work accepted |
| `204` | Successful action with no response body |
| `400` | Malformed or semantically invalid request |
| `401` | Missing, invalid, or expired authentication |
| `403` | Authenticated but not permitted |
| `404` | Resource absent or intentionally hidden across tenant boundary |
| `409` | State conflict, duplicate, or idempotency mismatch |
| `412` | `If-Match` version does not match |
| `413` | Request or upload too large |
| `415` | Unsupported media type |
| `422` | Field validation failed |
| `429` | Rate or quota exceeded |
| `503` | Temporarily unavailable dependency or disabled capability |

### 2.4 Standard resource metadata

Mutable resources normally include:

```json
{
  "id": "8cc724a7-4991-41da-a2d0-52157be1d7d5",
  "created_at": "2026-08-07T09:30:00Z",
  "updated_at": "2026-08-07T09:42:10Z",
  "version": 3
}
```

Responses for versioned mutable resources return `ETag: "3"`.

### 2.5 Pagination, filtering, and sorting

Cursor pagination is the default:

```http
GET /api/v1/leads?status=new&limit=50&sort=-created_at&cursor=opaque_value
```

```json
{
  "data": [],
  "page": {
    "next_cursor": "opaque_value_or_null",
    "has_more": false,
    "limit": 50
  }
}
```

- Default `limit`: 25; maximum: 100.
- Cursor values are opaque and bound to the filter/sort context.
- Sort fields are allowlisted per endpoint; prefix `-` means descending.
- Filters use repeated parameters for multiple values where useful.
- Full-text search uses `q`; clients should debounce.
- Date ranges use `created_from`, `created_to`, or domain-specific names.

### 2.6 Sparse fieldsets and expansion

Avoid arbitrary GraphQL-like projection. Selected endpoints may support:

- `include=organization,primary_contact`
- `fields=id,name,status,owner`

Allowlisted expansion prevents unbounded joins and data leakage. Default responses include stable core fields and link/reference IDs.

### 2.7 Error format

Errors follow an RFC 9457 Problem Details-compatible structure:

```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Request validation failed",
  "status": 422,
  "detail": "One or more fields are invalid.",
  "instance": "/api/v1/leads",
  "code": "validation_error",
  "request_id": "req_01J4R5K9X2",
  "errors": [
    {
      "field": "estimated_value",
      "code": "greater_than_or_equal",
      "message": "Value must be greater than or equal to 0."
    }
  ]
}
```

Messages are safe for users. Internal stack traces, SQL errors, raw provider responses, prompts, and secrets are never returned.

### 2.8 Idempotency

`Idempotency-Key` is required for:

- Public lead submission.
- Inbound event replay where provider IDs are unavailable.
- Agent run creation.
- Lead conversion.
- Proposal rendering/issuing.
- Approval decisions.
- Outbound message send.
- Bulk imports.

The server scopes a key by tenant and authenticated principal, hashes the request, and retains the successful response for at least 24 hours. Reusing a key with different content returns `409 idempotency_key_reused`.

### 2.9 Optimistic concurrency

`PATCH` requests and material state transitions require `If-Match` where concurrent editing is likely. A stale value returns:

```json
{
  "type": "https://api.example.com/problems/version-conflict",
  "title": "Resource version conflict",
  "status": 412,
  "detail": "The resource changed after it was loaded.",
  "code": "version_conflict",
  "request_id": "req_01J4R5K9X2",
  "current_version": 4
}
```

## 3. Authentication design

### 3.1 Human users

Use an external OIDC identity provider with Authorization Code flow and PKCE.

For the Next.js browser application, prefer a backend-for-frontend session:

1. Next.js starts OIDC login.
2. The identity provider authenticates the user and enforces MFA.
3. Next.js stores the session in a secure, `HttpOnly`, `Secure`, `SameSite` cookie.
4. Server-side Next.js obtains or forwards a short-lived access token to FastAPI.
5. Browser JavaScript does not store long-lived bearer or refresh tokens.

FastAPI validates signature, issuer, audience, expiry, not-before time, and token type. Membership and sensitive permissions are resolved from server-controlled data; token claims can be cached briefly but revocation-sensitive actions re-check current state.

### 3.2 Service accounts

n8n and internal workers use OAuth 2.0 Client Credentials or workload identity federation. Each service account has:

- One environment and workload owner.
- Explicit tenant or allowed-tenant scope.
- Narrow permission scopes.
- Short-lived access tokens.
- Rotated credentials when static client secrets cannot be avoided.
- No human UI access.

Workers inside the same trust boundary should still carry a workload identity and tenant context rather than relying on network location.

### 3.3 Provider webhooks

Provider webhook endpoints do not use bearer auth. They require provider-specific HMAC/signature validation, raw-body verification, timestamp/replay checks, account lookup, payload-size limits, and event deduplication.

Website public lead capture uses a form token or site key, origin policy, bot controls, rate limits, and consent fields. It must not expose internal tenant IDs.

### 3.4 Authorization model

RBAC supplies coarse permissions; application policies enforce tenant, object, ownership, state, and value thresholds.

Representative scopes:

| Scope | Purpose |
|---|---|
| `crm:read`, `crm:write` | Read/update permitted CRM records |
| `leads:assign`, `leads:qualify`, `leads:convert` | Lead commands |
| `opportunities:manage` | Pipeline operations |
| `conversations:read`, `messages:draft`, `messages:send` | Messaging |
| `knowledge:read`, `knowledge:manage` | Retrieval vs curation |
| `agents:run`, `agents:inspect`, `agents:admin` | Start, inspect, configure agent workflows |
| `models:read`, `models:manage` | Inspect approved deployments or manage provider/routing configuration |
| `proposals:read`, `proposals:write`, `proposals:approve`, `proposals:issue` | Proposal lifecycle |
| `content:write`, `content:approve`, `content:publish` | Content lifecycle |
| `integrations:manage` | Connector administration |
| `audit:read`, `exports:create` | Sensitive audit/export operations |

An agent tool receives the initiating principal and a server-generated capability set. It cannot expand its scopes.

### 3.5 CSRF, CORS, and rate limiting

- Cookie-authenticated calls require CSRF protection.
- CORS is an explicit production-origin allowlist; no wildcard with credentials.
- Rate limits apply by IP, user/service account, tenant, endpoint, and public form/provider account.
- Sensitive commands and AI usage also enforce tenant quotas.
- `429` returns `Retry-After` and machine-readable quota metadata.

## 4. Endpoint catalog

The catalog describes the first enterprise API baseline. Administration endpoints may be released after core CRM workflows but retain these resource contracts.

### 4.1 Session and tenant context

| Method | Path | Purpose | Scope |
|---|---|---|---|
| `GET` | `/me` | Current identity, memberships, roles, permissions | Authenticated |
| `GET` | `/tenants/{tenant_id}` | Tenant profile/settings visible to member | Authenticated member |
| `PATCH` | `/tenants/{tenant_id}` | Update tenant defaults/policies | `tenant:admin` |
| `GET` | `/memberships` | List tenant members | `memberships:read` |
| `POST` | `/memberships/invitations` | Invite a user | `memberships:manage` |
| `PATCH` | `/memberships/{membership_id}` | Suspend/update membership | `memberships:manage` |
| `PUT` | `/memberships/{membership_id}/roles` | Replace assigned roles | `roles:assign` |
| `GET` | `/roles` | List roles and permissions | `roles:read` |

### 4.2 Organizations and contacts

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/organizations` | Search/list or create organization |
| `GET`, `PATCH`, `DELETE` | `/organizations/{organization_id}` | Read, update, or soft-delete |
| `GET` | `/organizations/{organization_id}/timeline` | Combined activity timeline |
| `POST` | `/organizations/{organization_id}/research-runs` | Start customer research agent run |
| `POST` | `/organizations/{organization_id}/research-verifications` | Verify selected research facts |
| `GET`, `POST` | `/contacts` | Search/list or create contact |
| `GET`, `PATCH`, `DELETE` | `/contacts/{contact_id}` | Read, update, or soft-delete |
| `GET` | `/contacts/{contact_id}/timeline` | Contact activity timeline |
| `POST` | `/contacts/{contact_id}/consents` | Record consent grant/withdrawal |

Scopes are `crm:read` for reads and `crm:write` for mutations; consent recording may require `consent:manage`.

### 4.3 Leads

| Method | Path | Purpose | Notes |
|---|---|---|---|
| `POST` | `/public/lead-submissions` | Public website lead capture | Site token, rate limit, idempotency |
| `GET`, `POST` | `/leads` | List/create leads | Manual create requires `crm:write` |
| `GET`, `PATCH`, `DELETE` | `/leads/{lead_id}` | Read/update/archive | `If-Match` on update |
| `POST` | `/leads/{lead_id}/assignments` | Assign or unassign owner | `leads:assign` |
| `POST` | `/leads/{lead_id}/qualification-runs` | Start AI qualification | `leads:qualify`, returns `202` |
| `GET` | `/leads/{lead_id}/assessments` | Qualification history | `crm:read` |
| `POST` | `/leads/{lead_id}/assessments/{assessment_id}/reviews` | Approve/reject assessment | `leads:qualify` |
| `POST` | `/leads/{lead_id}/conversions` | Atomically create opportunity | `leads:convert`, idempotent |
| `POST` | `/leads/{lead_id}/disqualifications` | Disqualify with reason | `leads:qualify` |

### 4.4 Opportunities, activities, and tasks

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/opportunities` | Pipeline list/create |
| `GET`, `PATCH` | `/opportunities/{opportunity_id}` | Read/update |
| `POST` | `/opportunities/{opportunity_id}/stage-transitions` | Validated stage change |
| `POST` | `/opportunities/{opportunity_id}/close-won` | Mark won with required details |
| `POST` | `/opportunities/{opportunity_id}/close-lost` | Mark lost with reason |
| `GET`, `POST` | `/activities` | Filter or record activity |
| `GET`, `POST` | `/tasks` | List/create tasks |
| `GET`, `PATCH`, `DELETE` | `/tasks/{task_id}` | Read/update/soft-delete |
| `POST` | `/tasks/{task_id}/completion` | Complete task idempotently |

Stage transitions use commands because the server validates allowed transitions, permissions, required fields, audit data, and downstream events.

### 4.5 Conversations and messages

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/conversations` | Inbox/search |
| `POST` | `/conversations` | Create manual/internal conversation |
| `GET`, `PATCH` | `/conversations/{conversation_id}` | Read/update assignment/status |
| `GET` | `/conversations/{conversation_id}/messages` | Cursor-paginated messages |
| `POST` | `/conversations/{conversation_id}/message-drafts` | Save human or AI-assisted draft |
| `POST` | `/conversations/{conversation_id}/messages` | Queue outbound message |
| `POST` | `/messages/{message_id}/delivery-retries` | Explicit retry after review |
| `POST` | `/webhooks/{provider}/{account_key}` | Provider webhook ingress |

Creating an outbound message requires `messages:send`, idempotency, current consent/policy checks, and approval if generated or commercially consequential.

### 4.6 Files

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/files/upload-intents` | Validate metadata and return presigned upload |
| `POST` | `/files/{file_id}/completion` | Confirm upload, checksum, and start scan |
| `GET` | `/files/{file_id}` | Read metadata |
| `POST` | `/files/{file_id}/download-intents` | Return short-lived authorized download |
| `DELETE` | `/files/{file_id}` | Request controlled deletion |

Unscanned files cannot be ingested, rendered, downloaded by ordinary users, or sent to an AI provider.

### 4.7 Knowledge base

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/knowledge/sources` | List/create source |
| `GET`, `PATCH` | `/knowledge/sources/{source_id}` | Read/update source |
| `POST` | `/knowledge/sources/{source_id}/sync-runs` | Start ingestion/sync |
| `GET`, `POST` | `/knowledge/documents` | Search/create document metadata |
| `GET`, `PATCH` | `/knowledge/documents/{document_id}` | Read/update document |
| `POST` | `/knowledge/documents/{document_id}/versions` | Create version from clean file or text |
| `GET` | `/knowledge/documents/{document_id}/versions` | Version history |
| `POST` | `/knowledge/document-versions/{version_id}/approvals` | Approve for retrieval |
| `POST` | `/knowledge/search` | Authorized hybrid search/debug |
| `POST` | `/knowledge/answer-runs` | Start grounded knowledge agent |

Raw chunk search is restricted to knowledge managers and diagnostic users. Normal users receive cited answers or approved document results, not unrestricted vector-store access.

### 4.8 Agent runs and approvals

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/agent-runs` | Start an allowed workflow generically |
| `GET` | `/agent-runs` | Filter run history |
| `GET` | `/agent-runs/{run_id}` | Run status and permitted result |
| `GET` | `/agent-runs/{run_id}/events` | SSE progress stream |
| `GET` | `/agent-runs/{run_id}/steps` | Redacted steps for authorized inspection |
| `POST` | `/agent-runs/{run_id}/cancellations` | Request cancellation |
| `POST` | `/agent-runs/{run_id}/retries` | Retry eligible failed run as a new run |
| `GET` | `/approvals` | Current user's approval queue |
| `GET` | `/approvals/{approval_id}` | Approval details and action preview |
| `POST` | `/approvals/{approval_id}/decisions` | Approve or reject |

The generic `/agent-runs` endpoint accepts an allowlisted `workflow_type`, not arbitrary prompts, tools, system instructions, or model IDs. Domain-specific start endpoints are preferred because they provide clearer authorization and input schemas.

### 4.9 Model providers and routing

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/model-providers` | List provider metadata visible to authorized administrators |
| `POST` | `/model-providers` | Register OpenAI, Qwen, compatible-cloud, or local provider metadata |
| `GET`, `PATCH` | `/model-providers/{provider_id}` | Inspect or update provider status and non-secret settings |
| `POST` | `/model-providers/{provider_id}/connection-tests` | Verify credentials, endpoint, protocol, and safe capability probe |
| `GET`, `POST` | `/model-deployments` | List or register approved model deployments |
| `GET`, `PATCH` | `/model-deployments/{deployment_id}` | Inspect/update status, capabilities, limits, and data policy |
| `POST` | `/model-deployments/{deployment_id}/evaluation-runs` | Run the workflow evaluation suite before activation |
| `POST` | `/model-deployments/{deployment_id}/health-checks` | Execute an authorized health/capability check |
| `GET`, `POST` | `/model-routing-policies` | List or create a versioned tenant/workflow routing policy |
| `POST` | `/model-routing-policies/{policy_id}/activations` | Activate an evaluated policy version |
| `POST` | `/model-routing-policies/{policy_id}/retirements` | Retire a policy version |

Provider APIs never return credentials, raw secret references, or unrestricted private endpoint details. Ordinary agent callers cannot select a provider or model directly. The server resolves the active routing policy using workflow requirements, tenant data policy, deployment health, evaluation status, budget, and fallback rules.

Registering an OpenAI-compatible endpoint does not automatically mark tool calling, structured output, tracing, or other capabilities as supported. Capabilities become active only after controlled probes and workflow-specific evaluation.

### 4.10 Proposals

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/proposals` | List/create proposal shell |
| `GET`, `PATCH` | `/proposals/{proposal_id}` | Read/update proposal metadata |
| `GET` | `/proposals/{proposal_id}/versions` | Version history |
| `POST` | `/proposals/{proposal_id}/generation-runs` | Generate AI-assisted draft version |
| `POST` | `/proposals/{proposal_id}/versions` | Create human-edited immutable version |
| `GET` | `/proposal-versions/{version_id}` | Read one version |
| `POST` | `/proposal-versions/{version_id}/render-runs` | Render PDF/DOCX artifact asynchronously |
| `POST` | `/proposal-versions/{version_id}/review-requests` | Request approval |
| `POST` | `/proposals/{proposal_id}/issuances` | Issue approved version |
| `POST` | `/proposals/{proposal_id}/acceptances` | Record verified acceptance |

Proposal issuance checks that the selected version is approved, current, unexpired, fully rendered, and unchanged from the approval digest.

### 4.11 Marketing content

The current Phase 3.2.3.2 implementation exposes a human-operated governance API under `/api/v1/content`:

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/content/requests` | List or create manual content requests |
| `GET`, `PATCH` | `/content/requests/{request_id}` | Read or safely update an unassociated draft request |
| `GET`, `POST` | `/content/assets` | List/filter assets or create an initial manual asset/version |
| `GET` | `/content/assets/{asset_id}` | Read asset details with current and last-approved versions |
| `GET`, `POST` | `/content/assets/{asset_id}/versions` | List immutable history or create a successor version |
| `POST` | `/content/assets/{asset_id}/rollback` | Create a rollback successor without rewriting history |
| `POST` | `/content/assets/{asset_id}/submit-review` | Submit the exact current version and checksum |
| `POST` | `/content/assets/{asset_id}/decisions` | Approve, reject, or request changes under RBAC and separation of duties |
| `POST` | `/content/assets/{asset_id}/archive` | Archive an eligible asset with a reason |
| `POST` | `/content/assets/{asset_id}/restore` | Restore an archived asset as a draft |
| `GET` | `/content/assets/{asset_id}/decisions` | Read approval history with governance permission |
| `GET` | `/content/assets/{asset_id}/audit` | Read append-only audit history with governance permission |

Mutations use `Idempotency-Key` and concurrency-sensitive commands use `If-Match`. Historical versions and audit entries are not mutable through the API. AI generation, scheduling, publication, and outbound delivery endpoints are not implemented in this phase.

### 4.12 Integrations and automation

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/integrations` | List/create integration setup |
| `GET`, `PATCH`, `DELETE` | `/integrations/{integration_id}` | Read/update/disable |
| `POST` | `/integrations/{integration_id}/connection-tests` | Test credentials/scopes |
| `POST` | `/integrations/{integration_id}/secret-rotations` | Begin controlled secret rotation |
| `GET` | `/automation-executions` | Inspect tenant n8n workflow state |
| `GET` | `/automation-executions/{execution_id}` | Execution detail |
| `POST` | `/internal/events/{event_type}` | Service-account n8n event callback |

Integration responses never return credential values. Secret creation accepts a one-time value over TLS or a secret-manager reference, then returns only metadata.

### 4.13 Audit, exports, and operations

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/audit-events` | Filter tenant audit events |
| `POST` | `/imports` | Start validation or apply a confirmed import |
| `GET` | `/imports/{import_id}` | Import validation/application status |
| `POST` | `/exports` | Start controlled data/report export |
| `GET` | `/exports/{export_id}` | Export status |
| `POST` | `/data-subject-requests` | Create privacy request |
| `GET` | `/data-subject-requests/{request_id}` | Track privacy request |
| `GET` | `/health/live` | Process liveness; no dependency detail |
| `GET` | `/health/ready` | Orchestrator readiness |
| `GET` | `/version` | Safe build/version metadata |

Health endpoints reveal no tenant, topology, dependency address, or secret information.

## 5. Request and response examples

### 5.1 Public lead submission

```http
POST /api/v1/public/lead-submissions
Content-Type: application/json
Idempotency-Key: site-8f87f04a-09de-4e12-b98a-a98d461caf42
X-Site-Token: public_site_token
```

```json
{
  "contact": {
    "first_name": "Andi",
    "last_name": "Pratama",
    "email": "andi@example.co.id",
    "phone_e164": "+6281234567890",
    "preferred_language": "id"
  },
  "organization": {
    "name": "Nusantara Hospitality Group",
    "website_url": "https://example.co.id",
    "country_code": "ID"
  },
  "inquiry": {
    "message": "We need a central kitchen for a new hotel in Surabaya.",
    "project_country_code": "ID",
    "project_city": "Surabaya",
    "target_timeline": "Q1 2027"
  },
  "attribution": {
    "source": "website",
    "campaign": "hotel-kitchen-2026"
  },
  "consent": {
    "privacy_policy_version": "2026-07",
    "contact_consent": true,
    "marketing_consent": false
  },
  "captcha_token": "provider_token"
}
```

```json
{
  "submission_id": "83871747-3b7b-4b38-af5a-b87f5bdf0875",
  "status": "accepted",
  "message": "Your inquiry has been received."
}
```

Return `202 Accepted`. Do not reveal internal lead score, salesperson, tenant configuration, or duplicate-match result.

### 5.2 Create an internal lead

```http
POST /api/v1/leads
Authorization: Bearer eyJ...
X-Tenant-Id: 9af036aa-5708-497d-b1af-f2b3d3ff42a2
Idempotency-Key: 01J4R75D5AV3DNHZQBA91K6PX0
```

```json
{
  "contact_id": "c58757cb-2960-4c4a-a886-12e9a3bd6e53",
  "organization_id": "391d4c1b-bd8a-4081-a1b7-29b34d848a3c",
  "source_channel": "manual",
  "source_detail": "Trade show Jakarta",
  "inquiry_summary": "Hotel group planning a 2,000-meal-per-day central kitchen.",
  "priority": "high",
  "project_country_code": "ID",
  "estimated_value": "1250000000.0000",
  "currency": "IDR"
}
```

```json
{
  "id": "06057e69-7b5f-4d32-b2ad-6c39470a2664",
  "status": "new",
  "priority": "high",
  "contact_id": "c58757cb-2960-4c4a-a886-12e9a3bd6e53",
  "organization_id": "391d4c1b-bd8a-4081-a1b7-29b34d848a3c",
  "source_channel": "manual",
  "inquiry_summary": "Hotel group planning a 2,000-meal-per-day central kitchen.",
  "estimated_value": {
    "amount": "1250000000.0000",
    "currency": "IDR"
  },
  "owner": null,
  "created_at": "2026-08-07T09:30:00Z",
  "updated_at": "2026-08-07T09:30:00Z",
  "version": 1
}
```

### 5.3 Update a lead safely

```http
PATCH /api/v1/leads/06057e69-7b5f-4d32-b2ad-6c39470a2664
If-Match: "1"
Content-Type: application/merge-patch+json
```

```json
{
  "priority": "urgent",
  "target_timeline": "Tender closes 2026-09-15"
}
```

The response returns the full updated representation and `ETag: "2"`. JSON Merge Patch semantics distinguish omitted fields from explicit `null`.

### 5.4 Start lead qualification

```http
POST /api/v1/leads/06057e69-7b5f-4d32-b2ad-6c39470a2664/qualification-runs
Idempotency-Key: 01J4R7H4QK7B0PZ5E02DSZYKE3
```

```json
{
  "rubric_key": "commercial_kitchen_project_v1",
  "language": "en",
  "force_human_review": false
}
```

```json
{
  "run_id": "22f27424-2e37-4237-96bf-a4014425725f",
  "workflow_type": "lead_qualification",
  "status": "queued",
  "status_url": "/api/v1/agent-runs/22f27424-2e37-4237-96bf-a4014425725f",
  "events_url": "/api/v1/agent-runs/22f27424-2e37-4237-96bf-a4014425725f/events",
  "created_at": "2026-08-07T09:35:00Z"
}
```

Return `202 Accepted` and `Location` pointing to the run.

### 5.5 Completed qualification result

```json
{
  "id": "22f27424-2e37-4237-96bf-a4014425725f",
  "workflow_type": "lead_qualification",
  "status": "succeeded",
  "subject": {
    "type": "lead",
    "id": "06057e69-7b5f-4d32-b2ad-6c39470a2664"
  },
  "result": {
    "assessment_id": "14fd9a1b-8732-4465-8a32-bb7bce687606",
    "score": 82.5,
    "tier": "hot",
    "need_summary": "A high-capacity central kitchen for a hotel group in Surabaya.",
    "qualification": {
      "budget_status": "unknown",
      "authority_status": "partial",
      "need_status": "confirmed",
      "timeline_status": "confirmed"
    },
    "missing_information": [
      "Approved budget range",
      "Decision-making committee",
      "Available floor plan and utility loads"
    ],
    "recommended_action": "Schedule a discovery call and request the floor plan.",
    "confidence": 0.84,
    "review_status": "pending"
  },
  "usage": {
    "input_tokens": 3450,
    "output_tokens": 620
  },
  "model": {
    "provider_type": "qwen_cloud",
    "deployment_key": "qwen-business-prod-id",
    "model_id": "approved-qwen-model",
    "fallback_used": false
  },
  "started_at": "2026-08-07T09:35:02Z",
  "completed_at": "2026-08-07T09:35:18Z"
}
```

Usage and cost visibility may be role-restricted. Raw chain-of-thought is never returned.

### 5.6 Convert a lead to an opportunity

```http
POST /api/v1/leads/06057e69-7b5f-4d32-b2ad-6c39470a2664/conversions
Idempotency-Key: 01J4R8CBP7DX6WETKG4TZ7C68V
If-Match: "4"
```

```json
{
  "opportunity": {
    "name": "Nusantara Surabaya Central Kitchen",
    "stage": "discovery",
    "estimated_value": "1250000000.0000",
    "currency": "IDR",
    "expected_close_date": "2026-12-15",
    "owner_membership_id": "68246334-142f-44c7-9525-9fb5f8796042"
  },
  "create_follow_up_task": true
}
```

```json
{
  "lead": {
    "id": "06057e69-7b5f-4d32-b2ad-6c39470a2664",
    "status": "converted",
    "version": 5
  },
  "opportunity": {
    "id": "d74ec8ac-bd19-4baa-a080-42e78bec2e84",
    "name": "Nusantara Surabaya Central Kitchen",
    "stage": "discovery",
    "status": "open",
    "version": 1
  },
  "task_id": "fc8f8d60-0efb-47da-b928-92b3e33f3d3e"
}
```

Lead status, opportunity, task, audit record, and outbox events are committed atomically.

### 5.7 Grounded knowledge answer

```http
POST /api/v1/knowledge/answer-runs
Idempotency-Key: 01J4R8STZGJ6FH3SQSQDW9B16K
```

```json
{
  "question": "What Sari Arta capabilities are relevant for a 2,000-meal-per-day hotel central kitchen?",
  "context": {
    "opportunity_id": "d74ec8ac-bd19-4baa-a080-42e78bec2e84"
  },
  "language": "en"
}
```

Completed result:

```json
{
  "run_id": "32e5fc94-6e96-43fd-af62-362cc5fcf649",
  "status": "succeeded",
  "answer": "The approved knowledge base supports planning, engineering, equipment selection, installation, and after-sales service for commercial-kitchen projects. Capacity-specific suitability still requires discovery and engineering validation.",
  "citations": [
    {
      "citation_id": "cit_01J4R9A2",
      "document_id": "f41c1edb-8942-4775-83cf-bfd8ee7b11ea",
      "document_version": 3,
      "title": "Sari Arta Company Capabilities",
      "section": "Engineering and Installation",
      "page": 5
    }
  ],
  "uncertainties": [
    "The source does not establish capacity for this specific site."
  ]
}
```

### 5.8 Start proposal generation

```http
POST /api/v1/proposals/1604c5a1-4b91-4329-8fa6-c1f8272023b2/generation-runs
Idempotency-Key: 01J4R9F54GJZDCDNQ0C2H5YSK1
```

```json
{
  "opportunity_version": 7,
  "template_id": "0fcf1058-4ee4-418b-91e0-48ca8c673266",
  "language": "en",
  "currency": "IDR",
  "sections": [
    "executive_summary",
    "understanding_of_requirements",
    "proposed_solution",
    "delivery_approach",
    "assumptions_and_exclusions"
  ],
  "pricing_source": "approved_opportunity_lines"
}
```

The result is a new immutable proposal version in `draft`; it is never issued automatically.

### 5.9 Approval decision

```http
POST /api/v1/approvals/bfe120bd-10a2-44b7-b741-f90193db9131/decisions
Idempotency-Key: 01J4R9VN4GKCM7V2XFFXGZ1R1Q
If-Match: "1"
```

```json
{
  "decision": "approved",
  "action_digest": "sha256:86ab8e8f...",
  "comment": "Commercial and technical sections reviewed."
}
```

```json
{
  "id": "bfe120bd-10a2-44b7-b741-f90193db9131",
  "status": "approved",
  "decided_by": {
    "user_id": "6682068f-c8dc-4278-83e2-16837893d25c",
    "display_name": "Sales Manager"
  },
  "decided_at": "2026-08-07T10:05:00Z",
  "version": 2
}
```

If the underlying preview no longer matches `action_digest`, return `409 approval_subject_changed`.

### 5.10 Queue an outbound message

```http
POST /api/v1/conversations/25f9bd1f-156b-426b-b78e-36ff5f114a76/messages
Idempotency-Key: 01J4RA6K3Z0SP62EV6P8DPQFA6
```

```json
{
  "draft_message_id": "e809659e-b2ef-4882-b5e1-3863973ace67",
  "channel": "whatsapp",
  "recipient_contact_id": "c58757cb-2960-4c4a-a886-12e9a3bd6e53",
  "approved_template_key": "discovery_call_follow_up",
  "scheduled_at": null
}
```

```json
{
  "id": "5b1bbb85-c49d-4a7b-976e-48877f36ec96",
  "conversation_id": "25f9bd1f-156b-426b-b78e-36ff5f114a76",
  "direction": "outbound",
  "delivery_status": "queued",
  "created_at": "2026-08-07T10:10:00Z"
}
```

Return `202`. Provider acceptance and delivery are reflected asynchronously.

## 6. Agent progress streaming

`GET /agent-runs/{run_id}/events` uses Server-Sent Events:

```text
event: run.status
id: 12
data: {"run_id":"22f27424-2e37-4237-96bf-a4014425725f","status":"running"}

event: run.progress
id: 13
data: {"stage":"retrieving_knowledge","message":"Reviewing approved product and capability sources."}

event: run.completed
id: 14
data: {"status":"succeeded","result_url":"/api/v1/agent-runs/22f27424-2e37-4237-96bf-a4014425725f"}
```

Rules:

- Authenticate before opening the stream and re-check tenant/run access.
- Support `Last-Event-ID` for short reconnection windows.
- Events contain status and safe summaries, not hidden reasoning, secrets, or unrestricted tool payloads.
- Send heartbeats and close after terminal state.
- Clients fall back to polling with conditional requests.

## 7. Webhook contracts

### 7.1 Inbound providers

Provider-specific payloads are accepted only under `/webhooks/{provider}/{account_key}`. The endpoint:

1. Reads the raw body with a strict size limit.
2. Verifies provider signature and timestamp.
3. Resolves the integration account from opaque `account_key`.
4. Deduplicates by provider event ID or payload hash plus time window.
5. Persists a restricted webhook record.
6. Returns the provider-required acknowledgement.
7. Processes the event asynchronously.

Unsupported events may be acknowledged and recorded as `ignored` to prevent endless provider retry.

### 7.2 Outbound platform webhooks

If tenant webhooks are offered, events use a CloudEvents-inspired envelope:

```json
{
  "specversion": "1.0",
  "id": "evt_01J4RAN2K3",
  "type": "opportunity.stage_changed.v1",
  "source": "bd-platform",
  "subject": "opportunities/d74ec8ac-bd19-4baa-a080-42e78bec2e84",
  "time": "2026-08-07T10:15:00Z",
  "tenant_id": "9af036aa-5708-497d-b1af-f2b3d3ff42a2",
  "data": {
    "opportunity_id": "d74ec8ac-bd19-4baa-a080-42e78bec2e84",
    "previous_stage": "discovery",
    "stage": "solution_design",
    "version": 8
  }
}
```

Sign the exact body with a versioned HMAC header, include a timestamp, retry at least once with exponential backoff, expose delivery status, and allow secret rotation with overlapping verification.

## 8. Bulk operations and exports

Bulk imports and exports are always asynchronous.

`POST /imports` accepts a clean uploaded file reference, mapping, duplicate policy, and dry-run flag. It returns a job resource. Validation results are downloadable without applying mutations. Applying an import requires explicit confirmation against the dry-run digest.

`POST /exports` requires resource type, filters, field allowlist, purpose, and format. Large/sensitive exports may require approval. Result files use short-lived download intents, watermarking where appropriate, audit events, and limited retention.

Do not offer generic arbitrary SQL/report endpoints.

## 9. Versioning and compatibility

- Major version is in the URL: `/api/v1`.
- Backward-compatible fields may be added without a major version.
- Existing field meaning and type do not change within a major version.
- Clients ignore unknown response fields.
- Breaking changes receive a migration guide, deprecation headers, telemetry review, and announced sunset.
- Event types and agent input/output schemas carry independent versions.
- OpenAPI documents are generated in CI and diffed for breaking changes.

Example deprecation headers:

```http
Deprecation: true
Sunset: Sat, 01 Aug 2027 00:00:00 GMT
Link: <https://docs.example.com/migrations/v1-old-endpoint>; rel="deprecation"
```

## 10. API security requirements

- Enforce object-level authorization on every ID-based endpoint.
- Use parameterized database access.
- Validate all request and provider schemas with strict extra-field policy where appropriate.
- Apply maximum depth/length/count constraints to JSON and strings.
- Never accept arbitrary object-storage keys or URLs for server fetch; use issued file IDs and egress allowlists.
- Sanitize rich text and prevent stored XSS.
- Check file malware status before use.
- Redact sensitive attributes in logs, errors, traces, and audit summaries.
- Record security-relevant denials without leaking target existence.
- Agent endpoints accept business intent and bounded options, not system prompts or arbitrary tools.
- Agent callers cannot override model routing. Administrative model configuration is versioned, evaluated, permission-controlled, and audited.
- Model routing must enforce tenant-approved provider, region, retention, network boundary, and maximum data-classification policy before dispatch.
- Consequential operations re-check permission, state, consent, policy, approval digest, and resource version at execution time.

## 11. Observability and operational behavior

Every response contains `X-Request-Id`. Asynchronous resources correlate:

- `request_id`
- `job_id`
- `agent_run_id`
- `automation_execution_id`
- `trace_id`
- Business resource IDs

Metrics include endpoint latency/error rate, authorization denials, idempotency replay, rate-limit rejections, queue acknowledgement time, agent completion/cost, provider delivery, and webhook age.

The API exposes no public metrics endpoint. Operations telemetry is available through the protected observability platform.

## 12. OpenAPI and contract governance

FastAPI-generated OpenAPI is reviewed as a product contract, not treated as incidental output.

- Operation IDs are stable and human-readable.
- Every endpoint documents permissions, idempotency, concurrency, rate limits, and error codes.
- Request and response schemas have examples and field descriptions.
- TypeScript types/clients are generated for the Next.js application.
- n8n uses a restricted service API specification containing only its approved endpoints.
- Contract tests verify clients against the specification.
- Security tests cover cross-tenant IDs, stale versions, replayed commands, expired approvals, malicious uploads, and prompt-like content.
- Provider contract tests verify Qwen and local deployments against declared structured-output, tool-calling, streaming, timeout, usage, and error-normalization capabilities.
- API changes are checked for backward compatibility in CI.

## 13. Initial endpoint delivery order

1. Authentication context, tenants, memberships, health, and audit foundation.
2. Organizations, contacts, leads, activities, tasks, and lead conversion.
3. Conversations, messages, website/email webhook capture, and file lifecycle.
4. Knowledge ingestion, search, and grounded answer runs.
5. Lead qualification and agent run/approval inspection.
6. Opportunities and proposal generation/review/issuance.
7. Customer research, marketing content, additional channel integrations, and n8n automation.
8. Privacy workflows, advanced exports, and tenant administration.

Each release requires OpenAPI review, authorization matrix tests, tenant-isolation tests, idempotency/concurrency tests, and operational dashboards before production promotion.

## Phase 2.5.1 knowledge management API

The `/api/v1/knowledge-management` control-plane API supports collection creation/listing, version-1 upload, document search/detail, review submission, approve/reject, same-domain agent binding, activation, and archive. Read operations require `knowledge:retrieve`; mutations require `knowledge:manage`. These endpoints never call embeddings or vector retrieval.

Phase 2.5.2 adds `POST /documents/{id}/processing-runs` and `GET /processing-runs/{run_id}`. The command accepts only approved/active current versions with enabled agent bindings and returns `202`. Document responses include `processing_status`; uploads also accept DOCX. No endpoint exposes similarity search.

## Phase 2.5.3 knowledge governance API

The control plane now exposes governed metadata update, replacement-version upload, immutable version history, safe rollback, separate publish and activate commands, archive/restore, binding status changes, and a document audit timeline. Metadata update, replacement, and rollback use `If-Match` and return `412` for a stale `record_version`.

Permissions are split into `knowledge:upload`, `knowledge:edit`, `knowledge:submit_review`, `knowledge:approve`, `knowledge:publish`, `knowledge:archive`, `knowledge:restore`, `knowledge:process`, and `knowledge:audit_read`. Read-only metadata access remains `knowledge:retrieve`. Every command rechecks tenant ownership and state; approval, publication, and activation are separate transitions. See `knowledge-governance-design.en.md` for the endpoint matrix.

## Phase 2.6.1 knowledge retrieval API

`POST /api/v1/knowledge/search` accepts `tenant_id`, `agent_id`, a bounded query, exact language, and `top_k`. The request tenant must equal the authenticated workspace. Authorization for the active tenant agent and `approved_knowledge_retrieval` capability occurs before query embedding.

Results come only from active documents whose approved exact version equals both `published_version_id` and `active_version_id`, whose same-agent binding is enabled, and whose processing run completed. Each result returns document name, immutable version, chunk text, page, section, metadata, similarity, and a citation containing document/version/chunk IDs. Empty evidence returns `200 insufficient_evidence`. See `knowledge-retrieval-design.en.md`.

## Phase 2.6.2 retrieval diagnostics

The response additionally returns `correlation_id`, `duration_ms`, `similarity_threshold`, `minimum_evidence_count`, `decision_reason`, and `below_threshold_results`. Formal evidence remains limited to `results`. The internal test UI requests diagnostics with `include_diagnostics=true`; the flag defaults to `false`. Below-threshold results must not be used for generated answers. See `knowledge-retrieval-evaluation.en.md`.

## Phase 2.6.3 read-only Knowledge Assistant API

`POST /api/v1/knowledge/assistant/runs` accepts only `agent_id`, `language`, and a bounded `question`, requires `knowledge:retrieve` and `Idempotency-Key`, authorizes before queueing, and returns `202`. `GET /api/v1/knowledge/assistant/runs/{run_id}` returns status and the final structured result. The worker reauthorizes before embedding, then performs governed retrieval, deterministic evidence/conflict validation, no-tools generation only for sufficient evidence, and application-side citation validation. The endpoint is restricted to the Commercial Kitchen Agent; IVC remains denied. See `knowledge-assistant-design.en.md`.

## Phase 3.1 public consultation API

`POST /api/v1/public/consultation/turns` accepts a bounded English or Chinese answer for the current field in a fixed project-intake sequence. A server-held `X-Site-Token`, separate Redis rate limit, strict validation and abuse screening run before an optional no-tools public response provider. The endpoint cannot retrieve internal knowledge or CRM data.

After explicit contact consent, the website reuses `POST /api/v1/public/lead-submissions` with source `website_ai_assistant`. The endpoint retains idempotency, tenant scoping and validation, adds 24-hour duplicate suppression by normalized email/source/project/city, records create/duplicate audit events, and returns `duplicate`. The resulting lead remains new, unassigned and unqualified. See `public-consultation-agent-design.en.md`.

## Phase 3.2.3.4 governed marketing generation API

`POST /api/v1/content/requests/{request_id}/generate` requires `content:generate` and `Idempotency-Key`, authorizes the exact development Marketing Agent and `public_marketing_v1` policy before queueing, and returns `202`. `GET /api/v1/content/generation-runs/{run_id}` returns tenant-scoped status, evidence state, provider/model, duration, citations, and either a generated asset/version pointer or explicit insufficient evidence.

The worker reauthorizes before embedding, retrieval, or model use. A successful result creates only an immutable `ai_generated` version in `generated` status. It cannot approve, publish, send, schedule, archive, or write CRM data. See `marketing-content-generation-runtime.en.md`.

## Phase 3.2.3.5 marketing generation evaluation API

`POST /api/v1/content/assets/{asset_id}/feedback` requires `content:review` and an `Idempotency-Key`. It binds human-authored structured feedback to an exact version and SHA-256 checksum. `GET /api/v1/content/assets/{asset_id}/evaluation` requires `content:read` and returns the tenant-scoped generation outcome, evidence state, provider/model, deterministic quality projection, Human Edit Distance when available, citations, latency, correlation ID, usage/cost availability, and immutable feedback. Neither endpoint publishes, sends, schedules, approves, or writes CRM data. See `marketing-generation-evaluation.en.md`.

`GET /api/v1/content/acceptance` requires `content:read` and returns the fixed ten-case Phase 3.2 acceptance projection: preparation/review/decision counts, exact generated and approved-human version pointers, real Human Edit Distance only for a human successor, common feedback, quality averages, and explicit Brand Guideline/OpenAI comparison checkpoints. It reuses existing governed records and does not create a parallel approval lifecycle. See `marketing-content-business-acceptance.en.md`.
