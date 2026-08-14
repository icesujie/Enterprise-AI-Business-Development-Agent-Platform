import Link from "next/link";

import { PageHeader } from "@/components/workspace/page-header";
import { getLocale } from "@/i18n/server";
import {
  apiFetch,
  type CurrentIdentity,
  type KnowledgeAuditLog,
  type KnowledgeDocumentVersion,
  type ManagedKnowledgeDocument,
} from "@/lib/api";

import {
  activateKnowledgeDocument,
  archiveKnowledgeDocument,
  bindKnowledgeDocument,
  processKnowledgeDocument,
  publishKnowledgeDocument,
  restoreKnowledgeDocument,
  reviewKnowledgeDocument,
  rollbackKnowledgeVersion,
  submitKnowledgeReview,
  updateKnowledgeBinding,
  updateKnowledgeDocument,
  uploadKnowledgeDocumentVersion,
} from "../actions";

export default async function KnowledgeDocumentPage({
  params,
}: PageProps<"/knowledge/[id]">) {
  const { id } = await params;
  const [document, versions, identity, locale] = await Promise.all([
    apiFetch<ManagedKnowledgeDocument>(
      `/api/v1/knowledge-management/documents/${id}`,
    ),
    apiFetch<KnowledgeDocumentVersion[]>(
      `/api/v1/knowledge-management/documents/${id}/versions`,
    ),
    apiFetch<CurrentIdentity>("/api/v1/me"),
    getLocale(),
  ]);
  const canAudit = identity.permissions.includes("knowledge:audit_read");
  const audit = canAudit
    ? await apiFetch<KnowledgeAuditLog[]>(
        `/api/v1/knowledge-management/documents/${id}/audit-events`,
      )
    : [];
  const zh = locale === "zh-CN";
  const copy = zh ? chinese : english;
  const current = versions.find(
    (item) => item.id === document.current_version_id,
  );

  return (
    <div className="space-y-7">
      <Link
        href="/knowledge"
        className="text-sm font-semibold text-[var(--color-brand)]"
      >
        ← {copy.back}
      </Link>
      <PageHeader
        eyebrow={`${copy.eyebrow} · v${document.current_version_number}`}
        title={document.title}
        description={`${document.collection_name} · ${document.document_type} · ${document.language}`}
      />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <PointerCard
          label={copy.lifecycle}
          value={statusLabel(document.lifecycle_status, zh)}
        />
        <PointerCard
          label={copy.currentVersion}
          value={pointerLabel(document.current_version_id, versions)}
        />
        <PointerCard
          label={copy.publishedVersion}
          value={pointerLabel(document.published_version_id, versions)}
        />
        <PointerCard
          label={copy.activeVersion}
          value={pointerLabel(document.active_version_id, versions)}
          accent={Boolean(document.active_version_id)}
        />
      </section>

      <section className="card p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold">{copy.governanceActions}</h2>
            <p className="mt-1 text-sm text-[var(--color-muted)]">
              {copy.governanceHelp}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {has(identity, "knowledge:submit_review") &&
            document.lifecycle_status === "uploaded" ? (
              <form action={submitKnowledgeReview.bind(null, document.id)}>
                <button className="button-tertiary" type="submit">
                  {copy.submit}
                </button>
              </form>
            ) : null}
            {has(identity, "knowledge:approve") &&
            document.lifecycle_status === "review" &&
            document.approval_status === "pending" ? (
              <>
                <form
                  action={reviewKnowledgeDocument.bind(
                    null,
                    document.id,
                    "approved",
                  )}
                >
                  <button className="button-primary" type="submit">
                    {copy.approve}
                  </button>
                </form>
                <form
                  action={reviewKnowledgeDocument.bind(
                    null,
                    document.id,
                    "rejected",
                  )}
                >
                  <button className="button-tertiary" type="submit">
                    {copy.reject}
                  </button>
                </form>
              </>
            ) : null}
            {has(identity, "knowledge:publish") &&
            document.lifecycle_status === "approved" ? (
              <form action={publishKnowledgeDocument.bind(null, document.id)}>
                <button className="button-primary" type="submit">
                  {copy.publish}
                </button>
              </form>
            ) : null}
            {has(identity, "knowledge:publish") &&
            document.lifecycle_status === "published" ? (
              <form action={activateKnowledgeDocument.bind(null, document.id)}>
                <button className="button-primary" type="submit">
                  {copy.activate}
                </button>
              </form>
            ) : null}
            {has(identity, "knowledge:process") &&
            ["approved", "published", "active"].includes(
              document.lifecycle_status,
            ) &&
            document.processing_status !== "processing" ? (
              <form action={processKnowledgeDocument.bind(null, document.id)}>
                <button className="button-tertiary" type="submit">
                  {document.processing_status === "completed"
                    ? copy.reprocess
                    : copy.process}
                </button>
              </form>
            ) : null}
          </div>
        </div>
        {has(identity, "knowledge:archive") &&
        ["approved", "published", "active"].includes(
          document.lifecycle_status,
        ) ? (
          <form
            action={archiveKnowledgeDocument.bind(null, document.id)}
            className="mt-5 flex flex-col gap-3 border-t border-[var(--color-line)] pt-5 sm:flex-row"
          >
            <input
              className="field flex-1"
              name="reason"
              minLength={3}
              placeholder={copy.archiveReason}
              required
            />
            <button className="button-tertiary" type="submit">
              {copy.archive}
            </button>
          </form>
        ) : null}
        {has(identity, "knowledge:restore") &&
        document.lifecycle_status === "archived" ? (
          <form
            action={restoreKnowledgeDocument.bind(null, document.id)}
            className="mt-5 flex flex-col gap-3 border-t border-[var(--color-line)] pt-5 sm:flex-row"
          >
            <input
              className="field flex-1"
              name="reason"
              minLength={3}
              placeholder={copy.restoreReason}
              required
            />
            <button className="button-primary" type="submit">
              {copy.restore}
            </button>
          </form>
        ) : null}
      </section>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="card p-6">
          <h2 className="text-lg font-semibold">{copy.metadata}</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            {copy.metadataHelp}
          </p>
          {has(identity, "knowledge:edit") &&
          !["active", "archived"].includes(document.lifecycle_status) ? (
            <form
              action={updateKnowledgeDocument.bind(
                null,
                document.id,
                document.record_version,
              )}
              className="mt-5 space-y-4"
            >
              <Field label={copy.title} name="title" value={document.title} />
              <Field
                label={copy.documentType}
                name="document_type"
                value={document.document_type}
              />
              <label className="label">
                {copy.language}
                <select
                  className="field mt-2"
                  name="language"
                  defaultValue={document.language}
                >
                  <option value="en">English</option>
                  <option value="zh-CN">中文</option>
                  <option value="id">Bahasa Indonesia</option>
                </select>
              </label>
              <label className="label">
                {copy.metadataJson}
                <textarea
                  className="field mt-2 min-h-32 font-mono text-xs"
                  name="document_metadata_json"
                  defaultValue={JSON.stringify(
                    document.document_metadata,
                    null,
                    2,
                  )}
                />
              </label>
              <button className="button-primary" type="submit">
                {copy.saveMetadata}
              </button>
            </form>
          ) : (
            <pre className="mt-5 overflow-x-auto rounded-xl bg-[var(--color-surface-muted)] p-4 text-xs">
              {JSON.stringify(document.document_metadata, null, 2)}
            </pre>
          )}
        </section>

        <section className="card p-6">
          <h2 className="text-lg font-semibold">{copy.newVersion}</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            {copy.newVersionHelp}
          </p>
          {has(identity, "knowledge:upload") ? (
            <form
              action={uploadKnowledgeDocumentVersion.bind(
                null,
                document.id,
                document.record_version,
              )}
              className="mt-5 space-y-4"
            >
              <label className="label">
                {copy.file}
                <input
                  className="field mt-2"
                  type="file"
                  name="file"
                  accept=".pdf,.docx,.txt,.md"
                  required
                />
              </label>
              <label className="label">
                {copy.versionMetadata}
                <textarea
                  className="field mt-2 min-h-24 font-mono text-xs"
                  name="version_metadata_json"
                  defaultValue='{"source":"workspace_version_upload"}'
                />
              </label>
              <button className="button-primary" type="submit">
                {copy.uploadVersion}
              </button>
            </form>
          ) : null}
        </section>
      </div>

      <section className="card overflow-hidden">
        <div className="border-b border-[var(--color-line)] p-6">
          <h2 className="text-lg font-semibold">{copy.versionHistory}</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            {copy.versionHelp}
          </p>
        </div>
        <div className="divide-y divide-[var(--color-line)]">
          {versions.map((version) => (
            <article key={version.id} className="p-6">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold">
                      v{version.version_number} · {version.original_filename}
                    </h3>
                    <span className="status-chip">{version.status}</span>
                    {version.id === document.current_version_id ? (
                      <span className="status-chip">{copy.current}</span>
                    ) : null}
                    {version.id === document.published_version_id ? (
                      <span className="status-chip">{copy.published}</span>
                    ) : null}
                    {version.id === document.active_version_id ? (
                      <span className="status-chip">{copy.active}</span>
                    ) : null}
                  </div>
                  <p className="mt-2 text-sm text-[var(--color-muted)]">
                    {copy.uploadedBy}: {shortId(version.created_by)} ·{" "}
                    {formatDate(version.created_at)} · {version.byte_size} bytes
                  </p>
                  <p className="mt-1 break-all font-mono text-xs text-[var(--color-muted)]">
                    SHA-256 {version.content_sha256}
                  </p>
                  <p className="mt-2 text-sm">
                    {copy.approval}: {version.review_status}
                    {version.reviewed_at
                      ? ` · ${formatDate(version.reviewed_at)}`
                      : ""}
                    {version.review_note ? ` · ${version.review_note}` : ""}
                  </p>
                  {version.restored_from_version_id ? (
                    <p className="mt-2 text-xs font-semibold text-[var(--color-brand)]">
                      {copy.restoredFrom}{" "}
                      {shortId(version.restored_from_version_id)}
                    </p>
                  ) : null}
                </div>
                {has(identity, "knowledge:restore") &&
                version.id !== document.current_version_id ? (
                  <form
                    action={rollbackKnowledgeVersion.bind(
                      null,
                      document.id,
                      version.id,
                      document.record_version,
                    )}
                    className="flex min-w-64 flex-col gap-2"
                  >
                    <input
                      className="field"
                      name="reason"
                      minLength={3}
                      placeholder={copy.rollbackReason}
                      required
                    />
                    <button className="button-tertiary" type="submit">
                      {copy.rollback}
                    </button>
                  </form>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="card p-6">
        <h2 className="text-lg font-semibold">{copy.agentBindings}</h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          {copy.bindingHelp}
        </p>
        <div className="mt-5 space-y-3">
          {(document.bindings ?? []).map((binding) => (
            <div
              key={binding.id}
              className="flex flex-col gap-3 rounded-xl border border-[var(--color-line)] p-4 lg:flex-row lg:items-center lg:justify-between"
            >
              <div>
                <p className="font-semibold">{binding.agent_key}</p>
                <p className="mt-1 text-sm text-[var(--color-muted)]">
                  {binding.status} · {formatDate(binding.updated_at)}
                </p>
              </div>
              {has(identity, "knowledge:edit") ? (
                <form
                  action={updateKnowledgeBinding.bind(
                    null,
                    document.id,
                    binding.id,
                    binding.status === "enabled" ? "disabled" : "enabled",
                  )}
                  className="flex gap-2"
                >
                  <input
                    className="field"
                    name="reason"
                    minLength={3}
                    placeholder={copy.bindingReason}
                    required
                  />
                  <button className="button-tertiary" type="submit">
                    {binding.status === "enabled" ? copy.disable : copy.enable}
                  </button>
                </form>
              ) : null}
            </div>
          ))}
          {!(document.bindings ?? []).length &&
          has(identity, "knowledge:edit") ? (
            <form
              action={bindKnowledgeDocument.bind(null, document.id)}
              className="flex flex-col gap-3 sm:flex-row"
            >
              <input
                type="hidden"
                name="agent_key"
                value={
                  document.domain_key === "commercial_kitchen"
                    ? "commercial_kitchen.lead_qualification"
                    : "laboratory_animal_facility.ivc_business_development"
                }
              />
              <button className="button-primary" type="submit">
                {copy.bindAgent}
              </button>
            </form>
          ) : null}
        </div>
      </section>

      <section className="card overflow-hidden">
        <div className="border-b border-[var(--color-line)] p-6">
          <h2 className="text-lg font-semibold">{copy.auditTimeline}</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            {copy.auditHelp}
          </p>
        </div>
        {canAudit ? (
          <div className="divide-y divide-[var(--color-line)]">
            {audit.map((event) => (
              <article
                key={event.id}
                className="grid gap-2 p-5 md:grid-cols-[180px_1fr]"
              >
                <div className="text-xs text-[var(--color-muted)]">
                  <p>{formatDate(event.created_at)}</p>
                  <p className="mt-1">{event.actor_display_name}</p>
                </div>
                <div>
                  <p className="font-semibold">
                    {event.action.replaceAll("_", " ")}
                  </p>
                  <p className="mt-1 text-sm text-[var(--color-muted)]">
                    {event.document_version_id
                      ? `${copy.versionReference}: ${shortId(event.document_version_id)}`
                      : copy.documentLevel}
                  </p>
                  {Object.keys(event.details).length ? (
                    <pre className="mt-3 overflow-x-auto rounded-lg bg-[var(--color-surface-muted)] p-3 text-xs">
                      {JSON.stringify(event.details, null, 2)}
                    </pre>
                  ) : null}
                </div>
              </article>
            ))}
            {!audit.length ? (
              <p className="p-6 text-sm text-[var(--color-muted)]">
                {copy.noAudit}
              </p>
            ) : null}
          </div>
        ) : (
          <p className="p-6 text-sm text-[var(--color-muted)]">
            {copy.auditRestricted}
          </p>
        )}
      </section>

      {current ? (
        <p className="text-xs text-[var(--color-muted)]">
          {copy.currentFingerprint}: {current.content_sha256}
        </p>
      ) : null}
    </div>
  );
}

function PointerCard({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <article
      className={`card p-5 ${accent ? "border-[var(--color-brand)]" : ""}`}
    >
      <p className="text-xs font-bold uppercase tracking-wider text-[var(--color-muted)]">
        {label}
      </p>
      <p className="mt-2 text-lg font-semibold">{value}</p>
    </article>
  );
}

function Field({
  label,
  name,
  value,
}: {
  label: string;
  name: string;
  value: string;
}) {
  return (
    <label className="label">
      {label}
      <input className="field mt-2" name={name} defaultValue={value} required />
    </label>
  );
}

function has(identity: CurrentIdentity, permission: string) {
  return identity.permissions.includes(permission);
}

function pointerLabel(
  pointer: string | null,
  versions: KnowledgeDocumentVersion[],
) {
  if (!pointer) return "—";
  const version = versions.find((item) => item.id === pointer);
  return version ? `v${version.version_number}` : shortId(pointer);
}

function shortId(value: string) {
  return value.slice(0, 8);
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function statusLabel(status: string, zh: boolean) {
  if (!zh) return status.replaceAll("_", " ");
  return (
    (
      {
        draft: "草稿",
        uploaded: "已上传",
        processing: "处理中",
        review: "待审核",
        approved: "已批准",
        published: "已发布",
        active: "已生效",
        archived: "已归档",
      } as Record<string, string>
    )[status] ?? status
  );
}

const english = {
  back: "Knowledge management",
  eyebrow: "Phase 2.5.3 · Governed document",
  lifecycle: "Lifecycle",
  currentVersion: "Current version",
  publishedVersion: "Published version",
  activeVersion: "Active version",
  governanceActions: "Governance actions",
  governanceHelp:
    "Approval, publication, activation and archival are separate governed decisions.",
  submit: "Submit for review",
  approve: "Approve",
  reject: "Reject",
  publish: "Publish",
  activate: "Activate",
  process: "Process",
  reprocess: "Reprocess",
  archive: "Archive",
  archiveReason: "Required archive reason",
  restore: "Restore for approval",
  restoreReason: "Required restore reason",
  metadata: "Document metadata",
  metadataHelp:
    "Changes use optimistic concurrency. Approved metadata changes invalidate approval.",
  title: "Title",
  documentType: "Document type",
  language: "Language",
  metadataJson: "Metadata JSON",
  saveMetadata: "Save metadata",
  newVersion: "Upload replacement version",
  newVersionHelp:
    "A replacement creates an immutable successor and keeps any previously active version available until activation changes.",
  file: "PDF, DOCX, text, or Markdown file",
  versionMetadata: "Version metadata JSON",
  uploadVersion: "Create new version",
  versionHistory: "Version and approval history",
  versionHelp:
    "Version numbers only move forward. Rollback creates a new version and requires fresh approval.",
  current: "Current",
  published: "Published",
  active: "Active",
  uploadedBy: "Uploader",
  approval: "Approval",
  restoredFrom: "Restored from version",
  rollbackReason: "Required rollback reason",
  rollback: "Create rollback version",
  agentBindings: "Agent bindings",
  bindingHelp:
    "Disabled bindings immediately remove agent eligibility without deleting history.",
  bindingReason: "Required binding reason",
  disable: "Disable",
  enable: "Enable",
  bindAgent: "Bind domain agent",
  auditTimeline: "Governance audit timeline",
  auditHelp:
    "A tenant-scoped append-only record of document, version, approval, publication and binding actions.",
  versionReference: "Version",
  documentLevel: "Document-level event",
  noAudit: "No governance events recorded.",
  auditRestricted: "Your role cannot read governance audit events.",
  currentFingerprint: "Current version SHA-256",
};

const chinese: typeof english = {
  back: "知识管理",
  eyebrow: "Phase 2.5.3 · 受治理文档",
  lifecycle: "生命周期",
  currentVersion: "当前版本",
  publishedVersion: "已发布版本",
  activeVersion: "已生效版本",
  governanceActions: "治理操作",
  governanceHelp: "审批、发布、启用和归档是相互独立的受控决定。",
  submit: "提交审核",
  approve: "批准",
  reject: "拒绝",
  publish: "发布",
  activate: "启用",
  process: "处理",
  reprocess: "重新处理",
  archive: "归档",
  archiveReason: "必须填写归档原因",
  restore: "恢复到待发布状态",
  restoreReason: "必须填写恢复原因",
  metadata: "文档元数据",
  metadataHelp: "修改使用乐观并发控制；已批准元数据改变后原审批会失效。",
  title: "标题",
  documentType: "文档类型",
  language: "语言",
  metadataJson: "元数据 JSON",
  saveMetadata: "保存元数据",
  newVersion: "上传替换版本",
  newVersionHelp:
    "替换会创建不可变后继版本；在新版本正式启用前，原生效版本仍保留。",
  file: "PDF、DOCX、文本或 Markdown 文件",
  versionMetadata: "版本元数据 JSON",
  uploadVersion: "创建新版本",
  versionHistory: "版本和审批历史",
  versionHelp: "版本号只会递增；回滚会创建新版本并重新审批。",
  current: "当前",
  published: "已发布",
  active: "已生效",
  uploadedBy: "上传人",
  approval: "审批",
  restoredFrom: "来源历史版本",
  rollbackReason: "必须填写回滚原因",
  rollback: "创建回滚版本",
  agentBindings: "智能体绑定",
  bindingHelp: "禁用绑定会立即取消智能体资格，但不会删除历史。",
  bindingReason: "必须填写绑定变更原因",
  disable: "禁用",
  enable: "启用",
  bindAgent: "绑定业务域智能体",
  auditTimeline: "治理审计时间线",
  auditHelp: "按租户隔离，记录文档、版本、审批、发布和绑定操作的追加式历史。",
  versionReference: "版本",
  documentLevel: "文档级事件",
  noAudit: "尚无治理事件。",
  auditRestricted: "当前角色不能查看治理审计事件。",
  currentFingerprint: "当前版本 SHA-256",
};
