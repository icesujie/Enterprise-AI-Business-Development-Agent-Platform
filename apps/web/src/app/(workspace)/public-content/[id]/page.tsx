import Link from "next/link";

import { PublicContentDetailActions } from "@/components/public-content/public-content-forms";
import { StatusBadge } from "@/components/ui/status";
import { PageHeader } from "@/components/workspace/page-header";
import { getLocale } from "@/i18n/server";
import {
  apiFetch,
  type CurrentIdentity,
  type PublicContentAuditLog,
  type PublicContentDecision,
  type PublicContentItem,
  type PublicContentVersion,
} from "@/lib/api";

export default async function PublicContentDetailPage({
  params,
}: PageProps<"/public-content/[id]">) {
  const { id } = await params;
  const [item, versions, identity, locale] = await Promise.all([
    apiFetch<PublicContentItem>(`/api/v1/public-content/items/${id}`),
    apiFetch<PublicContentVersion[]>(
      `/api/v1/public-content/items/${id}/versions`,
    ),
    apiFetch<CurrentIdentity>("/api/v1/me"),
    getLocale(),
  ]);
  const zh = locale === "zh-CN";
  const canAudit = identity.permissions.includes("public_content:audit_read");
  const [decisions, audit] = canAudit
    ? await Promise.all([
        apiFetch<PublicContentDecision[]>(
          `/api/v1/public-content/items/${id}/decisions`,
        ),
        apiFetch<PublicContentAuditLog[]>(
          `/api/v1/public-content/items/${id}/audit`,
        ),
      ])
    : [[], []];
  return (
    <div className="space-y-7">
      <Link
        className="text-sm font-semibold text-[var(--color-brand)]"
        href="/public-content"
      >
        ← {zh ? "返回公开内容" : "Back to Public Content"}
      </Link>
      <PageHeader
        eyebrow={`${item.page_type} · ${item.locale}`}
        title={item.title}
        description={
          zh
            ? "发布只针对已批准的准确版本；历史版本永不覆盖。"
            : "Publishing targets one exact approved version; historical versions are never overwritten."
        }
      />
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <Pointer label={zh ? "状态" : "Status"}>
          <StatusBadge
            tone={
              item.status === "published" || item.status === "approved"
                ? "success"
                : item.status === "review"
                  ? "info"
                  : "warning"
            }
          >
            {item.status}
          </StatusBadge>
        </Pointer>
        <Pointer label={zh ? "当前" : "Current"}>
          v{item.current_version?.version_number ?? "—"}
        </Pointer>
        <Pointer label={zh ? "批准" : "Approved"}>
          {pointer(item.approved_version)}
        </Pointer>
        <Pointer label={zh ? "发布" : "Published"}>
          {pointer(item.published_version)}
        </Pointer>
        <Pointer label="ETag">{item.record_version}</Pointer>
      </section>
      {item.is_synthetic ? (
        <aside className="rounded-xl border border-[var(--color-warning)]/30 bg-[var(--color-warning-soft)] p-4 text-sm text-[var(--color-warning)]">
          {zh
            ? "合成内容：系统禁止发布。"
            : "Synthetic content: publishing is blocked."}
        </aside>
      ) : null}
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(340px,0.8fr)]">
        <div className="space-y-6">
          <section className="card p-6">
            <h2 className="text-lg font-semibold">
              {zh ? "当前结构化内容" : "Current structured content"}
            </h2>
            <p className="mt-2 text-sm text-[var(--color-muted)]">
              {item.summary}
            </p>
            <pre className="mt-5 max-h-[38rem] overflow-auto rounded-xl bg-[#152b22] p-5 text-xs leading-5 text-white/85">
              {JSON.stringify(
                item.current_version?.structured_content ?? {},
                null,
                2,
              )}
            </pre>
          </section>
          <History title={zh ? "版本历史" : "Version history"}>
            {versions.map((version) => (
              <article
                key={version.id}
                className="border-t border-[var(--color-line)] p-5"
              >
                <strong>v{version.version_number}</strong>
                {version.id === item.current_version_id ? " · current" : ""}
                {version.id === item.approved_version_id ? " · approved" : ""}
                {version.id === item.published_version_id ? " · published" : ""}
                <p className="mt-1 text-xs text-[var(--color-muted)]">
                  {version.origin} · {format(version.created_at, locale)}
                </p>
                {version.source_structuring_run_id &&
                version.source_reference_id ? (
                  <Link
                    className="mt-2 inline-block text-xs font-semibold text-[var(--color-brand)]"
                    href={`/public-content/imports/${version.source_reference_id}`}
                  >
                    {zh ? "查看导入依据" : "View import evidence"}
                    {version.source_candidate_key
                      ? ` · ${version.source_candidate_key}`
                      : ""}
                  </Link>
                ) : null}
                <p className="mt-1 break-all font-mono text-[0.65rem] text-[var(--color-muted)]">
                  {version.content_sha256}
                </p>
              </article>
            ))}
          </History>
          {canAudit ? (
            <History title={zh ? "审批历史" : "Review history"}>
              {decisions.map((decision) => (
                <article
                  key={decision.id}
                  className="border-t border-[var(--color-line)] p-5"
                >
                  <strong>{decision.decision_type}</strong>
                  <p className="mt-1 text-sm text-[var(--color-muted)]">
                    {decision.comment || "—"} ·{" "}
                    {format(decision.created_at, locale)}
                  </p>
                </article>
              ))}
            </History>
          ) : null}
          {canAudit ? (
            <History title={zh ? "审计记录" : "Audit timeline"}>
              {audit.map((event) => (
                <article
                  key={event.id}
                  className="border-t border-[var(--color-line)] p-5"
                >
                  <strong>{event.action}</strong>
                  <p className="mt-1 text-xs text-[var(--color-muted)]">
                    {format(event.created_at, locale)} ·{" "}
                    {event.correlation_id ?? "—"}
                  </p>
                </article>
              ))}
            </History>
          ) : null}
        </div>
        <PublicContentDetailActions item={item} identity={identity} zh={zh} />
      </div>
    </div>
  );
}

function Pointer({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="card p-5">
      <p className="text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">
        {label}
      </p>
      <div className="mt-3 font-semibold">{children}</div>
    </div>
  );
}
function History({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="card overflow-hidden">
      <h2 className="p-5 text-lg font-semibold">{title}</h2>
      {children}
    </section>
  );
}
function pointer(version: PublicContentVersion | null) {
  return version ? `v${version.version_number}` : "—";
}
function format(value: string, locale: string) {
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
