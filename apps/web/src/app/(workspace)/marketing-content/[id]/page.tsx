import Link from "next/link";

import {
  ContentFeedbackForm,
  ContentDetailActions,
  RollbackVersionButton,
} from "@/components/marketing/marketing-content-forms";
import { MarketingChannelPreview } from "@/components/marketing/marketing-channel-preview";
import { MarketingEvaluationPanel } from "@/components/marketing/marketing-evaluation-panel";
import { StatusBadge } from "@/components/ui/status";
import { PageHeader } from "@/components/workspace/page-header";
import { getLocale } from "@/i18n/server";
import {
  apiFetch,
  type CurrentIdentity,
  type MarketingContentAsset,
  type MarketingContentAuditLog,
  type MarketingContentDecision,
  type MarketingContentEvaluation,
  type MarketingContentVersion,
} from "@/lib/api";

export default async function MarketingContentDetailPage({
  params,
}: PageProps<"/marketing-content/[id]">) {
  const { id } = await params;
  const [asset, versions, identity, locale, evaluation] = await Promise.all([
    apiFetch<MarketingContentAsset>(`/api/v1/content/assets/${id}`),
    apiFetch<MarketingContentVersion[]>(
      `/api/v1/content/assets/${id}/versions`,
    ),
    apiFetch<CurrentIdentity>("/api/v1/me"),
    getLocale(),
    apiFetch<MarketingContentEvaluation>(
      `/api/v1/content/assets/${id}/evaluation`,
    ),
  ]);
  const zh = locale === "zh-CN";
  const canAudit = identity.permissions.includes("content:audit_read");
  const [decisions, audit] = canAudit
    ? await Promise.all([
        apiFetch<MarketingContentDecision[]>(
          `/api/v1/content/assets/${id}/decisions`,
        ),
        apiFetch<MarketingContentAuditLog[]>(
          `/api/v1/content/assets/${id}/audit`,
        ),
      ])
    : [[], []];
  const current = asset.current_version;
  const approved = asset.approved_version;

  return (
    <div className="space-y-7">
      <Link
        className="text-sm font-semibold text-[var(--color-brand)]"
        href="/marketing-content"
      >
        ← {zh ? "返回营销内容" : "Back to Marketing Content"}
      </Link>
      <PageHeader
        eyebrow={`${typeLabel(asset.content_type, zh)} · ${asset.language}`}
        title={asset.title}
        description={
          zh
            ? "人工内容治理记录。所有编辑、审批和回滚都保留不可变历史。"
            : "Human-operated governance record. Edits, decisions, and rollbacks preserve immutable history."
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <PointerCard label={zh ? "生命周期" : "Lifecycle"}>
          <StatusBadge tone={statusTone(asset.status)}>
            {statusLabel(asset.status, zh)}
          </StatusBadge>
        </PointerCard>
        <PointerCard label={zh ? "当前版本" : "Current version"}>
          <strong>v{current?.version_number ?? "—"}</strong>
          <span className="ml-2 text-sm text-[var(--color-muted)]">
            {statusLabel(asset.status, zh)}
          </span>
        </PointerCard>
        <PointerCard label={zh ? "批准版本" : "Approved version"}>
          {approved ? (
            <>
              <strong>v{approved.version_number}</strong>
              <span className="ml-2 text-sm text-[var(--color-success)]">
                {zh ? "已批准" : "Approved"}
              </span>
            </>
          ) : (
            "—"
          )}
        </PointerCard>
        <PointerCard label={zh ? "记录版本" : "Record version"}>
          <strong>{asset.record_version}</strong>
          <span className="ml-2 text-xs text-[var(--color-muted)]">ETag</span>
        </PointerCard>
      </section>

      {approved && current && approved.id !== current.id ? (
        <aside className="rounded-xl border border-[var(--color-warning)]/25 bg-[var(--color-warning-soft)] p-4 text-sm text-[var(--color-warning)]">
          {zh
            ? `当前 v${current.version_number} 尚未获批；最近批准版本仍为 v${approved.version_number}。`
            : `Current v${current.version_number} is not approved; the latest approved version remains v${approved.version_number}.`}
        </aside>
      ) : null}

      <section className="card grid gap-5 p-6 sm:grid-cols-2 xl:grid-cols-6">
        <Metadata label={zh ? "目标受众" : "Audience"} value={asset.audience} />
        <Metadata label={zh ? "渠道" : "Channel"} value={asset.channel} />
        <Metadata
          label={zh ? "创建者" : "Creator"}
          value={shortId(asset.creator_membership_id)}
        />
        <Metadata
          label={zh ? "负责人" : "Owner"}
          value={shortId(asset.owner_membership_id)}
        />
        <Metadata
          label={zh ? "创建时间" : "Created"}
          value={formatDate(asset.created_at, zh)}
        />
        <Metadata
          label={zh ? "更新时间" : "Updated"}
          value={formatDate(asset.updated_at, zh)}
        />
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(320px,0.7fr)]">
        <div className="space-y-6">
          {current ? (
            <>
              <MarketingChannelPreview contentType={asset.content_type} version={current} zh={zh} />
              <p className="break-all px-1 font-mono text-[0.68rem] text-[var(--color-muted)]">
                SHA-256: {current.content_sha256}
              </p>
            </>
          ) : null}

          <MarketingEvaluationPanel evaluation={evaluation} zh={zh} />

          <VersionHistory
            asset={asset}
            versions={versions}
            canRollback={identity.permissions.includes("content:edit")}
            zh={zh}
          />

          {canAudit ? <DecisionHistory decisions={decisions} zh={zh} /> : null}
          {canAudit ? <AuditTimeline audit={audit} zh={zh} /> : null}
        </div>

        <div className="space-y-6">
          <ContentFeedbackForm
            asset={asset}
            identity={identity}
            zh={zh}
            idempotencyKey={`feedback-${crypto.randomUUID()}`}
          />
          <ContentDetailActions
            asset={asset}
            identity={identity}
            zh={zh}
            keys={{
              edit: `edit-${crypto.randomUUID()}`,
              submit: `submit-${crypto.randomUUID()}`,
              approve: `approve-${crypto.randomUUID()}`,
              reject: `reject-${crypto.randomUUID()}`,
              archive: `lifecycle-${crypto.randomUUID()}`,
            }}
          />
        </div>
      </div>
    </div>
  );
}

function VersionHistory({
  asset,
  versions,
  canRollback,
  zh,
}: {
  asset: MarketingContentAsset;
  versions: MarketingContentVersion[];
  canRollback: boolean;
  zh: boolean;
}) {
  return (
    <section className="card overflow-hidden">
      <div className="border-b border-[var(--color-line)] p-5">
        <h2 className="text-lg font-semibold">
          {zh ? "版本历史" : "Version history"}
        </h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          {zh
            ? "历史版本不可修改或删除。"
            : "Historical versions cannot be edited or deleted."}
        </p>
      </div>
      <div className="divide-y divide-[var(--color-line)]">
        {versions.map((version) => {
          const current = version.id === asset.current_version_id;
          const approved = version.id === asset.approved_version_id;
          return (
            <article key={version.id} className="p-5">
              <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <strong>v{version.version_number}</strong>
                    {current ? (
                      <StatusBadge tone="info">
                        {zh ? "当前" : "Current"}
                      </StatusBadge>
                    ) : null}
                    {approved ? (
                      <StatusBadge tone="success">
                        {zh ? "已批准" : "Approved"}
                      </StatusBadge>
                    ) : null}
                    <span className="text-xs text-[var(--color-muted)]">
                      {version.origin}
                    </span>
                  </div>
                  <p className="mt-2 text-xs text-[var(--color-muted)]">
                    {zh ? "作者" : "Author"}: {shortId(version.created_by)} ·{" "}
                    {formatDate(version.created_at, zh)}
                  </p>
                  <p className="mt-1 font-mono text-[0.65rem] text-[var(--color-muted)]">
                    {version.content_sha256.slice(0, 18)}…
                  </p>
                </div>
                {canRollback && !current && asset.status !== "archived" ? (
                  <RollbackVersionButton
                    asset={asset}
                    version={version}
                    zh={zh}
                    idempotencyKey={`rollback-${crypto.randomUUID()}`}
                  />
                ) : null}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function DecisionHistory({
  decisions,
  zh,
}: {
  decisions: MarketingContentDecision[];
  zh: boolean;
}) {
  return (
    <section className="card p-6">
      <h2 className="text-lg font-semibold">
        {zh ? "审批历史" : "Approval history"}
      </h2>
      <div className="mt-5 space-y-4">
        {decisions.map((decision) => (
          <div
            key={decision.id}
            className="border-l-2 border-[var(--color-line)] pl-4"
          >
            <p className="text-sm font-semibold">
              {decisionLabel(decision.decision_type, zh)}
            </p>
            <p className="mt-1 text-xs text-[var(--color-muted)]">
              {shortId(decision.decided_by)} ·{" "}
              {formatDate(decision.created_at, zh)}
            </p>
            {decision.comment ? (
              <p className="mt-2 text-sm">{decision.comment}</p>
            ) : null}
          </div>
        ))}
        {!decisions.length ? (
          <p className="text-sm text-[var(--color-muted)]">
            {zh ? "暂无审批记录" : "No review decisions yet."}
          </p>
        ) : null}
      </div>
    </section>
  );
}

function AuditTimeline({
  audit,
  zh,
}: {
  audit: MarketingContentAuditLog[];
  zh: boolean;
}) {
  return (
    <section className="card p-6">
      <h2 className="text-lg font-semibold">
        {zh ? "治理审计" : "Governance audit"}
      </h2>
      <p className="mt-1 text-sm text-[var(--color-muted)]">
        {zh
          ? "仅管理员可见；记录仅可追加。"
          : "Admin only; records are append-only."}
      </p>
      <div className="mt-5 space-y-3">
        {audit.map((entry) => (
          <div
            key={entry.id}
            className="flex flex-col justify-between gap-1 border-b border-[var(--color-line)] pb-3 sm:flex-row"
          >
            <div>
              <p className="text-sm font-semibold">
                {auditLabel(entry.action, zh)}
              </p>
              <p className="mt-1 text-xs text-[var(--color-muted)]">
                {shortId(entry.actor_membership_id)} · {entry.target_type}
              </p>
            </div>
            <time
              className="text-xs text-[var(--color-muted)]"
              dateTime={entry.created_at}
            >
              {formatDate(entry.created_at, zh)}
            </time>
          </div>
        ))}
      </div>
    </section>
  );
}

function PointerCard({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <article className="card p-5">
      <p className="text-xs font-bold uppercase tracking-wider text-[var(--color-muted)]">
        {label}
      </p>
      <div className="mt-3">{children}</div>
    </article>
  );
}

function Metadata({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-bold uppercase tracking-wider text-[var(--color-muted)]">
        {label}
      </p>
      <p className="mt-2 text-sm font-semibold">{value}</p>
    </div>
  );
}

function statusLabel(status: string, zh: boolean): string {
  const labels: Record<string, [string, string]> = {
    draft: ["Draft", "草稿"],
    generated: ["Generated", "已生成"],
    review: ["In Review", "审核中"],
    approved: ["Approved", "已批准"],
    archived: ["Archived", "已归档"],
  };
  return labels[status]?.[zh ? 1 : 0] ?? status;
}

function statusTone(
  status: string,
): "neutral" | "info" | "success" | "warning" {
  if (status === "approved") return "success";
  if (status === "review") return "warning";
  if (status === "draft" || status === "generated") return "info";
  return "neutral";
}

function typeLabel(type: string, zh: boolean): string {
  const labels: Record<string, [string, string]> = {
    website_article: ["Website article", "网站文章"],
    tiktok_script: ["TikTok script", "TikTok 脚本"],
    instagram_reel_script: ["Instagram Reel script", "Instagram Reel 脚本"],
    facebook_post: ["Facebook post", "Facebook 帖子"],
    email_draft: ["Email draft", "邮件草稿"],
  };
  return labels[type]?.[zh ? 1 : 0] ?? type;
}

function decisionLabel(value: string, zh: boolean): string {
  const labels: Record<string, [string, string]> = {
    submitted: ["Submitted for review", "已提交审核"],
    approved: ["Approved", "已批准"],
    rejected: ["Rejected", "已拒绝"],
    changes_requested: ["Changes requested", "要求修改"],
  };
  return labels[value]?.[zh ? 1 : 0] ?? value;
}

function auditLabel(value: string, zh: boolean): string {
  if (!zh) return value.replaceAll(".", " · ").replaceAll("_", " ");
  const labels: Record<string, string> = {
    "content.asset_created": "创建内容资产",
    "content.version_created": "创建版本",
    "content.edited": "编辑并创建后继版本",
    "content.review_submitted": "提交审核",
    "content.approved": "批准版本",
    "content.rejected": "拒绝版本",
    "content.changes_requested": "要求修改",
    "content.archived": "归档内容",
    "content.restored": "恢复内容",
    "content.rollback": "回滚为新版本",
  };
  return labels[value] ?? value;
}

function shortId(value: string): string {
  return `${value.slice(0, 8)}…`;
}

function formatDate(value: string, zh: boolean): string {
  return new Intl.DateTimeFormat(zh ? "zh-CN" : "en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
