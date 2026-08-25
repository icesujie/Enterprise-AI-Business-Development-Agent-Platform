import Link from "next/link";

import { StatusBadge } from "@/components/ui/status";
import { PageHeader } from "@/components/workspace/page-header";
import { getLocale } from "@/i18n/server";
import { apiFetch, type PublicContentItem } from "@/lib/api";

type Search = {
  status?: string;
  page_type?: string;
  locale?: string;
  search?: string;
};

export default async function PublicContentPage({
  searchParams,
}: PageProps<"/public-content">) {
  const filters = (await searchParams) as Search;
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(filters))
    if (value) query.set(key, value);
  const [items, locale] = await Promise.all([
    apiFetch<PublicContentItem[]>(`/api/v1/public-content/items?${query}`),
    getLocale(),
  ]);
  const zh = locale === "zh-CN";
  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow={zh ? "公开内容治理" : "Public content governance"}
        title={zh ? "公开内容" : "Public Content"}
        description={
          zh
            ? "管理解决方案、行业、案例与指南的不可变版本、审核和发布。"
            : "Govern immutable versions, review, approval, and publication for solutions, industries, case studies, guides, and products."
        }
        actions={
          <div className="flex flex-wrap gap-3">
            <Link className="button-tertiary" href="/public-content/imports">
              {zh ? "导入文档" : "Import document"}
            </Link>
            <Link className="button-primary" href="/public-content/new">
              {zh ? "创建页面草稿" : "Create page draft"}
            </Link>
          </div>
        }
      />
      <form
        className="card grid gap-3 p-4 sm:grid-cols-6"
        action="/public-content"
      >
        <input
          className="input sm:col-span-2"
          name="search"
          aria-label={zh ? "搜索公开内容" : "Search public content"}
          defaultValue={filters.search}
          placeholder={zh ? "搜索标题或路径" : "Search title or path"}
        />
        <select
          className="input"
          name="page_type"
          aria-label={zh ? "页面类型" : "Page type"}
          defaultValue={filters.page_type ?? ""}
        >
          <option value="">{zh ? "全部类型" : "All types"}</option>
          <option value="solution">Solution</option>
          <option value="industry">Industry</option>
          <option value="case_study">Case study</option>
          <option value="guide">Guide</option>
          <option value="product">Product</option>
        </select>
        <select
          className="input"
          name="status"
          aria-label={zh ? "生命周期状态" : "Lifecycle status"}
          defaultValue={filters.status ?? ""}
        >
          <option value="">{zh ? "全部状态" : "All statuses"}</option>
          {["draft", "review", "approved", "published", "archived"].map(
            (status) => (
              <option key={status}>{status}</option>
            ),
          )}
        </select>
        <select
          className="input"
          name="locale"
          aria-label={zh ? "语言" : "Locale"}
          defaultValue={filters.locale ?? ""}
        >
          <option value="">{zh ? "全部语言" : "All locales"}</option>
          <option value="en">English</option>
          <option value="zh-CN">中文</option>
        </select>
        <button className="button-tertiary" type="submit">
          {zh ? "筛选" : "Filter"}
        </button>
      </form>
      {items.length ? (
        <div className="card overflow-x-auto">
          <table className="w-full min-w-[780px] text-left text-sm">
            <thead className="border-b border-[var(--color-line)] bg-[#f7f8f5] text-xs uppercase tracking-wider text-[var(--color-muted)]">
              <tr>
                <th className="p-4">{zh ? "页面" : "Page"}</th>
                <th className="p-4">{zh ? "类型" : "Type"}</th>
                <th className="p-4">{zh ? "语言" : "Locale"}</th>
                <th className="p-4">{zh ? "状态" : "Status"}</th>
                <th className="p-4">{zh ? "版本" : "Version"}</th>
                <th className="p-4">{zh ? "更新时间" : "Updated"}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-line)]">
              {items.map((item) => (
                <tr key={item.id}>
                  <td className="p-4">
                    <Link
                      className="font-semibold text-[var(--color-brand)]"
                      href={`/public-content/${item.id}`}
                    >
                      {item.title}
                    </Link>
                    <p className="mt-1 font-mono text-xs text-[var(--color-muted)]">
                      {item.canonical_path}
                    </p>
                  </td>
                  <td className="p-4">{item.page_type}</td>
                  <td className="p-4">{item.locale}</td>
                  <td className="p-4">
                    <StatusBadge tone={tone(item.status)}>
                      {item.status}
                    </StatusBadge>
                    {item.is_synthetic ? (
                      <span className="ml-2 text-xs text-[var(--color-warning)]">
                        synthetic
                      </span>
                    ) : null}
                  </td>
                  <td className="p-4">
                    v{item.current_version?.version_number ?? "—"}
                  </td>
                  <td className="p-4">
                    {new Intl.DateTimeFormat(locale, {
                      dateStyle: "medium",
                    }).format(new Date(item.updated_at))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="card p-10 text-center text-sm text-[var(--color-muted)]">
          {zh
            ? "没有符合条件的公开内容。"
            : "No public content matches these filters."}
        </div>
      )}
    </div>
  );
}

function tone(
  status: string,
): "neutral" | "info" | "success" | "warning" | "danger" {
  return status === "published" || status === "approved"
    ? "success"
    : status === "review"
      ? "info"
      : status === "archived"
        ? "neutral"
        : "warning";
}
