import Link from "next/link";

import { uploadMedia } from "@/app/(workspace)/media/actions";
import { StatusBadge } from "@/components/ui/status";
import { PageHeader } from "@/components/workspace/page-header";
import { getLocale } from "@/i18n/server";
import { apiFetch, type MediaAsset } from "@/lib/api";

export default async function MediaPage({ searchParams }: PageProps<"/media">) {
  const filters = (await searchParams) as { status?: string; search?: string };
  const query = new URLSearchParams();
  if (filters.status) query.set("status", filters.status);
  if (filters.search) query.set("search", filters.search);
  const [assets, locale] = await Promise.all([
    apiFetch<MediaAsset[]>(`/api/v1/media/assets?${query}`),
    getLocale(),
  ]);
  const zh = locale === "zh-CN";
  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow={zh ? "公开媒体治理" : "Public media governance"}
        title={zh ? "媒体库" : "Media Library"}
        description={
          zh
            ? "上传、审核并管理公开网站图片。"
            : "Upload, review, and govern images used by public website content."
        }
      />
      <form action={uploadMedia} className="card grid gap-4 p-6 lg:grid-cols-2">
        <h2 className="text-lg font-semibold lg:col-span-2">
          {zh ? "上传图片" : "Upload image"}
        </h2>
        <input
          aria-label={zh ? "上传图片" : "Upload image"}
          className="input"
          name="file"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          required
        />
        <input
          className="input"
          name="title"
          placeholder={zh ? "图片标题" : "Image title"}
          required
        />
        <input
          className="input"
          name="alt_text"
          placeholder={zh ? "替代文本" : "Accessible alt text"}
          required
        />
        <input
          className="input"
          name="caption"
          placeholder={zh ? "说明（可选）" : "Caption (optional)"}
        />
        <button className="button-primary w-fit" type="submit">
          {zh ? "上传为私有" : "Upload as private"}
        </button>
      </form>
      <form className="card flex flex-wrap gap-3 p-4" action="/media">
        <input
          className="input min-w-60 flex-1"
          name="search"
          defaultValue={filters.search}
          placeholder={zh ? "搜索媒体" : "Search media"}
        />
        <select
          className="input"
          name="status"
          defaultValue={filters.status ?? ""}
        >
          <option value="">{zh ? "全部状态" : "All statuses"}</option>
          {["uploaded", "review", "approved", "revoked", "archived"].map(
            (status) => (
              <option key={status}>{status}</option>
            ),
          )}
        </select>
        <button className="button-tertiary" type="submit">
          {zh ? "筛选" : "Filter"}
        </button>
      </form>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {assets.map((asset) => (
          <Link
            className="card block p-5"
            href={`/media/${asset.id}`}
            key={asset.id}
          >
            <div className="flex items-start justify-between gap-3">
              <h2 className="font-semibold">{asset.title}</h2>
              <StatusBadge
                tone={
                  asset.public_use_status === "approved"
                    ? "success"
                    : asset.public_use_status === "review"
                      ? "info"
                      : "neutral"
                }
              >
                {asset.public_use_status}
              </StatusBadge>
            </div>
            <p className="mt-3 text-sm text-[var(--color-muted)]">
              {asset.original_filename}
            </p>
            <p className="mt-2 text-xs text-[var(--color-muted)]">
              {asset.width} × {asset.height} · {asset.mime_type}
            </p>
          </Link>
        ))}
        {!assets.length ? (
          <div className="card p-8 text-sm text-[var(--color-muted)]">
            {zh ? "没有媒体资产。" : "No media assets."}
          </div>
        ) : null}
      </div>
    </div>
  );
}
