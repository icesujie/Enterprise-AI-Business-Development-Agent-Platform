"use client";

import { useState, type FormEvent } from "react";

import {
  getKnowledgeAssistantRun,
  startKnowledgeAssistantRun,
} from "@/app/(workspace)/knowledge/assistant/actions";
import { Button } from "@/components/ui/button";
import type {
  KnowledgeAssistantEvidence,
  KnowledgeAssistantRun,
} from "@/lib/api";

type Language = "en" | "zh-CN";

const AGENT_ID = "61000000-0000-4000-8000-000000000001";

export function KnowledgeAssistant({
  initialLanguage,
}: {
  initialLanguage: Language;
}) {
  const [language, setLanguage] = useState<Language>(initialLanguage);
  const [question, setQuestion] = useState("");
  const [run, setRun] = useState<KnowledgeAssistantRun | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const copy = language === "zh-CN" ? chinese : english;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setRun(null);
    setError(null);
    try {
      const started = await startKnowledgeAssistantRun({
        agent_id: AGENT_ID,
        language,
        question,
      });
      for (let attempt = 0; attempt < 45; attempt += 1) {
        await delay(attempt === 0 ? 250 : 800);
        const current = await getKnowledgeAssistantRun(started.run_id);
        setRun(current);
        if (["succeeded", "failed", "cancelled"].includes(current.status)) {
          if (current.status !== "succeeded") {
            setError(current.error_message || copy.failed);
          }
          return;
        }
      }
      setError(copy.timeout);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : copy.failed);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(340px,0.72fr)_minmax(0,1.28fr)]">
      <form className="card h-fit p-6 sm:p-7" onSubmit={submit}>
        <div className="rounded-xl bg-[var(--color-info-soft)] p-4 text-sm text-[var(--color-info)]">
          {copy.notice}
        </div>
        <label className="label mt-6">
          {copy.agent}
          <select className="field mt-2" disabled value={AGENT_ID}>
            <option value={AGENT_ID}>{copy.kitchen}</option>
          </select>
        </label>
        <label className="label mt-5">
          {copy.language}
          <select
            className="field mt-2"
            value={language}
            onChange={(event) => setLanguage(event.target.value as Language)}
          >
            <option value="en">English</option>
            <option value="zh-CN">中文</option>
          </select>
        </label>
        <label className="label mt-5">
          {copy.question}
          <textarea
            className="field mt-2 min-h-40 resize-y"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            minLength={3}
            maxLength={2000}
            placeholder={copy.placeholder}
            required
          />
        </label>
        <Button className="mt-6 w-full" type="submit" disabled={pending}>
          {pending ? copy.running : copy.ask}
        </Button>
        {error ? (
          <p
            className="mt-4 rounded-xl bg-[var(--color-danger-soft)] p-4 text-sm text-[var(--color-danger)]"
            role="alert"
          >
            {error}
          </p>
        ) : null}
      </form>

      <section className="space-y-5" aria-live="polite">
        {!run && !pending ? <Empty text={copy.empty} /> : null}
        {pending && !run ? <Empty text={copy.loading} loading /> : null}
        {run?.result ? <Answer run={run} copy={copy} /> : null}
      </section>
    </div>
  );
}

function Answer({ run, copy }: { run: KnowledgeAssistantRun; copy: Copy }) {
  const result = run.result;
  if (!result) return null;
  const tone =
    result.evidence_status === "sufficient"
      ? "border-l-emerald-700"
      : result.evidence_status === "conflicting"
        ? "border-l-red-700"
        : "border-l-amber-600";
  return (
    <>
      <article className={`card border-l-4 p-6 sm:p-7 ${tone}`}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--color-muted)]">
              {copy.status}
            </p>
            <h2 className="mt-1 text-xl font-semibold">
              {copy[result.evidence_status]}
            </h2>
          </div>
          <div className="text-right text-xs text-[var(--color-muted)]">
            <p>{run.provider_type ?? result.model_provider}</p>
            <p>{run.duration_ms?.toFixed(1) ?? "—"} ms</p>
          </div>
        </div>
        <p className="mt-5 whitespace-pre-wrap text-sm leading-7">
          {result.answer}
        </p>
        <p className="mt-5 border-t border-[var(--color-line)] pt-3 text-xs text-[var(--color-muted)]">
          {copy.correlation}: {run.correlation_id ?? "—"}
        </p>
      </article>

      <section className="card p-6">
        <h2 className="text-lg font-semibold">
          {copy.citations} ({result.citations.length})
        </h2>
        <div className="mt-4 space-y-3">
          {result.citations.map((citation, index) => (
            <div
              className="rounded-xl border border-[var(--color-line)] p-4"
              key={citation.chunk_id}
            >
              <p className="text-sm font-semibold">
                [{index + 1}] {citation.document_name} · v
                {citation.document_version}
              </p>
              <p className="mt-1 text-xs text-[var(--color-muted)]">
                {citation.section ?? "—"} · {copy.page}{" "}
                {citation.page_number ?? "—"} ·{" "}
                {citation.similarity_score.toFixed(6)}
              </p>
              <p className="mt-2 break-all font-mono text-[0.68rem] text-[var(--color-muted)]">
                {citation.chunk_id}
              </p>
            </div>
          ))}
          {!result.citations.length ? (
            <p className="text-sm text-[var(--color-muted)]">
              {copy.noCitations}
            </p>
          ) : null}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--color-muted)]">
          {copy.sources} ({result.evidence.length})
        </h2>
        {result.evidence.map((item) => (
          <EvidenceCard key={item.chunk_id} item={item} copy={copy} />
        ))}
      </section>
    </>
  );
}

function EvidenceCard({
  item,
  copy,
}: {
  item: KnowledgeAssistantEvidence;
  copy: Copy;
}) {
  return (
    <details className="card p-5">
      <summary className="cursor-pointer list-none">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="font-semibold">
              {item.document_name} · v{item.document_version}
            </p>
            <p className="mt-1 text-xs text-[var(--color-muted)]">
              {item.section ?? "—"} · {copy.page} {item.page_number ?? "—"}
            </p>
          </div>
          <span className="status-chip font-mono">
            {item.similarity_score.toFixed(6)}
          </span>
        </div>
      </summary>
      <p className="mt-4 whitespace-pre-wrap border-t border-[var(--color-line)] pt-4 text-sm leading-6">
        {item.content}
      </p>
    </details>
  );
}

function Empty({ text, loading = false }: { text: string; loading?: boolean }) {
  return (
    <div
      className={`card p-10 text-center text-sm text-[var(--color-muted)] ${loading ? "animate-pulse" : ""}`}
    >
      {text}
    </div>
  );
}

const english = {
  notice:
    "Read-only · Approved knowledge only · No CRM writes or external actions",
  agent: "Agent",
  kitchen: "Commercial Kitchen Agent",
  language: "Answer language",
  question: "Question",
  placeholder:
    "Ask about approved company, product, case, or delivery knowledge…",
  ask: "Ask Knowledge Assistant",
  running: "Checking evidence…",
  failed: "The assistant failed safely.",
  timeout:
    "The answer is taking longer than expected. The durable run remains available.",
  empty:
    "Ask a question to receive a cited answer or an explicit evidence limitation.",
  loading: "Authorizing, retrieving, and validating approved knowledge…",
  status: "Evidence status",
  sufficient: "Sufficient evidence",
  insufficient: "Insufficient evidence",
  conflicting: "Conflicting evidence",
  citations: "Validated citations",
  noCitations: "No citations are available for this response.",
  sources: "Source excerpts",
  correlation: "Correlation ID",
  page: "page",
};

const chinese: typeof english = {
  notice: "只读 · 仅使用已批准知识 · 不写入 CRM，也不执行外部动作",
  agent: "智能体",
  kitchen: "商用厨房智能体",
  language: "回答语言",
  question: "问题",
  placeholder: "询问已批准的公司、产品、案例或交付知识……",
  ask: "询问知识助手",
  running: "正在检查证据……",
  failed: "知识助手已安全失败。",
  timeout: "回答时间超过预期，但持久化运行记录仍然保留。",
  empty: "输入问题后，系统将提供带引用的回答或明确说明证据限制。",
  loading: "正在授权、检索并验证已批准知识……",
  status: "证据状态",
  sufficient: "证据充分",
  insufficient: "证据不足",
  conflicting: "证据冲突",
  citations: "已验证引用",
  noCitations: "本次回答没有可用引用。",
  sources: "来源摘录",
  correlation: "关联 ID",
  page: "页码",
};

type Copy = typeof english;

function delay(milliseconds: number) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}
