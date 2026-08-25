import Link from "next/link";

import { importPublicContentDocument } from "@/app/(workspace)/public-content/imports/actions";
import { StatusBadge } from "@/components/ui/status";
import { PageHeader } from "@/components/workspace/page-header";
import { getLocale } from "@/i18n/server";
import { apiFetch, type PublicContentImport } from "@/lib/api";

export default async function PublicContentImportsPage() {
  const [imports, locale] = await Promise.all([
    apiFetch<PublicContentImport[]>("/api/v1/public-content/imports"),
    getLocale(),
  ]);
  const zh = locale === "zh-CN";
  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow={zh ? "公开内容来源" : "Public content sources"}
        title={zh ? "文档导入" : "Document Imports"}
        description={
          zh
            ? "安全提取现有业务文档的文本、结构和图片。导入不会创建或发布公开页面。"
            : "Safely extract text, structure, and images from existing business documents. Imports never create or publish public pages."
        }
        actions={
          <Link className="button-tertiary" href="/public-content">
            {zh ? "返回公开内容" : "Back to Public Content"}
          </Link>
        }
      />
      <form
        action={importPublicContentDocument}
        className="card grid gap-4 p-6 lg:grid-cols-[1fr_auto] lg:items-end"
      >
        <label className="space-y-2 text-sm font-semibold">
          <span>{zh ? "选择业务文档" : "Choose business document"}</span>
          <input
            aria-label={zh ? "选择业务文档" : "Choose business document"}
            className="input block w-full"
            name="file"
            type="file"
            accept=".docx,.pdf,.html,.htm,.txt,.md"
            required
          />
          <span className="block text-xs font-normal text-[var(--color-muted)]">
            DOCX, text-based PDF, HTML, TXT{zh ? " 或 Markdown。暂不支持 OCR。" : ", or Markdown. OCR is not supported."}
          </span>
        </label>
        <button className="button-primary" type="submit">
          {zh ? "导入并提取" : "Import and extract"}
        </button>
      </form>
      <section className="space-y-3" aria-labelledby="import-history-title">
        <h2 id="import-history-title" className="text-xl font-semibold">
          {zh ? "导入记录" : "Import history"}
        </h2>
        {imports.length ? (
          <div className="card overflow-x-auto">
            <table className="w-full min-w-[700px] text-left text-sm">
              <thead className="border-b border-[var(--color-line)] bg-[#f7f8f5] text-xs uppercase tracking-wider text-[var(--color-muted)]">
                <tr>
                  <th className="p-4">{zh ? "文件" : "File"}</th>
                  <th className="p-4">{zh ? "类型" : "Type"}</th>
                  <th className="p-4">{zh ? "状态" : "Status"}</th>
                  <th className="p-4">{zh ? "提取结果" : "Extraction"}</th>
                  <th className="p-4">{zh ? "创建时间" : "Created"}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-line)]">
                {imports.map((record) => (
                  <tr key={record.id}>
                    <td className="p-4">
                      <Link
                        href={`/public-content/imports/${record.id}`}
                        className="font-semibold text-[var(--color-brand)]"
                      >
                        {record.original_filename}
                      </Link>
                    </td>
                    <td className="p-4 uppercase">{record.source_type}</td>
                    <td className="p-4">
                      <StatusBadge tone={statusTone(record.processing_status)}>
                        {record.processing_status}
                      </StatusBadge>
                    </td>
                    <td className="p-4 text-[var(--color-muted)]">
                      {record.processing_status === "completed"
                        ? `${record.extraction_metadata.block_count ?? 0} blocks · ${record.extracted_media_ids.length} media`
                        : record.failure_reason ?? "—"}
                    </td>
                    <td className="p-4">
                      {new Intl.DateTimeFormat(locale, { dateStyle: "medium" }).format(
                        new Date(record.created_at),
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="card p-8 text-sm text-[var(--color-muted)]">
            {zh ? "尚无文档导入记录。" : "No documents have been imported."}
          </div>
        )}
      </section>
    </div>
  );
}

function statusTone(status: string): "neutral" | "info" | "success" | "warning" | "danger" {
  if (status === "completed") return "success";
  if (status === "failed") return "danger";
  if (status === "processing") return "info";
  return "neutral";
}
