import type { MarketingContentEvaluation } from "@/lib/api";

export function MarketingEvaluationPanel({ evaluation, zh }: { evaluation: MarketingContentEvaluation; zh: boolean }) {
  const quality = evaluation.quality_evaluation;
  return (
    <section className="card p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow">{zh ? "内部评估" : "Internal evaluation"}</p>
          <h2 className="mt-2 text-lg font-semibold">{zh ? "营销质量与运行信息" : "Marketing quality and run information"}</h2>
        </div>
        {quality ? <strong className="text-2xl text-[var(--color-brand)]">{quality.overall_score}/100</strong> : null}
      </div>
      <dl className="mt-5 grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
        <Datum label={zh ? "生成结果" : "Outcome"} value={evaluation.generation_outcome ?? "manual"} />
        <Datum label={zh ? "证据状态" : "Evidence"} value={evaluation.evidence_status ?? "—"} />
        <Datum label={zh ? "提供方 / 模型" : "Provider / model"} value={`${evaluation.provider ?? "—"} / ${evaluation.model ?? "—"}`} />
        <Datum label={zh ? "耗时" : "Latency"} value={evaluation.latency_ms == null ? "—" : `${evaluation.latency_ms} ms`} />
        <Datum label="Correlation ID" value={evaluation.correlation_id ?? "—"} />
        <Datum
          label={zh ? "人工修改比例" : "Human edit distance"}
          value={evaluation.human_edit_distance == null ? (zh ? "尚无人工批准后继版本" : "No approved human successor") : `${Math.round(evaluation.human_edit_distance * 100)}%`}
        />
        <Datum label={zh ? "AI 生成版本" : "Generated version"} value={evaluation.generated_version_number == null ? "—" : `v${evaluation.generated_version_number}`} />
        <Datum label={zh ? "人工批准版本" : "Approved human version"} value={evaluation.approved_human_version_number == null ? "—" : `v${evaluation.approved_human_version_number}`} />
        <Datum label={zh ? "引用数量" : "Citations"} value={String(evaluation.citations.length)} />
        <Datum label={zh ? "估算成本" : "Estimated cost"} value={evaluation.estimated_cost ?? (zh ? "提供方未返回" : "Not reported")} />
      </dl>
      {quality ? (
        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {qualityRows(quality, zh).map(([label, score]) => <Score key={label} label={label} score={score} />)}
        </div>
      ) : <p className="mt-5 text-sm text-[var(--color-muted)]">{zh ? "人工内容没有 AI 质量评分。" : "Manual content has no AI quality score."}</p>}
      {quality?.issues.length ? <p className="mt-5 rounded-lg bg-[var(--color-warning-soft)] p-4 text-sm">{zh ? "评估提示" : "Evaluation flags"}: {quality.issues.join(", ")}</p> : null}
      <div className="mt-6 border-t border-[var(--color-line)] pt-5">
        <h3 className="font-semibold">{zh ? "人工反馈" : "Human feedback"}</h3>
        <div className="mt-3 space-y-3">
          {evaluation.feedback.map((item) => <article className="rounded-lg border border-[var(--color-line)] p-4" key={item.id}><p className="text-sm font-semibold">{item.categories.join(" · ")}</p>{item.note ? <p className="mt-2 text-sm">{item.note}</p> : null}<p className="mt-2 text-xs text-[var(--color-muted)]">{new Date(item.created_at).toLocaleString(zh ? "zh-CN" : "en")}</p></article>)}
          {!evaluation.feedback.length ? <p className="text-sm text-[var(--color-muted)]">{zh ? "暂无结构化反馈。" : "No structured feedback yet."}</p> : null}
        </div>
      </div>
    </section>
  );
}

function qualityRows(quality: NonNullable<MarketingContentEvaluation["quality_evaluation"]>, zh: boolean): Array<[string, number]> {
  return [
    [zh ? "品牌契合" : "Brand fit", quality.brand_fit], [zh ? "受众契合" : "Audience fit", quality.audience_fit],
    [zh ? "渠道契合" : "Channel fit", quality.channel_fit], [zh ? "清晰度" : "Clarity", quality.clarity],
    [zh ? "CTA 质量" : "CTA quality", quality.cta_quality], [zh ? "事实依据" : "Factual grounding", quality.factual_grounding],
    [zh ? "重复控制" : "Repetition control", quality.repetition], [zh ? "内容实用性" : "Usefulness", quality.content_usefulness],
    [zh ? "不受支持声明" : "Unsupported claims", quality.unsupported_claims],
  ];
}

function Score({ label, score }: { label: string; score: number }) { return <div className="rounded-lg bg-[var(--color-surface-subtle)] p-4"><div className="flex justify-between gap-3 text-sm"><span>{label}</span><strong>{score}</strong></div><div className="mt-2 h-1.5 rounded-full bg-[var(--color-line)]"><div className="h-full rounded-full bg-[var(--color-brand)]" style={{ width: `${Math.max(0, Math.min(100, score))}%` }} /></div></div>; }
function Datum({ label, value }: { label: string; value: string }) { return <div><dt className="text-xs font-bold uppercase tracking-wide text-[var(--color-muted)]">{label}</dt><dd className="mt-1 break-all">{value}</dd></div>; }
