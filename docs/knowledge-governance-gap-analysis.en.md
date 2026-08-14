# Enterprise Knowledge Governance Gap Analysis

## 1. Purpose and review scope

This review evaluates whether the Phase 2.5.1 Knowledge Management control plane and Phase 2.5.2 processing pipeline provide sufficient enterprise document governance before Knowledge Retrieval is enabled.

The assessment is based on the implementation as of 2026-08-14, principally:

- `apps/api/src/sari_api/adapters/models.py`
- `apps/api/src/sari_api/adapters/enterprise_knowledge_repository.py`
- `apps/api/src/sari_api/api/routes/knowledge_management.py`
- `apps/api/src/sari_api/domain/identity.py`
- `apps/web/src/app/(workspace)/knowledge/`
- migrations `6b2a8e4d1c90` and `a7d4c2e91f63`
- Phase 2.5.1 and Phase 2.5.2 integration tests

This is a gap analysis and implementation proposal only. It does not change application code, APIs, permissions, or database schema.

### Rating definitions

| Rating | Meaning |
|---|---|
| Supported | The data model, API/service behavior, authorization, and usable workflow exist |
| Partial | Some data or behavior exists, but the end-to-end governance capability is incomplete |
| Not supported | No safe application workflow exists |

## 2. Executive conclusion

The current system is a sound approval-controlled upload foundation, but it is not yet a complete enterprise document governance system. It can create a logical document with immutable version 1, record a basic reviewer decision, bind the document to a same-domain agent, activate it, process it, and archive it. Tenant RLS protects the managed knowledge tables.

It cannot update document metadata, upload version 2+, restore an archived document, disable a binding, inspect a document-centric audit timeline, or roll back to earlier content. Upload, approval, publication, binding, and archive all use the single broad `knowledge:manage` permission, so there is no enforceable separation of duties.

The recommended gate is:

```text
Phase 2.5.2 processing
        ↓
Phase 2.5.3 governance completion
        ↓
Knowledge Retrieval
```

Retrieval should not become generally available until the exact published version, authorization state, and governance history can be determined reliably.

### Capability summary

| Area | Capability | Rating | Current evidence | Primary gap |
|---|---|---:|---|---|
| CRUD | Create/upload | Supported | Upload creates logical document and immutable version 1 | No metadata-only draft creation |
| CRUD | Update metadata | Not supported | Metadata is accepted only during initial upload | No PATCH API, UI, concurrency control, or change audit |
| CRUD | Replace document version | Not supported | Version table and `current_version_number` exist | No version-upload command or state reset |
| CRUD | Archive | Supported | Approved/active documents can be archived | No required reason; no archive attribution fields |
| CRUD | Restore | Not supported | Archived is terminal in current service | No safe transition or republish requirement |
| Attribution | Creator/uploader/approver | Partial | IDs and core timestamps are stored | Version uploader is not returned; no updater/publisher/archiver fields |
| Audit | Upload/approval/lifecycle | Partial | Successful command events enter `audit_events` | No document audit API/UI, weak event snapshots, no failed attempts |
| Audit | Binding history | Partial | Binding creation is audited | No disable/re-enable operation or history view |
| Versioning | Version number/history | Partial | Immutable rows and repository list method exist | No public version-list endpoint or UI |
| Versioning | Active/published version | Partial | Current number and lifecycle status exist | No explicit `published_version_id` authority |
| Versioning | Rollback | Not supported | No command exists | Must preserve immutability and require fresh approval |
| RBAC | Upload/approve/publish separation | Not supported | Admin has broad `knowledge:manage`; sales has read | One admin may perform all consequential actions |

## 3. Document CRUD analysis

### 3.1 Create

**Rating: Supported, with a narrow definition.**

`POST /api/v1/knowledge-management/collections/{collection_id}/documents` stores a private object, creates `managed_knowledge_documents`, creates `knowledge_document_versions` version 1, records SHA-256 and size, assigns `created_by`, and writes `knowledge.document.uploaded`.

Strengths:

- Tenant-prefixed object key.
- File type and size validation.
- Immutable version record with checksum.
- Database/object cleanup when the database transaction fails.
- Tenant RLS and explicit tenant predicates.

Limitations:

- Creation and first upload are one operation; a metadata-only draft is not supported.
- Uploader and logical creator are necessarily the same user for version 1.
- No idempotency key protects a retried upload.
- There is no malware-scanning or quarantine state in this implementation.

### 3.2 Update metadata

**Rating: Not supported.**

The logical document stores `title`, `document_type`, `language`, and `document_metadata`, but no repository method, API endpoint, or UI permits editing them. Collection metadata is also create-only.

Required governance behavior:

- Permit controlled editing while a document is `draft`, `uploaded`, or `review`.
- Define which changes invalidate approval. Title formatting may not; language, document type, classification, effective dates, or evidence scope should.
- Require optimistic concurrency through the existing record `version` field and `If-Match`.
- Audit before/after values without placing sensitive document content in the event.
- Reset processed assets when retrieval-relevant metadata changes.

### 3.3 Replace document version

**Rating: Not supported.**

The schema can store multiple immutable versions, and the repository contains `list_versions()`, but the application creates only version 1. There is no upload-new-version API, current-version switch, approval reset, version listing route, or version history UI.

A replacement must:

1. Lock the logical document.
2. Store new bytes under a new immutable object key.
3. Create version `N + 1` with its own uploader, checksum, metadata, and timestamp.
4. Set `current_version_number = N + 1`.
5. Reset lifecycle to `uploaded`, approval to `pending`, and processing to `uploaded`.
6. Revoke publication eligibility for the superseded version.
7. Preserve all old versions, decisions, processing runs, chunks, and citations as historical evidence.

### 3.4 Archive

**Rating: Supported, but incomplete for enterprise governance.**

Approved or active current documents can move to `archived`, and an audit event is written. Future processing already rejects archived documents.

Gaps:

- Archive reason is not required or stored on the document.
- `archived_by` and `archived_at` are not first-class fields.
- Existing agent bindings remain enabled; current retrieval can still be made safe by filtering lifecycle, but explicit revocation is easier to reason about.
- The current version status changes to archived, but no explicit published-version pointer is cleared.
- There is no test proving future retrieval cannot return archived chunks.

### 3.5 Restore

**Rating: Not supported.**

Archived documents have no outgoing lifecycle transition. A safe restore should return the document to `approved`, not directly to `active`, and require an explicit publish action. If approval has expired, policy changed, or the underlying version is no longer eligible, it should return to `review` instead.

Restore must never silently reactivate old bindings or make stale chunks retrievable.

## 4. User attribution analysis

### 4.1 What is stored today

| Record/action | Current attribution |
|---|---|
| Collection creation | `knowledge_collections.created_by`, `created_at`, `updated_at` |
| Logical document creation | `managed_knowledge_documents.created_by`, `created_at`, `updated_at` |
| Version upload | `knowledge_document_versions.created_by`, `created_at` |
| Approval | `approved_by`, `approved_at`, `review_note` for approved decisions |
| Rejection | Actor exists only in the generic audit event |
| Binding creation | Binding `created_by`, `created_at`; actor also in audit event |
| Activation/archive | Actor and time exist only in audit event |
| Processing request | Processing run `created_by`, `created_at`, correlation ID |

### 4.2 Attribution gaps

- `VersionResponse` does not expose `created_by`, so users cannot see who uploaded a version.
- `BindingResponse` does not expose `created_by`.
- IDs are not resolved to safe display names in the knowledge UI.
- There is no `updated_by`, `submitted_by/at`, `published_by/at`, `archived_by/at`, or `restored_by/at` on the controlled resource.
- A rejected decision does not have a first-class reviewer and timestamp on the document/version.
- Approval belongs logically to an exact version, but the current approval fields live on the logical document. This becomes ambiguous as soon as version 2 exists.
- There is no explicit system/service actor representation for background governance events.

## 5. Audit trail analysis

### 5.1 Events currently written

The control-plane API records successful events for:

- Collection creation.
- Version-1 document upload.
- Review submission.
- Approval or rejection.
- Agent binding creation.
- Activation.
- Archive.
- Processing request.

Each event includes tenant, actor, action, target, result, correlation/request ID, details, and timestamp.

### 5.2 Audit gaps

**Rating: Partial.** Event creation exists, but a usable governance trail does not.

- No API or UI lists audit events for a document or exact version.
- No event is generated for metadata update, new version, binding disable/re-enable, restore, rollback, or explicit publication because those commands do not exist.
- Approval events do not consistently snapshot exact `document_version_id`, version number, checksum, or reviewed content fingerprint.
- Lifecycle events do not capture previous state, new state, reason, or exact published version.
- Binding events do not store binding ID or prior/new status.
- Only successful operations are recorded; denied or invalid consequential attempts are not captured as governance security events.
- The generic `audit_events` table is not protected by the forced tenant RLS applied to the managed knowledge tables, and no knowledge audit read boundary currently exists.
- Append-only behavior is an application convention, not a database-enforced guarantee.
- Retention, export, legal hold, and tamper-evidence policies are not implemented.

Before retrieval, the minimum requirement is a tenant-scoped, document-centric read-only audit endpoint backed by complete exact-version event payloads. Strong cryptographic tamper evidence and legal hold can remain a later compliance enhancement.

## 6. Version management analysis

### 6.1 Version number

**Rating: Partial.** The database enforces unique `(tenant_id, document_id, version_number)`, stores immutable object keys and checksums, and keeps `current_version_number`. The API detail response shows only the current version. The existing repository list function is not exposed.

### 6.2 Active/published version

**Rating: Partial.** `lifecycle_status = active` and current version status indicate activation, but there is no explicit immutable `published_version_id`. A numeric pointer plus mutable lifecycle state is insufficient as the long-term retrieval authority when replacements and rollback exist.

Recommended source of truth:

```text
logical document
  ├── current_version_id    → version being edited/reviewed
  └── published_version_id  → exact version eligible for retrieval, or NULL
```

Retrieval must use `published_version_id`, not merely the highest version number.

### 6.3 Rollback

**Rating: Not supported.**

Rollback should not move a pointer backward and pretend history did not happen. The recommended command creates version `N + 1` by copying the selected historical object and metadata, records `restored_from_version_id`, and sends the new version through review and publication. This preserves monotonic version numbers and unambiguous citations.

## 7. RBAC analysis

### 7.1 Current permissions

The running MVP has two roles:

| Role | Knowledge permissions | Effective capability |
|---|---|---|
| `admin` | `knowledge:manage`, `knowledge:retrieve` | Create collections, upload, submit, approve/reject, bind, activate, archive, process, and read |
| `sales` | `knowledge:retrieve` | List and view metadata/status |

All mutations use `knowledge:manage`. Therefore the system cannot answer independently:

- Who may upload?
- Who may approve?
- Who may publish?

The answer to all three is currently “any tenant admin,” including the same person on the same document.

### 7.2 Required permission split

Phase 2.5.3 should introduce these explicit permissions while retaining `knowledge:manage` only as a temporary compatibility aggregate:

| Permission | Intended operations |
|---|---|
| `knowledge:read` | View collections, documents, versions, bindings, and permitted audit history |
| `knowledge:upload` | Create document, edit allowed metadata, upload a replacement version |
| `knowledge:submit` | Submit exact current version for review |
| `knowledge:approve` | Approve/reject an exact version |
| `knowledge:bind` | Enable or disable agent bindings |
| `knowledge:publish` | Activate/publish, archive, and restore according to policy |
| `knowledge:process` | Request processing for an eligible exact version |
| `knowledge:audit_read` | Read governance events |

Recommended role intent for the future enterprise role model:

| Role | Upload | Approve | Publish | Read |
|---|---:|---:|---:|---:|
| Tenant Admin | ✓ | ✓ | ✓ | ✓ |
| Sales Manager | Optional | ✓ for business content | ✓ for business content | ✓ |
| Sales User | Optional draft/upload | — | — | ✓ |
| Technical User | ✓ for technical content | ✓ under technical policy | — by default | ✓ |
| Viewer | — | — | — | ✓ |

For the current two-role MVP, `admin` can initially receive all new permissions and `sales` can retain read-only access. However, self-approval should be blocked when the tenant enables separation-of-duties policy, and the richer enterprise roles should be introduced before real multi-tenant use.

## 8. Risks before Knowledge Retrieval

| Risk | Severity | Why it matters |
|---|---:|---|
| No explicit published exact version | Critical | Retrieval could use the wrong or superseded content |
| No replacement/version release workflow | High | Corrections cannot be governed without creating another logical document |
| No restore/rollback | High | Operational recovery invites direct database intervention |
| One broad management permission | High | Uploaders can approve and publish their own content |
| Audit history is not user-visible | High | Reviewers cannot establish provenance or reconstruct decisions |
| Approval fields live only on logical document | High | Approval becomes ambiguous after version 2 |
| Binding cannot be disabled | High | Agent authorization cannot be explicitly revoked |
| Metadata changes are impossible | Medium | Incorrect classification and language cannot be safely corrected |
| No optimistic concurrency/idempotency | Medium | Concurrent commands or retries may create inconsistent governance outcomes |

## 9. Phase 2.5.3 implementation plan

### 9.1 Objective

Complete the minimum enterprise document governance control plane needed to make future retrieval deterministic, revocable, attributable, and auditable without implementing retrieval or a conversational assistant.

### 9.2 Milestone A — Schema and invariants

Add a non-destructive migration that:

1. Adds `current_version_id` and nullable `published_version_id` to managed documents while preserving `current_version_number` during transition.
2. Adds version-level approval fields: `review_status`, `reviewed_by`, `reviewed_at`, `review_note`, and optional `restored_from_version_id`.
3. Adds document governance attribution: `updated_by`, `published_by/at`, `archived_by/at`, and archive/restore reason fields.
4. Adds `updated_by/at` to bindings and preserves disabled binding rows rather than deleting them.
5. Adds constraints ensuring version/document tenant alignment and valid published-version ownership, using application checks plus database constraints where PostgreSQL can enforce them safely.
6. Adds tenant RLS to the governance audit read path and suitable indexes for document/version timelines.

Existing version-1 documents should be backfilled so `current_version_id` references their current version. Existing active documents should receive `published_version_id` pointing to that exact approved version. No document bytes are rewritten.

### 9.3 Milestone B — Application services and state machine

Implement typed, transactional commands for:

- Update allowed metadata with `If-Match`.
- Upload replacement version `N + 1`.
- List and inspect all immutable versions.
- Submit an exact version for review.
- Approve/reject an exact version.
- Publish an exact approved version.
- Archive a published document.
- Restore an archived document to `approved` or `review`, never directly to published.
- Roll back by creating a new version from a historical version.
- Disable and re-enable an agent binding.

Consequential commands should require a reason where appropriate, be idempotent, lock the logical document, validate tenant/domain/agent alignment, and record the exact before/after state in the same transaction.

### 9.4 Milestone C — API contract

Recommended endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `PATCH` | `/api/v1/knowledge-management/documents/{id}` | Update allowed metadata with `If-Match` |
| `POST` | `/api/v1/knowledge-management/documents/{id}/versions` | Upload immutable replacement version |
| `GET` | `/api/v1/knowledge-management/documents/{id}/versions` | List complete version history |
| `GET` | `/api/v1/knowledge-management/documents/{id}/versions/{version_id}` | Inspect one exact version |
| `POST` | `/api/v1/knowledge-management/documents/{id}/versions/{version_id}/submit-review` | Submit exact version |
| `POST` | `/api/v1/knowledge-management/documents/{id}/versions/{version_id}/approval` | Approve/reject exact version |
| `POST` | `/api/v1/knowledge-management/documents/{id}/versions/{version_id}/publish` | Publish exact approved version |
| `POST` | `/api/v1/knowledge-management/documents/{id}/archive` | Revoke publication with reason |
| `POST` | `/api/v1/knowledge-management/documents/{id}/restore` | Restore to a non-published state |
| `POST` | `/api/v1/knowledge-management/documents/{id}/versions/{version_id}/rollback` | Create reviewed successor from history |
| `PATCH` | `/api/v1/knowledge-management/documents/{id}/bindings/{binding_id}` | Enable/disable binding |
| `GET` | `/api/v1/knowledge-management/documents/{id}/audit-events` | Read document governance timeline |

Pre-production legacy lifecycle endpoints may remain as compatibility wrappers during the UI transition, but should call the same version-aware services.

### 9.5 Milestone D — RBAC and policy

1. Add the explicit permissions in section 7.2.
2. Map current `admin` to all governance permissions and current `sales` to read-only initially, preserving Phase 1 behavior.
3. Introduce a policy hook for `uploader_user_id != approver_user_id` and optional publisher separation.
4. Require approval and publish authorization against the exact version fingerprint.
5. Deny all unknown or missing grants by default.

### 9.6 Milestone E — Audit and UI

Extend `/knowledge` with:

- Document detail page rather than only list-row commands.
- Editable metadata panel with concurrency errors.
- Version history showing uploader, checksum, status, decision, and publication state.
- Approval and publication controls shown only when authorized.
- Agent binding panel with enable/disable history.
- Read-only document timeline combining upload, metadata, review, approval, binding, processing, publication, archive, restore, and rollback events.
- Clear labels for current version versus published version.

Audit payloads should contain IDs, safe metadata diffs, checksums, state transitions, actor, reason, and correlation ID—but never raw document text, credentials, or storage keys.

### 9.7 Milestone F — Tests and acceptance

Required validation:

- Version numbers are monotonic under concurrent uploads.
- Failed object/database operations leave neither orphan state nor a partially current version.
- Replacement invalidates approval and does not alter old versions.
- Publish selects only an approved exact version with eligible bindings.
- Archive immediately removes retrieval eligibility while preserving chunks and history.
- Restore never directly republishes.
- Rollback creates a new version and requires fresh approval.
- Disabled bindings cannot process or retrieve.
- Upload, approve, publish, audit-read permissions are independently enforced.
- Configured self-approval is rejected and audited.
- Every governance command emits one correlated audit event in the same transaction.
- Cross-tenant document, version, binding, and audit access returns no data.
- Existing Sari Arta and IVC demo documents migrate without changing CRM or Agent Playground behavior.

### 9.8 Recommended implementation order

```text
1. Migration and backfill
2. Version-aware repository/services
3. Permission split and policy checks
4. Version/metadata/binding APIs
5. Publish/archive/restore/rollback commands
6. Audit timeline API
7. Knowledge detail UI
8. Integration, RLS, concurrency, and regression tests
9. Bilingual documentation and demo data refresh
```

## 10. Phase 2.5.3 acceptance gate

Phase 2.5.3 is complete when an authorized reviewer can answer, using only the product:

1. Who uploaded this exact content, and when?
2. What metadata changed, by whom, and why?
3. Which exact immutable version was approved?
4. Who approved and who published it?
5. Which agents currently have access, and who changed that access?
6. Is the document archived, restored, superseded, or rolled back?
7. Can the system prove that an ineligible version cannot be processed or retrieved?

Only after these questions have deterministic, tenant-isolated answers should Knowledge Retrieval use `published_version_id` and enabled bindings as mandatory filters.

## 11. Explicitly out of scope

Phase 2.5.3 should not implement:

- Vector similarity search or hybrid retrieval.
- Conversational Knowledge Assistant.
- Automatic approval or publication by AI.
- OCR, document redaction, DLP, legal hold, or records-management certification.
- External customer communication.
- Changes to CRM, Agent Playground, or qualification workflows.

