"use client";

import { useState } from "react";

import {
  searchKnowledge,
  type KnowledgeSearchActionResult,
} from "@/app/(workspace)/knowledge/search/actions";
import type { KnowledgeSearchResult } from "@/lib/api";

const agents = [
  {
    id: "61000000-0000-4000-8000-000000000001",
    en: "Commercial Kitchen Agent",
    zh: "商用厨房智能体",
  },
  {
    id: "61000000-0000-4000-8000-000000000002",
    en: "IVC Facility Agent (retrieval disabled)",
    zh: "IVC 设施智能体（检索未启用）",
  },
];

export function KnowledgeSearchTester({ zh }: { zh: boolean }) {
  const [state, setState] = useState<KnowledgeSearchActionResult | null>(null);
  const [pending, setPending] = useState(false);
  const copy = zh ? chinese : english;

  async function submit(formData: FormData) {
    setPending(true);
    setState(null);
    const result = await searchKnowledge({
      agent_id: String(formData.get("agent_id")),
      query: String(formData.get("query")),
      language: String(formData.get("language")) as "en" | "zh-CN" | "id",
      top_k: Number(formData.get("top_k")),
    });
    setState(result);
    setPending(false);
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[360px_1fr]">
      <form action={submit} className="card h-fit space-y-5 p-6">
        <h2 className="text-lg font-semibold">{copy.parameters}</h2>
        <Select label={copy.agent} name="agent_id">
          {agents.map((agent) => (
            <option key={agent.id} value={agent.id}>
              {zh ? agent.zh : agent.en}
            </option>
          ))}
        </Select>
        <label className="label">
          {copy.query}
          <textarea
            className="field mt-2 min-h-32 resize-y"
            name="query"
            minLength={3}
            maxLength={2000}
            required
            placeholder={copy.placeholder}
          />
        </label>
        <Select label={copy.language} name="language">
          <option value="en">English</option>
          <option value="zh-CN">中文</option>
          <option value="id">Bahasa Indonesia</option>
        </Select>
        <Select label="Top K" name="top_k">
          {[1, 3, 5, 10].map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </Select>
        <button
          className="button-primary w-full"
          disabled={pending}
          type="submit"
        >
          {pending ? copy.searching : copy.search}
        </button>
      </form>

      <section className="space-y-5" aria-live="polite">
        {!state && !pending ? <Empty copy={copy} /> : null}
        {pending ? <Loading copy={copy} /> : null}
        {state && !state.ok ? (
          <div
            className={`card border-l-4 p-6 ${state.kind === "denied" ? "border-l-amber-600" : "border-l-red-600"}`}
          >
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--color-muted)]">
              {state.kind === "denied" ? copy.denied : copy.error}
            </p>
            <p className="mt-2 font-semibold">{state.message}</p>
            {state.kind === "denied" ? (
              <p className="mt-2 text-sm text-[var(--color-muted)]">
                {copy.deniedHelp}
              </p>
            ) : null}
          </div>
        ) : null}
        {state?.ok ? <SearchResults data={state.data} copy={copy} /> : null}
      </section>
    </div>
  );
}

function SearchResults({
  data,
  copy,
}: {
  data: Extract<KnowledgeSearchActionResult, { ok: true }>["data"];
  copy: Copy;
}) {
  return (
    <>
      <div
        className={`card border-l-4 p-5 ${data.evidence_status === "sufficient_candidates" ? "border-l-emerald-700" : "border-l-amber-600"}`}
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--color-muted)]">
              {copy.decision}
            </p>
            <h2 className="mt-1 text-xl font-semibold">
              {data.evidence_status === "sufficient_candidates"
                ? copy.sufficient
                : copy.insufficient}
            </h2>
          </div>
          <div className="text-right text-xs text-[var(--color-muted)]">
            <p>
              {copy.threshold}: {data.similarity_threshold.toFixed(3)}
            </p>
            <p>
              {copy.duration}: {data.duration_ms.toFixed(1)} ms
            </p>
          </div>
        </div>
        <p className="mt-3 text-sm text-[var(--color-muted)]">
          {copy.reason}: {data.decision_reason} · {copy.correlation}:{" "}
          {data.correlation_id}
        </p>
      </div>

      {data.results.length ? (
        <ResultGroup
          title={copy.relevant}
          tone="relevant"
          results={data.results}
        />
      ) : null}
      {data.below_threshold_results.length ? (
        <ResultGroup
          title={copy.below}
          tone="below"
          results={data.below_threshold_results}
        />
      ) : null}
      {!data.results.length && !data.below_threshold_results.length ? (
        <div className="card p-8 text-center text-sm text-[var(--color-muted)]">
          {copy.noCandidates}
        </div>
      ) : null}
    </>
  );
}

function ResultGroup({
  title,
  tone,
  results,
}: {
  title: string;
  tone: "relevant" | "below";
  results: KnowledgeSearchResult[];
}) {
  return (
    <div className="space-y-3">
      <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--color-muted)]">
        {title}
      </h2>
      {results.map((result, index) => (
        <article className="card p-5" key={result.citation.chunk_id}>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-bold text-[var(--color-brand)]">
                #{index + 1} ·{" "}
                {tone === "relevant" ? "RELEVANT" : "BELOW THRESHOLD"}
              </p>
              <h3 className="mt-1 font-semibold">
                {result.document_name} · v{result.document_version}
              </h3>
              <p className="mt-1 text-xs text-[var(--color-muted)]">
                {result.section ?? "—"} · page {result.page_number ?? "—"}
              </p>
            </div>
            <span className="status-chip font-mono">
              {result.similarity_score.toFixed(6)}
            </span>
          </div>
          <p className="mt-4 whitespace-pre-wrap text-sm leading-6">
            {result.chunk_content}
          </p>
          <details className="mt-4 border-t border-[var(--color-line)] pt-3 text-xs text-[var(--color-muted)]">
            <summary className="cursor-pointer font-semibold">Citation</summary>
            <dl className="mt-3 grid gap-1 font-mono">
              <div>document_id: {result.citation.document_id}</div>
              <div>version_id: {result.citation.document_version_id}</div>
              <div>chunk_id: {result.citation.chunk_id}</div>
              <div>sha256: {result.citation.content_sha256}</div>
            </dl>
          </details>
        </article>
      ))}
    </div>
  );
}

function Empty({ copy }: { copy: Copy }) {
  return (
    <div className="card p-8 text-center text-sm text-[var(--color-muted)]">
      {copy.empty}
    </div>
  );
}

function Loading({ copy }: { copy: Copy }) {
  return (
    <div className="card animate-pulse p-8 text-sm text-[var(--color-muted)]">
      {copy.loading}
    </div>
  );
}

function Select({
  label,
  name,
  children,
}: {
  label: string;
  name: string;
  children: React.ReactNode;
}) {
  return (
    <label className="label">
      {label}
      <select
        className="field mt-2"
        name={name}
        defaultValue={name === "top_k" ? "5" : undefined}
      >
        {children}
      </select>
    </label>
  );
}

const english = {
  parameters: "Search parameters",
  agent: "Agent",
  query: "Query",
  language: "Language",
  placeholder: "Ask a factual question covered by approved knowledge…",
  search: "Run search",
  searching: "Searching…",
  empty: "Enter a query to inspect governed retrieval results.",
  loading: "Embedding the query and searching governed knowledge…",
  denied: "Access denied / binding mismatch",
  deniedHelp:
    "The selected agent is disabled, unavailable, or not authorized for knowledge retrieval.",
  error: "Search error",
  decision: "Evidence decision",
  sufficient: "Relevant evidence found",
  insufficient: "Insufficient evidence",
  threshold: "Threshold",
  duration: "Duration",
  reason: "Reason",
  correlation: "Correlation ID",
  relevant: "Relevant results",
  below: "Below-threshold diagnostic results",
  noCandidates: "No authorized candidates were found.",
};

const chinese: typeof english = {
  parameters: "检索参数",
  agent: "智能体",
  query: "查询",
  language: "语言",
  placeholder: "输入一个可由已批准知识回答的事实问题……",
  search: "执行检索",
  searching: "检索中……",
  empty: "输入查询以检查受治理的检索结果。",
  loading: "正在生成查询向量并检索受治理知识……",
  denied: "访问被拒绝 / 绑定不匹配",
  deniedHelp: "所选智能体未启用、不可用或没有知识检索权限。",
  error: "检索错误",
  decision: "证据判定",
  sufficient: "已找到相关证据",
  insufficient: "证据不足",
  threshold: "阈值",
  duration: "耗时",
  reason: "原因",
  correlation: "关联 ID",
  relevant: "相关结果",
  below: "低于阈值的诊断结果",
  noCandidates: "没有找到已授权的候选内容。",
};

type Copy = typeof english;
