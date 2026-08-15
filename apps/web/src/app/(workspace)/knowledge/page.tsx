import Link from "next/link";

import { PageHeader } from "@/components/workspace/page-header";
import { getLocale } from "@/i18n/server";
import {
  apiFetch,
  type KnowledgeCollection,
  type ManagedKnowledgeDocument,
} from "@/lib/api";

import {
  activateKnowledgeDocument,
  archiveKnowledgeDocument,
  bindKnowledgeDocument,
  createKnowledgeCollection,
  processKnowledgeDocument,
  publishKnowledgeDocument,
  reviewKnowledgeDocument,
  submitKnowledgeReview,
  uploadKnowledgeDocument,
} from "./actions";

export default async function KnowledgePage({
  searchParams,
}: PageProps<"/knowledge">) {
  const query = await searchParams;
  const search = value(query.search);
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  const [collections, documents, locale] = await Promise.all([
    apiFetch<KnowledgeCollection[]>("/api/v1/knowledge-management/collections"),
    apiFetch<ManagedKnowledgeDocument[]>(
      `/api/v1/knowledge-management/documents?${params}`,
    ),
    getLocale(),
  ]);
  const zh = locale === "zh-CN";
  const copy = zh ? chinese : english;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow={copy.eyebrow}
        title={copy.title}
        description={copy.description}
      />

      <div className="flex justify-end">
        <div className="flex flex-wrap gap-2">
          <Link className="button-primary" href="/knowledge/assistant">
            {zh ? "打开知识助手" : "Open Knowledge Assistant"}
          </Link>
          <Link className="button-tertiary" href="/knowledge/search">
            {zh ? "测试知识检索" : "Test knowledge retrieval"}
          </Link>
        </div>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {collections.map((collection) => (
          <article className="card p-5" key={collection.id}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-[var(--color-brand)]">
                  {domainLabel(collection.domain_key, zh)}
                </p>
                <h2 className="mt-2 text-lg font-semibold">
                  {collection.name}
                </h2>
              </div>
              <span className="status-chip">{collection.document_count}</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">
              {collection.description || copy.noDescription}
            </p>
          </article>
        ))}
        {!collections.length ? (
          <div className="card p-6 text-sm text-[var(--color-muted)]">
            {copy.noCollections}
          </div>
        ) : null}
      </section>

      <div className="grid gap-6 xl:grid-cols-2">
        <form action={createKnowledgeCollection} className="card p-6">
          <h2 className="text-lg font-semibold">{copy.createCollection}</h2>
          <Field label={copy.name} name="name" required />
          <Field label={copy.key} name="collection_key" required />
          <Select
            label={copy.domain}
            name="domain_key"
            options={[
              ["commercial_kitchen", copy.kitchen],
              ["laboratory_animal_facility", copy.ivc],
            ]}
          />
          <Field label={copy.descriptionField} name="description" />
          <button className="button-primary mt-5" type="submit">
            {copy.create}
          </button>
        </form>

        <form action={uploadKnowledgeDocument} className="card p-6">
          <h2 className="text-lg font-semibold">{copy.upload}</h2>
          <Select
            label={copy.collection}
            name="collection_id"
            options={collections.map((item) => [item.id, item.name])}
          />
          <Field label={copy.documentTitle} name="title" required />
          <Select
            label={copy.documentType}
            name="document_type"
            options={[
              ["company_profile", copy.companyProfile],
              ["case_study", copy.caseStudy],
              ["product_catalogue", copy.productCatalogue],
              ["installation_sop", "Installation SOP"],
              ["technical_reference", copy.technicalReference],
            ]}
          />
          <Select
            label={copy.language}
            name="language"
            options={[
              ["en", "English"],
              ["zh-CN", "中文"],
              ["id", "Bahasa Indonesia"],
            ]}
          />
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
          <button
            className="button-primary mt-5"
            type="submit"
            disabled={!collections.length}
          >
            {copy.uploadAction}
          </button>
        </form>
      </div>

      <section className="card overflow-hidden">
        <div className="border-b border-[var(--color-line)] p-5 sm:flex sm:items-end sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold">{copy.documents}</h2>
            <p className="mt-1 text-sm text-[var(--color-muted)]">
              {copy.documentsHelp}
            </p>
          </div>
          <form action="/knowledge" className="mt-4 flex gap-2 sm:mt-0">
            <input
              className="field min-w-0"
              name="search"
              defaultValue={search}
              placeholder={copy.search}
            />
            <button className="button-tertiary" type="submit">
              {copy.find}
            </button>
          </form>
        </div>
        <div className="divide-y divide-[var(--color-line)]">
          {documents.map((document) => (
            <DocumentRow
              key={document.id}
              document={document}
              copy={copy}
              zh={zh}
            />
          ))}
          {!documents.length ? (
            <p className="p-6 text-sm text-[var(--color-muted)]">
              {copy.noDocuments}
            </p>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function DocumentRow({
  document,
  copy,
  zh,
}: {
  document: ManagedKnowledgeDocument;
  copy: Copy;
  zh: boolean;
}) {
  const agentKey =
    document.domain_key === "commercial_kitchen"
      ? "commercial_kitchen.lead_qualification"
      : "laboratory_animal_facility.ivc_business_development";
  return (
    <article className="p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold">
              <Link
                className="hover:text-[var(--color-brand)]"
                href={`/knowledge/${document.id}`}
              >
                {document.title}
              </Link>
            </h3>
            <span className="status-chip">
              {statusLabel(document.lifecycle_status, zh)}
            </span>
            <span className="status-chip">
              {copy.processing}:{" "}
              {processingLabel(document.processing_status, zh)}
            </span>
            <span className="text-xs font-semibold text-[var(--color-muted)]">
              v{document.current_version_number}
            </span>
          </div>
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            {document.collection_name} · {domainLabel(document.domain_key, zh)}{" "}
            · {document.language} · {document.document_type}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {!document.agent_id ? (
            <form action={bindKnowledgeDocument.bind(null, document.id)}>
              <input type="hidden" name="agent_key" value={agentKey} />
              <button className="button-tertiary" type="submit">
                {copy.bind}
              </button>
            </form>
          ) : null}
          {document.lifecycle_status === "uploaded" ? (
            <form action={submitKnowledgeReview.bind(null, document.id)}>
              <button className="button-tertiary" type="submit">
                {copy.submitReview}
              </button>
            </form>
          ) : null}
          {document.lifecycle_status === "review" &&
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
          {document.lifecycle_status === "approved" ? (
            <form action={publishKnowledgeDocument.bind(null, document.id)}>
              <button className="button-primary" type="submit">
                {copy.publish}
              </button>
            </form>
          ) : null}
          {document.lifecycle_status === "published" ? (
            <form action={activateKnowledgeDocument.bind(null, document.id)}>
              <button className="button-primary" type="submit">
                {copy.activate}
              </button>
            </form>
          ) : null}
          {["approved", "published", "active"].includes(
            document.lifecycle_status,
          ) && document.processing_status !== "processing" ? (
            <form action={processKnowledgeDocument.bind(null, document.id)}>
              <button className="button-primary" type="submit">
                {document.processing_status === "completed"
                  ? copy.reprocess
                  : copy.process}
              </button>
            </form>
          ) : null}
          {["approved", "published", "active"].includes(
            document.lifecycle_status,
          ) ? (
            <form action={archiveKnowledgeDocument.bind(null, document.id)}>
              <button className="button-tertiary" type="submit">
                {copy.archive}
              </button>
            </form>
          ) : null}
        </div>
      </div>
    </article>
  );
}

function Field({
  label,
  name,
  required = false,
}: {
  label: string;
  name: string;
  required?: boolean;
}) {
  return (
    <label className="label">
      {label}
      <input className="field mt-2" name={name} required={required} />
    </label>
  );
}

function Select({
  label,
  name,
  options,
}: {
  label: string;
  name: string;
  options: string[][];
}) {
  return (
    <label className="label">
      {label}
      <select className="field mt-2" name={name} required>
        {options.map(([id, text]) => (
          <option key={id} value={id}>
            {text}
          </option>
        ))}
      </select>
    </label>
  );
}

function value(input: string | string[] | undefined) {
  return Array.isArray(input) ? input[0] : input;
}
function domainLabel(key: string, zh: boolean) {
  return key === "commercial_kitchen"
    ? zh
      ? "商用厨房"
      : "Commercial Kitchen"
    : zh
      ? "实验动物设施 / IVC"
      : "Laboratory Animal Facility / IVC";
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

function processingLabel(status: string, zh: boolean) {
  if (!zh) return status;
  return (
    (
      {
        uploaded: "待处理",
        processing: "处理中",
        completed: "已完成",
        failed: "失败",
      } as Record<string, string>
    )[status] ?? status
  );
}

const english = {
  eyebrow: "Phase 2.5.1 · Knowledge control plane",
  title: "Knowledge management",
  description:
    "Organize synthetic or approved business documents by domain, review exact versions, and explicitly grant agent access. No conversational assistant or RAG is enabled here.",
  noDescription: "No description",
  noCollections: "No collections yet.",
  createCollection: "Create collection",
  name: "Collection name",
  key: "Collection key",
  domain: "Business domain",
  descriptionField: "Description",
  kitchen: "Commercial Kitchen",
  ivc: "Laboratory Animal Facility / IVC",
  create: "Create collection",
  upload: "Upload document",
  collection: "Collection",
  documentTitle: "Document title",
  documentType: "Document type",
  companyProfile: "Company profile",
  caseStudy: "Case study",
  productCatalogue: "Product catalogue",
  technicalReference: "Technical reference",
  language: "Language",
  file: "PDF, DOCX, text, or Markdown file",
  uploadAction: "Upload document",
  documents: "Documents",
  documentsHelp:
    "Only explicitly bound and approved/active versions are eligible for processing and future RAG publication.",
  search: "Search title or type",
  find: "Search",
  noDocuments: "No documents found.",
  bind: "Bind to domain agent",
  submitReview: "Submit for review",
  approve: "Approve",
  reject: "Reject",
  publish: "Publish",
  activate: "Activate",
  archive: "Archive",
  processing: "Processing",
  process: "Process",
  reprocess: "Reprocess",
};
const chinese: typeof english = {
  eyebrow: "Phase 2.5.1 · 知识控制面",
  title: "企业知识管理",
  description:
    "按业务域管理合成或已获授权的业务文档，审核准确版本，并明确授予智能体访问权限。这里不会启用对话助手或 RAG。",
  noDescription: "暂无说明",
  noCollections: "尚未创建知识集合。",
  createCollection: "创建知识集合",
  name: "集合名称",
  key: "集合标识",
  domain: "业务域",
  descriptionField: "说明",
  kitchen: "商用厨房",
  ivc: "实验动物设施 / IVC",
  create: "创建集合",
  upload: "上传文档",
  collection: "知识集合",
  documentTitle: "文档标题",
  documentType: "文档类型",
  companyProfile: "公司简介",
  caseStudy: "项目案例",
  productCatalogue: "产品目录",
  technicalReference: "技术资料",
  language: "语言",
  file: "PDF、DOCX、文本或 Markdown 文件",
  uploadAction: "上传文档",
  documents: "文档",
  documentsHelp:
    "只有明确绑定智能体且状态为已批准或已生效的版本，才可处理并在未来发布到 RAG。",
  search: "按标题或类型查找",
  find: "查找",
  noDocuments: "没有找到文档。",
  bind: "绑定业务智能体",
  submitReview: "提交审核",
  approve: "批准",
  reject: "拒绝",
  publish: "发布",
  activate: "启用",
  archive: "归档",
  processing: "处理状态",
  process: "开始处理",
  reprocess: "重新处理",
};
type Copy = typeof english;
