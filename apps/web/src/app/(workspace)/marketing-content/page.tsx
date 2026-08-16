import Link from "next/link";

import { PageHeader } from "@/components/workspace/page-header";
import { StatusBadge } from "@/components/ui/status";
import { getLocale } from "@/i18n/server";
import {
  apiFetch,
  type MarketingContentAsset,
  type MarketingContentRequest,
} from "@/lib/api";

const lifecycleTabs = [
  "draft",
  "generated",
  "review",
  "approved",
  "archived",
] as const;

export default async function MarketingContentPage({
  searchParams,
}: PageProps<"/marketing-content">) {
  const query = await searchParams;
  const zh = (await getLocale()) === "zh-CN";
  const copy = zh ? chinese : english;
  const view = single(query.view) || "draft";
  const contentType = single(query.content_type);
  const language = single(query.language);
  const search = single(query.search);
  const params = new URLSearchParams();
  if (view !== "requests") params.set("status", view);
  if (contentType) params.set("content_type", contentType);
  if (language) params.set("language", language);
  if (search) params.set("search", search);
  const [assets, requests] = await Promise.all([
    view === "requests"
      ? Promise.resolve([])
      : apiFetch<MarketingContentAsset[]>(`/api/v1/content/assets?${params}`),
    view === "requests"
      ? apiFetch<MarketingContentRequest[]>(
          `/api/v1/content/requests?${params}`,
        )
      : Promise.resolve([]),
  ]);

  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow={copy.eyebrow}
        title={copy.title}
        description={copy.description}
        actions={
          <div className="flex flex-wrap gap-3">
            <Link className="button-tertiary" href="/marketing-content/acceptance">
              {zh ? "业务验收" : "Business acceptance"}
            </Link>
            <Link className="button-primary" href="/marketing-content/new">
              {copy.newDraft}
            </Link>
          </div>
        }
      />

      <section className="card p-2">
        <nav
          className="flex gap-2 overflow-x-auto"
          aria-label={copy.lifecycleNavigation}
        >
          <Tab
            href="/marketing-content?view=requests"
            active={view === "requests"}
          >
            {copy.requests}
          </Tab>
          {lifecycleTabs.map((status) => (
            <Tab
              key={status}
              href={`/marketing-content?view=${status}`}
              active={view === status}
            >
              {statusLabel(status, zh)}
            </Tab>
          ))}
        </nav>
      </section>

      <form
        className="card grid gap-4 p-5 md:grid-cols-4"
        action="/marketing-content"
      >
        <input type="hidden" name="view" value={view} />
        <label className="label">
          {copy.search}
          <input className="field mt-2" name="search" defaultValue={search} />
        </label>
        <label className="label">
          {copy.type}
          <select
            className="field mt-2"
            name="content_type"
            defaultValue={contentType}
          >
            <option value="">{copy.allTypes}</option>
            {contentTypeOptions(zh).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label className="label">
          {copy.language}
          <select
            className="field mt-2"
            name="language"
            defaultValue={language}
          >
            <option value="">{copy.allLanguages}</option>
            <option value="en">English</option>
            <option value="zh-CN">中文</option>
          </select>
        </label>
        <button className="button-tertiary self-end" type="submit">
          {copy.apply}
        </button>
      </form>

      {view === "requests" ? (
        <RequestList requests={requests} zh={zh} />
      ) : (
        <AssetList assets={assets} zh={zh} />
      )}
    </div>
  );
}

function AssetList({
  assets,
  zh,
}: {
  assets: MarketingContentAsset[];
  zh: boolean;
}) {
  if (!assets.length) {
    return <EmptyState zh={zh} requests={false} />;
  }
  return (
    <section className="card overflow-hidden">
      <div className="hidden grid-cols-[minmax(220px,2fr)_1fr_1fr_1fr_150px] gap-4 border-b border-[var(--color-line)] px-5 py-3 text-xs font-bold uppercase tracking-wider text-[var(--color-muted)] lg:grid">
        <span>{zh ? "内容" : "Content"}</span>
        <span>{zh ? "状态" : "Status"}</span>
        <span>{zh ? "当前版本" : "Current"}</span>
        <span>{zh ? "批准版本" : "Approved"}</span>
        <span>{zh ? "更新时间" : "Updated"}</span>
      </div>
      <div className="divide-y divide-[var(--color-line)]">
        {assets.map((asset) => (
          <article
            key={asset.id}
            className="grid gap-3 p-5 lg:grid-cols-[minmax(220px,2fr)_1fr_1fr_1fr_150px] lg:items-center lg:gap-4"
          >
            <div>
              <Link
                href={`/marketing-content/${asset.id}`}
                className="font-semibold hover:text-[var(--color-brand)]"
              >
                {asset.title}
              </Link>
              <p className="mt-1 text-xs text-[var(--color-muted)]">
                {typeLabel(asset.content_type, zh)} · {asset.language} ·{" "}
                {asset.channel}
              </p>
              <p className="mt-1 text-xs text-[var(--color-muted)]">
                {zh ? "创建者" : "Creator"}:{" "}
                {shortId(asset.creator_membership_id)}
              </p>
            </div>
            <StatusBadge tone={statusTone(asset.status)}>
              {statusLabel(asset.status, zh)}
            </StatusBadge>
            <Pointer
              label={zh ? "当前" : "Current"}
              version={asset.current_version?.version_number}
              status={asset.status}
              zh={zh}
            />
            <Pointer
              label={zh ? "已批准" : "Approved"}
              version={asset.approved_version?.version_number}
              status={asset.approved_version ? "approved" : undefined}
              zh={zh}
            />
            <time
              className="text-sm text-[var(--color-muted)]"
              dateTime={asset.updated_at}
            >
              {formatDate(asset.updated_at, zh)}
            </time>
          </article>
        ))}
      </div>
    </section>
  );
}

function RequestList({
  requests,
  zh,
}: {
  requests: MarketingContentRequest[];
  zh: boolean;
}) {
  if (!requests.length) return <EmptyState zh={zh} requests />;
  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {requests.map((request) => (
        <article className="card p-5" key={request.id}>
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-[var(--color-brand)]">
                {typeLabel(request.content_type, zh)}
              </p>
              <h2 className="mt-2 font-semibold">{request.topic}</h2>
            </div>
            <StatusBadge
              tone={request.status === "completed" ? "success" : "neutral"}
            >
              {request.status}
            </StatusBadge>
          </div>
          <p className="mt-3 line-clamp-3 text-sm leading-6 text-[var(--color-muted)]">
            {request.business_objective}
          </p>
          <div className="mt-4 flex items-center justify-between text-xs text-[var(--color-muted)]">
            <span>
              {request.language} · {request.channel}
            </span>
            {request.result_asset_id ? (
              <Link
                className="font-semibold text-[var(--color-brand)]"
                href={`/marketing-content/${request.result_asset_id}`}
              >
                {zh ? "查看内容 →" : "View content →"}
              </Link>
            ) : null}
          </div>
        </article>
      ))}
    </section>
  );
}

function Pointer({
  label,
  version,
  status,
  zh,
}: {
  label: string;
  version?: number;
  status?: string;
  zh: boolean;
}) {
  return (
    <div className="text-sm">
      <span className="mr-2 text-xs text-[var(--color-muted)] lg:hidden">
        {label}:
      </span>
      {version ? `v${version} · ${statusLabel(status ?? "draft", zh)}` : "—"}
    </div>
  );
}

function EmptyState({ zh, requests }: { zh: boolean; requests: boolean }) {
  return (
    <section className="card p-10 text-center">
      <h2 className="text-lg font-semibold">
        {requests
          ? zh
            ? "暂无内容请求"
            : "No content requests"
          : zh
            ? "当前筛选条件下没有内容"
            : "No content matches these filters"}
      </h2>
      <p className="mt-2 text-sm text-[var(--color-muted)]">
        {zh
          ? "创建 AI 或人工草稿来启动受治理流程。"
          : "Create an AI or manual draft to start the governed workflow."}
      </p>
    </section>
  );
}

function Tab({
  href,
  active,
  children,
}: {
  href: string;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={`shrink-0 rounded-lg px-4 py-2 text-sm font-semibold ${active ? "bg-[var(--color-brand-strong)] text-white" : "text-[var(--color-muted)] hover:bg-[var(--color-surface-subtle)]"}`}
    >
      {children}
    </Link>
  );
}

function single(value: string | string[] | undefined): string {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
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
  return contentTypeOptions(zh).find(([value]) => value === type)?.[1] ?? type;
}

function contentTypeOptions(zh: boolean): string[][] {
  return [
    ["website_article", zh ? "网站文章" : "Website article"],
    ["tiktok_script", "TikTok script"],
    ["instagram_reel_script", "Instagram Reel script"],
    ["facebook_post", "Facebook post"],
    ["email_draft", zh ? "邮件草稿" : "Email draft"],
  ];
}

function formatDate(value: string, zh: boolean): string {
  return new Intl.DateTimeFormat(zh ? "zh-CN" : "en", {
    dateStyle: "medium",
  }).format(new Date(value));
}

function shortId(value: string): string {
  return `${value.slice(0, 8)}…`;
}

const english = {
  eyebrow: "Human-operated content governance",
  title: "Marketing Content",
  description:
    "Generate grounded B2B drafts from approved public knowledge, then review, approve, version, and archive them. No publishing or external sending is available.",
  newDraft: "New content",
  requests: "Requests",
  lifecycleNavigation: "Content lifecycle",
  search: "Search",
  type: "Content type",
  allTypes: "All types",
  language: "Language",
  allLanguages: "All languages",
  apply: "Apply filters",
};

const chinese = {
  eyebrow: "人工操作的内容治理",
  title: "营销内容",
  description:
    "根据已批准公开知识生成 B2B 草稿，然后进行审核、批准、版本化和归档。本工作台不提供发布或外部发送。",
  newDraft: "新建内容",
  requests: "内容请求",
  lifecycleNavigation: "内容生命周期",
  search: "搜索",
  type: "内容类型",
  allTypes: "全部类型",
  language: "语言",
  allLanguages: "全部语言",
  apply: "应用筛选",
};
