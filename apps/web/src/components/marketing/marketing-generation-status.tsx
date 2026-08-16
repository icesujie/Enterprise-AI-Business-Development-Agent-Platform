"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import type { MarketingGenerationRun } from "@/lib/api";

export function MarketingGenerationStatus({ run, zh }: { run: MarketingGenerationRun; zh: boolean }) {
  const router = useRouter();
  useEffect(() => {
    if (!["queued", "running"].includes(run.status)) return;
    const timer = window.setTimeout(() => router.refresh(), 1500);
    return () => window.clearTimeout(timer);
  }, [router, run.status]);
  const result = run.result;
  return (
    <div className="space-y-6">
      <section className="card p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-xl font-semibold">{zh ? "生成状态" : "Generation status"}</h2>
          <span className="status-badge">{run.status}</span>
        </div>
        <dl className="mt-5 grid gap-4 text-sm sm:grid-cols-2">
          <div><dt className="text-[var(--color-muted)]">{zh ? "证据状态" : "Evidence"}</dt><dd>{run.evidence_status ?? "—"}</dd></div>
          <div><dt className="text-[var(--color-muted)]">{zh ? "模型" : "Provider / model"}</dt><dd>{run.provider ?? "—"} / {run.model ?? "—"}</dd></div>
          <div><dt className="text-[var(--color-muted)]">Correlation ID</dt><dd className="break-all">{run.correlation_id}</dd></div>
          <div><dt className="text-[var(--color-muted)]">{zh ? "耗时" : "Latency"}</dt><dd>{run.duration_ms ? `${run.duration_ms} ms` : "—"}</dd></div>
        </dl>
      </section>
      {result?.outcome === "insufficient_evidence" ? (
        <section className="rounded-xl bg-[var(--color-warning-soft)] p-6">
          <h2 className="font-semibold">{zh ? "证据不足，未生成草稿" : "Insufficient evidence — no draft generated"}</h2>
          <p className="mt-2 text-sm">{result.message}</p>
        </section>
      ) : null}
      {result?.content ? (
        <section className="card p-6">
          <h2 className="text-xl font-semibold">{zh ? "结构化草稿" : "Structured draft"}</h2>
          <pre className="mt-4 overflow-x-auto whitespace-pre-wrap text-sm">{JSON.stringify(result.content, null, 2)}</pre>
          {result.asset_id ? <Link className="button-primary mt-5 inline-flex" href={`/marketing-content/${result.asset_id}`}>{zh ? "进入人工审核" : "Open human review"}</Link> : null}
        </section>
      ) : null}
      {result?.citations?.length ? (
        <section className="card p-6">
          <h2 className="text-xl font-semibold">{zh ? "知识来源" : "Knowledge references"}</h2>
          <div className="mt-4 space-y-3">{result.citations.map((citation, index) => <div className="rounded-lg border border-[var(--color-line)] p-4 text-sm" key={String(citation.chunk_id)}><strong>[{index + 1}] {String(citation.document_name)}</strong><div className="mt-1 text-[var(--color-muted)]">v{String(citation.document_version)} · {String(citation.section ?? "—")} · score {String(citation.similarity_score)}</div><div className="mt-1 break-all text-xs">chunk {String(citation.chunk_id)}</div></div>)}</div>
        </section>
      ) : null}
      {run.status === "failed" ? <p className="rounded-xl bg-[var(--color-danger-soft)] p-5 text-sm">{run.error_message ?? (zh ? "生成失败。" : "Generation failed.")}</p> : null}
    </div>
  );
}
