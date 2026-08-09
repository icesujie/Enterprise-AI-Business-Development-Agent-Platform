import Link from "next/link";

import {
  apiFetch,
  type Activity,
  type Opportunity,
  type Organization,
} from "@/lib/api";

import { transitionOpportunity } from "../../actions";

const transitions: Record<string, string[]> = {
  discovery: ["requirements_confirmed", "lost"],
  requirements_confirmed: ["discovery", "proposal", "lost"],
  proposal: ["requirements_confirmed", "negotiation", "lost"],
  negotiation: ["proposal", "won", "lost"],
  won: [],
  lost: [],
};

export default async function OpportunityDetailPage({
  params,
}: PageProps<"/opportunities/[id]">) {
  const { id } = await params;
  const opportunity = await apiFetch<Opportunity>(
    `/api/v1/opportunities/${id}`,
  );
  const [organization, activities] = await Promise.all([
    apiFetch<Organization>(
      `/api/v1/organizations/${opportunity.organization_id}`,
    ),
    apiFetch<Activity[]>(`/api/v1/opportunities/${id}/activities`),
  ]);
  const nextStages = transitions[opportunity.stage] ?? [];

  return (
    <div>
      <Link
        href="/opportunities"
        className="text-sm font-semibold text-[var(--accent)]"
      >
        ← Back to opportunities
      </Link>
      <header className="mt-5 flex flex-wrap items-start justify-between gap-5">
        <div>
          <p className="eyebrow">{organization.display_name}</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">
            {opportunity.name}
          </h1>
          <p className="mt-3 text-sm text-[var(--muted)]">
            {opportunity.currency} {formatAmount(opportunity.estimated_value)} ·{" "}
            {opportunity.probability}% probability · Version{" "}
            {opportunity.version}
          </p>
        </div>
        <div className="flex gap-2">
          <span className="status-chip">
            {opportunity.stage.replaceAll("_", " ")}
          </span>
          <span className="status-chip">{opportunity.status}</span>
        </div>
      </header>

      <div className="mt-7 grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <section className="card p-7">
            <p className="eyebrow">Project snapshot</p>
            <dl className="mt-5 grid gap-5 sm:grid-cols-2">
              <Detail label="Company" value={organization.display_name} />
              <Detail
                label="Expected close"
                value={
                  opportunity.expected_close_date
                    ? formatDate(opportunity.expected_close_date)
                    : "Not set"
                }
              />
              {Object.entries(opportunity.requirements)
                .filter(([, value]) => value)
                .map(([key, value]) => (
                  <Detail
                    key={key}
                    label={key.replaceAll("_", " ")}
                    value={String(value)}
                  />
                ))}
            </dl>
          </section>

          <section className="card p-7">
            <p className="eyebrow">Audit trail</p>
            <h2 className="mt-2 text-xl font-semibold">Opportunity history</h2>
            <ol className="timeline mt-7">
              {activities.map((activity) => (
                <li key={activity.id} className="timeline-item">
                  <div className="flex flex-wrap items-center gap-2">
                    <strong className="text-sm">{activity.subject}</strong>
                    <span className="status-chip">
                      {activity.activity_type.replaceAll("_", " ")}
                    </span>
                  </div>
                  {activity.description ? (
                    <p className="mt-2 text-sm text-[var(--muted)]">
                      {activity.description}
                    </p>
                  ) : null}
                  <p className="mt-2 text-xs text-[var(--muted)]">
                    {formatDateTime(activity.occurred_at)}
                  </p>
                </li>
              ))}
            </ol>
          </section>
        </div>

        <aside className="space-y-6">
          <section className="card p-6">
            <p className="eyebrow">Stage control</p>
            <h2 className="mt-3 text-xl font-semibold">Move the deal</h2>
            {nextStages.length ? (
              <div className="mt-5 space-y-3">
                {nextStages
                  .filter((stage) => stage !== "lost")
                  .map((stage) => {
                    const action = transitionOpportunity.bind(
                      null,
                      opportunity.id,
                      opportunity.version,
                      stage,
                    );
                    return (
                      <form key={stage} action={action}>
                        <button className="button-primary w-full capitalize">
                          Move to {stage.replaceAll("_", " ")}
                        </button>
                      </form>
                    );
                  })}
                {nextStages.includes("lost") ? (
                  <form
                    action={transitionOpportunity.bind(
                      null,
                      opportunity.id,
                      opportunity.version,
                      "lost",
                    )}
                    className="rounded-xl border border-[var(--line)] p-4"
                  >
                    <label className="label">
                      Loss reason
                      <textarea
                        className="field mt-2 min-h-20"
                        name="reason"
                        required
                      />
                    </label>
                    <button className="button-secondary mt-3 w-full">
                      Mark as lost
                    </button>
                  </form>
                ) : null}
              </div>
            ) : (
              <p className="mt-4 text-sm leading-6 text-[var(--muted)]">
                This opportunity is closed. Its final stage cannot be changed in
                the MVP.
              </p>
            )}
          </section>
          <section className="card p-6">
            <p className="eyebrow">Control boundary</p>
            <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
              Stage changes are explicit human actions. The API rejects skipped
              stages, stale edits, and losses without a recorded reason.
            </p>
          </section>
        </aside>
      </div>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
        {label}
      </dt>
      <dd className="mt-2 text-sm font-semibold">{value}</dd>
    </div>
  );
}

function formatAmount(value: string) {
  return new Intl.NumberFormat("en", { maximumFractionDigits: 0 }).format(
    Number(value),
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(
    new Date(`${value}T00:00:00Z`),
  );
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
