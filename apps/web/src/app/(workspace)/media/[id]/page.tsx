import Link from "next/link";
import Image from "next/image";

import {
  governMedia,
  updateMediaMetadata,
} from "@/app/(workspace)/media/actions";
import { StatusBadge } from "@/components/ui/status";
import { getLocale } from "@/i18n/server";
import {
  apiFetch,
  type CurrentIdentity,
  type MediaAsset,
  type MediaAuditLog,
} from "@/lib/api";

export default async function MediaDetailPage({
  params,
}: PageProps<"/media/[id]">) {
  const { id } = await params;
  const [asset, identity, locale] = await Promise.all([
    apiFetch<MediaAsset>(`/api/v1/media/assets/${id}`),
    apiFetch<CurrentIdentity>("/api/v1/me"),
    getLocale(),
  ]);
  const can = (permission: string) => identity.permissions.includes(permission);
  const audit = can("media:audit_read")
    ? await apiFetch<MediaAuditLog[]>(`/api/v1/media/assets/${id}/audit`)
    : [];
  const zh = locale === "zh-CN";
  return (
    <div className="mx-auto max-w-5xl space-y-7">
      <Link
        className="text-sm font-semibold text-[var(--color-brand)]"
        href="/media"
      >
        ← {zh ? "返回媒体库" : "Back to Media Library"}
      </Link>
      <section className="card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="eyebrow">{asset.original_filename}</p>
            <h1 className="section-title mt-3">{asset.title}</h1>
          </div>
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
        {asset.public_use_status === "approved" ? (
          <Image
            className="mt-6 max-h-[28rem] w-auto rounded-xl object-contain"
            src={`/public-media/${asset.id}`}
            alt={asset.alt_text}
            width={asset.width}
            height={asset.height}
          />
        ) : (
          <div className="mt-6 rounded-xl bg-[var(--color-surface-subtle)] p-8 text-sm text-[var(--color-muted)]">
            {zh
              ? "私有媒体不会通过公开地址显示。"
              : "Private media is not rendered through the public URL."}
          </div>
        )}
        <dl className="mt-6 grid gap-4 text-sm sm:grid-cols-3">
          <div>
            <dt className="text-[var(--color-muted)]">ID</dt>
            <dd className="mt-1 break-all font-mono text-xs">{asset.id}</dd>
          </div>
          <div>
            <dt className="text-[var(--color-muted)]">Dimensions</dt>
            <dd>
              {asset.width} × {asset.height}
            </dd>
          </div>
          <div>
            <dt className="text-[var(--color-muted)]">Size</dt>
            <dd>{Math.ceil(asset.file_size / 1024)} KB</dd>
          </div>
        </dl>
      </section>
      {can("media:edit") && asset.public_use_status !== "archived" ? (
        <form
          className="card grid gap-4 p-6"
          action={updateMediaMetadata.bind(
            null,
            asset.id,
            asset.record_version,
          )}
        >
          <h2 className="text-lg font-semibold">
            {zh ? "编辑元数据" : "Edit metadata"}
          </h2>
          <input
            className="input"
            name="title"
            defaultValue={asset.title}
            required
          />
          <textarea
            className="input min-h-24"
            name="alt_text"
            defaultValue={asset.alt_text}
            required
          />
          <textarea
            className="input min-h-24"
            name="caption"
            defaultValue={asset.caption ?? ""}
          />
          <button className="button-secondary w-fit" type="submit">
            {zh ? "保存" : "Save metadata"}
          </button>
        </form>
      ) : null}
      <section className="card space-y-3 p-6">
        <h2 className="text-lg font-semibold">
          {zh ? "治理操作" : "Governance"}
        </h2>
        {can("media:submit_review") &&
        ["uploaded", "revoked"].includes(asset.public_use_status) ? (
          <Action
            asset={asset}
            action="submit-review"
            label={zh ? "提交审核" : "Submit review"}
          />
        ) : null}
        {can("media:approve") && asset.public_use_status === "review" ? (
          <Action
            asset={asset}
            action="approve"
            label={zh ? "批准公开使用" : "Approve public use"}
          />
        ) : null}
        {can("media:revoke") && asset.public_use_status === "approved" ? (
          <Action
            asset={asset}
            action="revoke"
            label={zh ? "撤销公开使用" : "Revoke public use"}
          />
        ) : null}
        {can("media:archive") && asset.public_use_status !== "archived" ? (
          <Action
            asset={asset}
            action="archive"
            label={zh ? "归档" : "Archive"}
          />
        ) : null}
      </section>
      {audit.length ? (
        <section className="card overflow-hidden">
          <h2 className="p-5 text-lg font-semibold">
            {zh ? "审计记录" : "Audit timeline"}
          </h2>
          <div className="divide-y divide-[var(--color-line)]">
            {audit.map((entry) => (
              <div className="p-5 text-sm" key={entry.id}>
                <strong>{entry.action}</strong>
                <span className="ml-3 text-[var(--color-muted)]">
                  {new Date(entry.created_at).toLocaleString(locale)}
                </span>
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function Action({
  asset,
  action,
  label,
}: {
  asset: MediaAsset;
  action: "submit-review" | "approve" | "revoke" | "archive";
  label: string;
}) {
  return (
    <form
      action={governMedia.bind(null, asset.id, asset.record_version, action)}
    >
      <button className="button-tertiary" type="submit">
        {label}
      </button>
    </form>
  );
}
