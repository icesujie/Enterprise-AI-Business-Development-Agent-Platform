import Link from "next/link";

import { StatusBadge } from "@/components/ui/status";
import type {
  Contact,
  Lead,
  LeadAssessment,
  QualificationRun,
} from "@/lib/api";
import { formatDateTime } from "@/lib/workspace-format";

type ServerAction = () => Promise<void>;

export function QualificationCard({
  lead,
  contact,
  assessment,
  history,
  run,
  runAction,
  approveAction,
  rejectAction,
}: {
  lead: Lead;
  contact?: Contact | null;
  assessment?: LeadAssessment;
  history: LeadAssessment[];
  run?: QualificationRun;
  runAction: ServerAction;
  approveAction?: ServerAction;
  rejectAction?: ServerAction;
}) {
  if (!assessment) {
    return <AgentRunStatus lead={lead} run={run} runAction={runAction} />;
  }

  const score = Math.round(Number(assessment.score));
  const confidence = confidenceDetails(Number(assessment.confidence));
  const dimensions = [
    {
      label: "Need and project fit",
      weight: "35%",
      status: assessment.qualification.need_status,
      evidence:
        [lead.project_type, lead.expected_capacity]
          .filter(Boolean)
          .join(" · ") || "No structured need evidence saved",
    },
    {
      label: "Timeline",
      weight: "25%",
      status: assessment.qualification.timeline_status,
      evidence: lead.target_timeline || "No target timeline saved",
    },
    {
      label: "Budget",
      weight: "20%",
      status: assessment.qualification.budget_status,
      evidence:
        lead.estimated_value && lead.currency
          ? `${lead.currency} ${Number(lead.estimated_value).toLocaleString("en")}`
          : "No budget value saved",
    },
    {
      label: "Authority",
      weight: "20%",
      status: assessment.qualification.authority_status,
      evidence: contact?.job_title || "Decision role has not been confirmed",
    },
  ];

  return (
    <div className="space-y-6">
      <section className="card overflow-hidden">
        <div className="border-b border-[var(--color-line)] bg-[var(--color-brand-strong)] p-6 text-white sm:p-7">
          <div className="flex flex-wrap items-start justify-between gap-5">
            <div>
              <AISourceLabel />
              <div className="mt-5 flex items-end gap-3">
                <p className="text-5xl font-semibold tabular-nums">{score}</p>
                <p className="pb-1 text-sm text-white/55">/ 100</p>
              </div>
              <p className="mt-2 text-sm text-white/65">
                {score >= 75
                  ? "Strong qualification signals"
                  : score >= 45
                    ? "Promising, with evidence gaps"
                    : "More discovery is required"}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <StatusBadge tone={tierTone(assessment.tier)}>
                {capitalize(assessment.tier)}
              </StatusBadge>
              <StatusBadge tone={reviewTone(assessment.review_status)}>
                Review {assessment.review_status.replaceAll("_", " ")}
              </StatusBadge>
            </div>
          </div>
          <ScoreBar score={score} />
        </div>

        <div className="p-6 sm:p-7">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <ConfidenceBadge
              label={confidence.label}
              explanation={confidence.explanation}
            />
            <p className="text-xs text-[var(--color-muted)]">
              Assessment v{assessment.assessment_version} ·{" "}
              {formatDateTime(assessment.created_at)}
            </p>
          </div>

          <div className="mt-7 grid gap-7 lg:grid-cols-[1.1fr_0.9fr]">
            <div>
              <p className="eyebrow">Business summary</p>
              <p className="mt-3 text-base leading-7">
                {assessment.need_summary ||
                  "The assessment did not provide a need summary."}
              </p>
            </div>
            <div className="rounded-xl bg-[var(--color-surface-subtle)] p-5">
              <p className="text-xs font-bold uppercase tracking-[0.13em] text-[var(--color-muted)]">
                Recommended next action
              </p>
              <p className="mt-3 text-sm font-semibold leading-6">
                {assessment.recommended_action}
              </p>
            </div>
          </div>

          <div className="mt-8 border-t border-[var(--color-line)] pt-6">
            <h3 className="font-semibold">Qualification dimensions</h3>
            <div className="mt-4 divide-y divide-[var(--color-line)]">
              {dimensions.map((dimension) => (
                <QualificationDimensionRow
                  key={dimension.label}
                  {...dimension}
                />
              ))}
            </div>
          </div>

          <MissingInformationList items={assessment.missing_information} />

          <div className="mt-7 rounded-xl border border-[var(--color-line)] p-5">
            <p className="text-sm font-semibold">Human decision required</p>
            <p className="mt-2 text-sm leading-6 text-[var(--color-muted)]">
              Accepting this assessment records the AI score only. It does not
              qualify, convert, price, or contact the lead.
            </p>
            {assessment.review_status === "pending" &&
            approveAction &&
            rejectAction ? (
              <div className="mt-4 flex flex-col gap-2 sm:flex-row">
                <form action={approveAction}>
                  <button className="button-primary w-full sm:w-auto">
                    Accept assessment
                  </button>
                </form>
                <form action={rejectAction}>
                  <button className="button-secondary w-full sm:w-auto">
                    Reject assessment
                  </button>
                </form>
              </div>
            ) : (
              <form action={runAction} className="mt-4">
                <button className="button-secondary w-full sm:w-auto">
                  Run a new assessment
                </button>
              </form>
            )}
          </div>
        </div>
      </section>

      {history.length > 1 ? (
        <section className="card p-6 sm:p-7">
          <h2 className="font-semibold">Assessment history</h2>
          <div className="mt-4 divide-y divide-[var(--color-line)]">
            {history.slice(1).map((item) => (
              <div
                key={item.id}
                className="flex flex-wrap items-center justify-between gap-3 py-4 text-sm"
              >
                <div>
                  <p className="font-semibold">
                    Version {item.assessment_version} · {item.score}/100 ·{" "}
                    {capitalize(item.tier)}
                  </p>
                  <p className="mt-1 text-xs text-[var(--color-muted)]">
                    {formatDateTime(item.created_at)}
                  </p>
                </div>
                <StatusBadge tone={reviewTone(item.review_status)}>
                  {item.review_status.replaceAll("_", " ")}
                </StatusBadge>
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

export function AISourceLabel() {
  return (
    <p className="text-xs font-bold uppercase tracking-[0.17em] text-[#d7a58e]">
      AI-generated assessment · Human review required
    </p>
  );
}

export function ScoreBar({ score }: { score: number }) {
  const width = Math.min(100, Math.max(0, score));
  return (
    <div className="mt-5">
      <div
        className="h-2 overflow-hidden rounded-full bg-white/12"
        role="progressbar"
        aria-label={`Qualification score ${score} out of 100`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={score}
      >
        <div
          className="h-full rounded-full bg-[#d18867]"
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}

export function ConfidenceBadge({
  label,
  explanation,
}: {
  label: string;
  explanation: string;
}) {
  return (
    <div>
      <p className="text-sm font-semibold">{label} confidence</p>
      <p className="mt-1 text-xs text-[var(--color-muted)]">{explanation}</p>
    </div>
  );
}

export function QualificationDimensionRow({
  label,
  weight,
  status,
  evidence,
}: {
  label: string;
  weight: string;
  status: unknown;
  evidence: string;
}) {
  const normalized = typeof status === "string" ? status : "unknown";
  return (
    <div className="grid gap-3 py-4 sm:grid-cols-[1fr_110px_1.4fr] sm:items-center">
      <div>
        <p className="text-sm font-semibold">{label}</p>
        <p className="mt-1 text-xs text-[var(--color-muted)]">
          Weight {weight}
        </p>
      </div>
      <StatusBadge tone={dimensionTone(normalized)}>
        {capitalize(normalized)}
      </StatusBadge>
      <p className="text-sm leading-6 text-[var(--color-muted)]">{evidence}</p>
    </div>
  );
}

export function MissingInformationList({ items }: { items: string[] }) {
  if (!items.length) return null;
  return (
    <div className="mt-7 rounded-xl border border-[var(--color-warning)]/25 bg-[var(--color-warning-soft)] p-5">
      <h3 className="text-sm font-semibold">Information to confirm</h3>
      <ul className="mt-3 grid gap-2 text-sm text-[var(--color-muted)] sm:grid-cols-2">
        {items.map((item) => (
          <li key={item} className="flex gap-2">
            <span aria-hidden>□</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function AgentRunStatus({
  lead,
  run,
  runAction,
}: {
  lead: Lead;
  run?: QualificationRun;
  runAction: ServerAction;
}) {
  const inProgress = run?.status === "queued" || run?.status === "running";
  const failed = run?.status === "failed";
  return (
    <section className="card p-7" aria-live="polite">
      <AISourceLabel />
      <h2 className="mt-4 text-2xl font-semibold">
        {inProgress
          ? "Qualification is in progress"
          : failed
            ? "Qualification could not be completed"
            : "Qualification has not been run"}
      </h2>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--color-muted)]">
        {inProgress
          ? `The run is ${run.status}. You can leave this page; the result will remain attached to the lead.`
          : failed
            ? run.error_message ||
              "The AI service returned a safe failure. Manual qualification remains available."
            : "AI can summarize project fit, timeline, budget evidence, authority, missing information, and a recommended next action."}
      </p>
      {inProgress ? (
        <Link
          href={`/leads/${lead.id}?tab=qualification`}
          className="button-secondary mt-5"
        >
          Refresh status
        </Link>
      ) : (
        <form action={runAction} className="mt-5">
          <button className="button-primary">
            {failed ? "Retry qualification" : "Run AI qualification"}
          </button>
        </form>
      )}
      <p className="mt-5 text-xs leading-5 text-[var(--color-muted)]">
        The UI displays structured business output only. Hidden model reasoning
        is never shown.
      </p>
    </section>
  );
}

function confidenceDetails(value: number) {
  if (value >= 0.75)
    return {
      label: "High",
      explanation: "Most scoring inputs have supporting saved information.",
    };
  if (value >= 0.5)
    return {
      label: "Medium",
      explanation: "Some important evidence is incomplete or indirect.",
    };
  return {
    label: "Low",
    explanation: "Treat the result as a discovery prompt, not a decision.",
  };
}

function tierTone(tier: string): "success" | "warning" | "neutral" {
  return tier === "hot" ? "success" : tier === "warm" ? "warning" : "neutral";
}

function reviewTone(
  status: string,
): "success" | "danger" | "warning" | "neutral" {
  if (status === "approved") return "success";
  if (status === "rejected") return "danger";
  if (status === "pending") return "warning";
  return "neutral";
}

function dimensionTone(status: string): "success" | "warning" | "neutral" {
  if (status === "confirmed") return "success";
  if (status === "partial") return "warning";
  return "neutral";
}

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1).replaceAll("_", " ");
}
