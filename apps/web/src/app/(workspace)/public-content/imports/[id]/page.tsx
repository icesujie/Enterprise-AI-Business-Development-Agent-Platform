import Link from "next/link";

import {
  createPublicDraftFromImport,
  structurePublicContentImport,
} from "@/app/(workspace)/public-content/imports/actions";
import { StatusBadge } from "@/components/ui/status";
import { PageHeader } from "@/components/workspace/page-header";
import { getLocale } from "@/i18n/server";
import {
  apiFetch,
  type PublicContentImport,
  type PublicContentStructuringRun,
} from "@/lib/api";

export default async function PublicContentImportDetailPage({
  params,
}: PageProps<"/public-content/imports/[id]">) {
  const { id } = await params;
  const [record, runs, locale] = await Promise.all([
    apiFetch<PublicContentImport>(`/api/v1/public-content/imports/${id}`),
    apiFetch<PublicContentStructuringRun[]>(
      `/api/v1/public-content/imports/${id}/structuring-runs`,
    ),
    getLocale(),
  ]);
  const zh = locale === "zh-CN";
  const blocks = record.extraction_result.blocks ?? [];
  const media = record.extraction_result.media ?? [];
  const latest = runs.find((run) => run.status === "completed") ?? runs[0];
  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow={zh ? "内部导入预览" : "Internal import preview"}
        title={record.extraction_result.title || record.original_filename}
        description={
          zh
            ? "提取内容保持为内部资料；本阶段不会生成或发布网页。"
            : "Extracted content remains internal; this phase does not generate or publish a webpage."
        }
        actions={
          <Link className="button-tertiary" href="/public-content/imports">
            {zh ? "返回导入记录" : "Back to imports"}
          </Link>
        }
      />
      <section className="grid gap-4 md:grid-cols-4">
        <Summary label={zh ? "状态" : "Status"}>
          <StatusBadge
            tone={
              record.processing_status === "completed"
                ? "success"
                : record.processing_status === "failed"
                  ? "danger"
                  : "info"
            }
          >
            {record.processing_status}
          </StatusBadge>
        </Summary>
        <Summary label={zh ? "来源类型" : "Source type"}>
          {record.source_type.toUpperCase()}
        </Summary>
        <Summary label={zh ? "结构块" : "Structured blocks"}>
          {String(blocks.length)}
        </Summary>
        <Summary label={zh ? "私有媒体" : "Private media"}>
          {String(media.length)}
        </Summary>
      </section>
      {record.failure_reason ? (
        <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-800">
          <strong>{zh ? "提取失败：" : "Extraction failed: "}</strong>
          {record.failure_reason}
        </div>
      ) : null}
      {blocks.length ? (
        <section
          className="card p-6 sm:p-8"
          aria-labelledby="extracted-content-title"
        >
          <h2 id="extracted-content-title" className="text-xl font-semibold">
            {zh ? "提取内容" : "Extracted content"}
          </h2>
          <div className="mt-6 space-y-5">
            {blocks.map((block) => (
              <article
                key={`${block.order}-${block.kind}`}
                className="border-l-2 border-[var(--color-line)] pl-4"
              >
                <p className="text-[0.68rem] font-bold uppercase tracking-wider text-[var(--color-muted)]">
                  {block.kind}
                  {block.page_number ? ` · page ${block.page_number}` : ""}
                  {block.section_title ? ` · ${block.section_title}` : ""}
                </p>
                {block.kind === "heading" ? (
                  <h3 className="mt-1 text-lg font-semibold">{block.text}</h3>
                ) : (
                  <p className="mt-1 whitespace-pre-wrap text-sm leading-7">
                    {block.text}
                  </p>
                )}
              </article>
            ))}
          </div>
        </section>
      ) : null}
      {media.length ? (
        <section className="card p-6" aria-labelledby="imported-media-title">
          <h2 id="imported-media-title" className="text-xl font-semibold">
            {zh ? "提取的私有媒体" : "Extracted private media"}
          </h2>
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            {zh
              ? "所有图片都需要在媒体库中单独审核后才能公开使用。"
              : "Every image requires separate Media Library review before public use."}
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            {media.map((item) => (
              <Link
                className="button-tertiary"
                href={`/media/${item.media_asset_id}`}
                key={item.media_asset_id}
              >
                {zh ? "查看图片" : "Review image"} {item.order + 1}
              </Link>
            ))}
          </div>
        </section>
      ) : null}
      {record.processing_status === "completed" ? (
        <section
          className="card space-y-5 p-6"
          aria-labelledby="structure-title"
        >
          <div>
            <p className="eyebrow">
              {zh ? "AI 辅助，人工控制" : "AI-assisted, human controlled"}
            </p>
            <h2 id="structure-title" className="mt-2 text-xl font-semibold">
              {zh ? "结构化为公开内容" : "Structure as Public Content"}
            </h2>
            <p className="mt-2 text-sm text-[var(--color-muted)]">
              {zh
                ? "只使用本次导入的提取结果。结构化不会创建、审批或发布页面。"
                : "Uses only this import result. Structuring does not create, approve, or publish a page."}
            </p>
          </div>
          <form
            action={structurePublicContentImport.bind(null, record.id)}
            className="grid gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end"
          >
            <label className="space-y-2 text-sm font-semibold">
              <span>{zh ? "目标页面类型" : "Target page type"}</span>
              <select
                className="input w-full"
                name="page_type"
                defaultValue={latest?.recommended_page_type ?? "solution"}
              >
                <option value="solution">Solution</option>
                <option value="industry">Industry</option>
                <option value="case_study">Case study</option>
                <option value="guide">Guide</option>
                <option value="product">Product</option>
              </select>
            </label>
            <label className="space-y-2 text-sm font-semibold">
              <span>{zh ? "内容语言" : "Content locale"}</span>
              <select
                className="input w-full"
                name="locale"
                defaultValue={latest?.locale ?? "en"}
              >
                <option value="en">English</option>
                <option value="zh-CN">中文</option>
              </select>
            </label>
            <button className="button-primary" type="submit">
              {zh ? "运行结构化" : "Run structuring"}
            </button>
          </form>
        </section>
      ) : null}
      {latest ? (
        <StructuringPreview run={latest} importRecord={record} zh={zh} />
      ) : null}
      <section className="card p-6 text-sm text-[var(--color-muted)]">
        <p>
          <strong>Import ID:</strong> {record.id}
        </p>
        <p className="mt-2">
          <strong>SHA-256:</strong>{" "}
          <span className="break-all font-mono text-xs">{record.checksum}</span>
        </p>
      </section>
    </div>
  );
}

function StructuringPreview({
  run,
  importRecord,
  zh,
}: {
  run: PublicContentStructuringRun;
  importRecord: PublicContentImport;
  zh: boolean;
}) {
  const result = run.result;
  const productCandidates = result.product_candidates ?? [];
  if (run.status === "failed")
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-800">
        {run.failure_reason ?? (zh ? "结构化失败。" : "Structuring failed.")}
      </div>
    );
  return (
    <section
      className="card space-y-6 p-6 sm:p-8"
      aria-labelledby="structuring-preview-title"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow">{zh ? "结构化预览" : "Structured preview"}</p>
          <h2
            id="structuring-preview-title"
            className="mt-2 text-xl font-semibold"
          >
            {result.title || importRecord.original_filename}
          </h2>
        </div>
        <div className="text-right text-xs text-[var(--color-muted)]">
          <p>
            {run.provider} · {run.model}
          </p>
          <p>
            {run.duration_ms ?? "—"} ms · {run.correlation_id ?? "—"}
          </p>
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <Summary label={zh ? "结果" : "Outcome"}>
          {run.outcome ?? run.status}
        </Summary>
        <Summary label={zh ? "推荐" : "Recommended"}>
          {run.recommended_page_type ?? "—"}
        </Summary>
        <Summary label={zh ? "已选择" : "Selected"}>
          {run.selected_page_type}
        </Summary>
      </div>
      {run.missing_fields.length ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
          <strong>{zh ? "需要人工补充：" : "Human input required: "}</strong>
          {run.missing_fields.join(", ")}
        </div>
      ) : null}
      {result.multiple_products_detected ? (
        <div className="rounded-xl border border-amber-300 bg-amber-50 p-5 text-sm text-amber-950">
          <strong>
            {zh ? "检测到多个产品。" : "Multiple products detected."}
          </strong>{" "}
          {zh
            ? "请选择并确认一个候选产品；系统不会批量创建产品页面。"
            : "Review and confirm one candidate. No batch Product pages will be created."}
        </div>
      ) : null}
      {run.selected_page_type === "product" && productCandidates.length ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {productCandidates.map((candidate) => (
            <div
              className="rounded-xl border border-[var(--color-line)] bg-[#f5f6f2] p-5 text-sm"
              key={candidate.candidate_key}
            >
              <p className="eyebrow">{candidate.candidate_key}</p>
              <h3 className="mt-2 text-lg font-semibold">
                {candidate.title ?? (zh ? "未命名产品" : "Untitled Product")}
              </h3>
              <p className="mt-3 text-[var(--color-muted)]">
                {candidate.summary ??
                  (zh
                    ? "需要人工补充产品摘要。"
                    : "Product summary requires human input.")}
              </p>
              <p className="mt-3 text-xs text-[var(--color-muted)]">
                {candidate.missing_fields.length
                  ? `${zh ? "缺失：" : "Missing: "}${candidate.missing_fields.join(", ")}`
                  : zh
                    ? "来源字段完整，仍需人工审核。"
                    : "Source fields are complete; human review is still required."}
              </p>
              <ProductPricingPreview candidate={candidate} zh={zh} />
            </div>
          ))}
        </div>
      ) : null}
      <div>
        <h3 className="font-semibold">{zh ? "来源依据" : "Source evidence"}</h3>
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          {(result.evidence ?? []).slice(0, 12).map((evidence, index) => (
            <div
              className="rounded-lg bg-[#f5f6f2] p-3 text-xs"
              key={`${evidence.field_path}-${index}`}
            >
              <strong>{evidence.field_path}</strong>
              <p className="mt-1 text-[var(--color-muted)]">
                block {evidence.block_order ?? "—"}
                {evidence.source_page ? ` · page ${evidence.source_page}` : ""}
                {evidence.source_section ? ` · ${evidence.source_section}` : ""}
              </p>
            </div>
          ))}
        </div>
      </div>
      {run.outcome !== "insufficient_source" ? (
        productCandidates.length ? (
          productCandidates.map((candidate) => (
            <DraftCreationForm
              candidate={candidate}
              importRecord={importRecord}
              key={candidate.candidate_key}
              run={run}
              zh={zh}
            />
          ))
        ) : (
          <DraftCreationForm importRecord={importRecord} run={run} zh={zh} />
        )
      ) : null}
    </section>
  );
}

type ProductCandidate = NonNullable<
  PublicContentStructuringRun["result"]["product_candidates"]
>[number];

function DraftCreationForm({
  candidate,
  importRecord,
  run,
  zh,
}: {
  candidate?: ProductCandidate;
  importRecord: PublicContentImport;
  run: PublicContentStructuringRun;
  zh: boolean;
}) {
  const result = run.result;
  const title = candidate?.title ?? result.title;
  const summary = candidate?.summary ?? result.summary;
  const seoTitle = candidate?.seo_title ?? result.seo_title ?? title;
  const seoDescription =
    candidate?.seo_description ?? result.seo_description ?? summary;
  const structuredContent =
    candidate?.cms_structured_content ?? result.cms_structured_content ?? {};
  const mediaSuggestions =
    candidate?.media_suggestions ?? result.media_suggestions ?? [];
  const mediaReferences = mediaSuggestions.map((suggestion) => ({
    media_asset_id: suggestion.media_asset_id,
    role:
      run.selected_page_type === "product" && suggestion.role === "hero"
        ? "product_hero"
        : suggestion.role === "gallery"
          ? "product_gallery"
          : suggestion.role,
    alt_text: "Review imported media metadata before public use.",
    caption: null,
  }));
  return (
    <form
      action={createPublicDraftFromImport.bind(null, importRecord.id, run.id)}
      className="space-y-4 border-t border-[var(--color-line)] pt-6"
    >
      {candidate ? (
        <input
          name="product_candidate_key"
          type="hidden"
          value={candidate.candidate_key}
        />
      ) : null}
      <h3 className="text-lg font-semibold">
        {candidate
          ? `${zh ? "确认产品候选" : "Confirm Product candidate"}: ${candidate.candidate_key}`
          : zh
            ? "确认并创建私有草稿"
            : "Confirm and create private Draft"}
      </h3>
      <p className="text-sm text-[var(--color-muted)]">
        {zh
          ? "请先修正缺失字段。创建后仍须经过现有审核和发布流程。"
          : "Correct missing fields first. The resulting Draft still requires the existing review and publishing workflow."}
      </p>
      {candidate ? (
        <ProductPricingPreview candidate={candidate} zh={zh} />
      ) : null}
      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="URL slug"
          name="slug"
          defaultValue={
            candidate?.slug_suggestion ??
            slugify(String(title ?? "imported-page"))
          }
        />
        <Input
          label={zh ? "标题" : "Title"}
          name="title"
          defaultValue={String(title ?? "")}
        />
        <Input
          label="SEO title"
          name="seo_title"
          defaultValue={String(seoTitle ?? "")}
        />
        <Input
          label="SEO description"
          name="seo_description"
          defaultValue={String(seoDescription ?? "")}
        />
      </div>
      <label className="block space-y-2 text-sm font-semibold">
        <span>{zh ? "摘要" : "Summary"}</span>
        <textarea
          className="input min-h-24 w-full"
          name="summary"
          defaultValue={String(summary ?? "")}
          required
        />
      </label>
      <label className="block space-y-2 text-sm font-semibold">
        <span>{zh ? "结构化内容 JSON" : "Structured content JSON"}</span>
        <textarea
          className="input min-h-80 w-full font-mono text-xs"
          name="structured_content"
          defaultValue={JSON.stringify(structuredContent, null, 2)}
          required
        />
      </label>
      <label className="block space-y-2 text-sm font-semibold">
        <span>{zh ? "媒体引用 JSON" : "Media references JSON"}</span>
        <textarea
          className="input min-h-32 w-full font-mono text-xs"
          name="media_references"
          defaultValue={JSON.stringify(mediaReferences, null, 2)}
          required
        />
      </label>
      <p className="text-xs leading-5 text-[var(--color-muted)]">
        {zh
          ? "导入媒体保持私有并需要单独批准；创建产品草稿不会批准任何图片。"
          : "Imported media remains private and requires separate approval; creating this Draft approves no image."}
      </p>
      <label className="flex items-center gap-3 text-sm text-[var(--color-muted)]">
        <input type="checkbox" name="is_synthetic" />
        {zh
          ? "标记为合成/演示内容（禁止发布）"
          : "Synthetic/demo content (publishing blocked)"}
      </label>
      <button className="button-primary" type="submit">
        {zh ? "创建私有草稿" : "Create private Draft"}
      </button>
    </form>
  );
}

function ProductPricingPreview({
  candidate,
  zh,
}: {
  candidate: ProductCandidate;
  zh: boolean;
}) {
  const content = candidate.content;
  const mode = String(content.price_mode ?? "request_quote");
  const currency = content.currency ? String(content.currency) : null;
  const minimum = content.price_min ? String(content.price_min) : null;
  const maximum = content.price_max ? String(content.price_max) : null;
  return (
    <div className="mt-4 rounded-lg border border-[var(--color-line)] bg-white p-3 text-xs">
      <strong>{zh ? "价格审核" : "Pricing review"}</strong>
      <p className="mt-1 text-[var(--color-muted)]">
        {mode}
        {currency ? ` · ${currency}` : ""}
        {minimum ? ` · ${minimum}${maximum ? `–${maximum}` : ""}` : ""}
      </p>
      <p className="mt-1 text-[var(--color-muted)]">
        {zh
          ? "价格与币种仅在来源明确提供时填入，否则保持询价模式。"
          : "Price and currency are populated only when explicit in the source; otherwise request-quote remains selected."}
      </p>
    </div>
  );
}

function Input({
  label,
  name,
  defaultValue,
}: {
  label: string;
  name: string;
  defaultValue: string;
}) {
  return (
    <label className="space-y-2 text-sm font-semibold">
      <span>{label}</span>
      <input
        className="input w-full"
        name={name}
        defaultValue={defaultValue}
        required
      />
    </label>
  );
}

function slugify(value: string) {
  return (
    value
      .normalize("NFKD")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "")
      .slice(0, 160) || "imported-page"
  );
}

function Summary({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="card p-5">
      <p className="text-xs font-bold uppercase tracking-wider text-[var(--color-muted)]">
        {label}
      </p>
      <div className="mt-2 text-lg font-semibold">{children}</div>
    </div>
  );
}
