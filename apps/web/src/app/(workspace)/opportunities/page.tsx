import Link from "next/link";

import { StatusBadge } from "@/components/ui/status";
import { PageHeader } from "@/components/workspace/page-header";
import {
  apiFetch,
  type Opportunity,
  type OpportunityList,
  type Organization,
} from "@/lib/api";
import {
  formatDate,
  formatMoney,
  groupOpportunityValue,
  opportunityStageLabels,
} from "@/lib/workspace-format";

const openStages = [
  "discovery",
  "requirements_confirmed",
  "proposal",
  "negotiation",
] as const;

export default async function OpportunitiesPage({
  searchParams,
}: PageProps<"/opportunities">) {
  const query = await searchParams;
  const view = single(query.view) === "list" ? "list" : "pipeline";
  const [data, organizations] = await Promise.all([
    apiFetch<OpportunityList>("/api/v1/opportunities?limit=100"),
    apiFetch<Organization[]>("/api/v1/organizations?limit=100"),
  ]);
  const companies = new Map(
    organizations.map((organization) => [
      organization.id,
      organization.display_name,
    ]),
  );
  const openItems = data.items.filter((item) => item.status === "open");
  const won = data.items.filter((item) => item.stage === "won");
  const lost = data.items.filter((item) => item.stage === "lost");
  const totals = groupOpportunityValue(openItems);

  return (
    <div>
      <PageHeader
        eyebrow="Commercial pipeline"
        title="Opportunities"
        description="Track qualified kitchen projects through explicit sales stages. Every stage change remains a human action confirmed by the API."
        actions={
          <div className="rounded-2xl border border-[var(--color-line)] bg-white px-5 py-3 text-right shadow-sm">
            <p className="text-[0.65rem] font-bold uppercase tracking-[0.12em] text-[var(--color-muted)]">
              Open pipeline
            </p>
            <p className="mt-1 text-sm font-semibold">
              {totals.join(" · ") || "No open value"}
            </p>
          </div>
        }
      />

      <div className="mt-7 flex flex-wrap items-center justify-between gap-4 border-b border-[var(--color-line)] pb-4">
        <div className="flex gap-2" role="group" aria-label="Opportunity view">
          <Link
            href="/opportunities"
            aria-current={view === "pipeline" ? "page" : undefined}
            className={
              view === "pipeline" ? "button-primary" : "button-tertiary"
            }
          >
            Pipeline
          </Link>
          <Link
            href="/opportunities?view=list"
            aria-current={view === "list" ? "page" : undefined}
            className={view === "list" ? "button-primary" : "button-tertiary"}
          >
            List
          </Link>
        </div>
        <p className="text-sm text-[var(--color-muted)]">
          {openItems.length} open · {won.length} won · {lost.length} lost
        </p>
      </div>

      {view === "pipeline" ? (
        <PipelineView items={openItems} companies={companies} />
      ) : (
        <ListView items={data.items} companies={companies} />
      )}

      <section className="mt-6 grid gap-4 sm:grid-cols-2">
        <ClosedStage label="Won" items={won} tone="success" />
        <ClosedStage label="Lost" items={lost} tone="danger" />
      </section>
    </div>
  );
}

function PipelineView({
  items,
  companies,
}: {
  items: Opportunity[];
  companies: Map<string, string>;
}) {
  return (
    <div className="mt-6 overflow-x-auto pb-3">
      <div className="grid min-w-[1120px] grid-cols-4 gap-4">
        {openStages.map((stage) => {
          const stageItems = items.filter((item) => item.stage === stage);
          const totals = groupOpportunityValue(stageItems);
          return (
            <section
              key={stage}
              className="min-h-80 rounded-2xl bg-[#e5e8e1] p-3"
            >
              <header className="px-2 pb-3 pt-1">
                <div className="flex items-center justify-between gap-3">
                  <h2 className="text-sm font-semibold">
                    {opportunityStageLabels[stage]}
                  </h2>
                  <span className="grid h-7 min-w-7 place-items-center rounded-full bg-white px-2 text-xs font-bold">
                    {stageItems.length}
                  </span>
                </div>
                <p className="mt-2 min-h-5 text-xs text-[var(--color-muted)]">
                  {totals.join(" · ") || "No value"}
                </p>
              </header>
              <div className="space-y-3">
                {stageItems.length ? (
                  stageItems.map((item) => (
                    <OpportunityCard
                      key={item.id}
                      item={item}
                      company={companies.get(item.organization_id)}
                    />
                  ))
                ) : (
                  <p className="rounded-xl border border-dashed border-[#bcc5bc] p-5 text-center text-xs text-[var(--color-muted)]">
                    No opportunities in this stage
                  </p>
                )}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}

function OpportunityCard({
  item,
  company,
}: {
  item: Opportunity;
  company?: string;
}) {
  return (
    <Link
      href={`/opportunities/${item.id}`}
      className="block rounded-xl border border-[var(--color-line)] bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
    >
      <p className="text-xs font-semibold text-[var(--color-muted)]">
        {company ?? "Company record"}
      </p>
      <h3 className="mt-2 font-semibold leading-6">{item.name}</h3>
      <p className="mt-4 text-sm font-semibold">
        {formatMoney(item.estimated_value, item.currency)}
      </p>
      <div className="mt-4 flex items-center justify-between gap-3 text-xs text-[var(--color-muted)]">
        <span>{Math.round(Number(item.probability))}% probability</span>
        <span>
          {item.expected_close_date
            ? formatDate(item.expected_close_date)
            : "No close date"}
        </span>
      </div>
    </Link>
  );
}

function ListView({
  items,
  companies,
}: {
  items: Opportunity[];
  companies: Map<string, string>;
}) {
  return (
    <section className="card mt-6 overflow-hidden">
      <div className="hidden grid-cols-[minmax(220px,1.3fr)_minmax(150px,0.8fr)_150px_150px_120px] gap-4 border-b border-[var(--color-line)] bg-[var(--color-surface-subtle)] px-5 py-3 text-[0.68rem] font-bold uppercase tracking-[0.12em] text-[var(--color-muted)] lg:grid">
        <span>Opportunity</span>
        <span>Company</span>
        <span>Stage</span>
        <span>Value</span>
        <span>Expected close</span>
      </div>
      {items.length ? (
        <div className="divide-y divide-[var(--color-line)]">
          {items.map((item) => (
            <Link
              key={item.id}
              href={`/opportunities/${item.id}`}
              className="grid gap-3 px-5 py-5 transition hover:bg-[var(--color-surface-subtle)] lg:grid-cols-[minmax(220px,1.3fr)_minmax(150px,0.8fr)_150px_150px_120px] lg:items-center"
            >
              <p className="font-semibold">{item.name}</p>
              <p className="text-sm text-[var(--color-muted)]">
                {companies.get(item.organization_id) ?? "Company record"}
              </p>
              <StatusBadge
                tone={
                  item.status === "won"
                    ? "success"
                    : item.status === "lost"
                      ? "danger"
                      : "neutral"
                }
              >
                {opportunityStageLabels[item.stage] ?? item.stage}
              </StatusBadge>
              <p className="text-sm font-semibold">
                {formatMoney(item.estimated_value, item.currency)}
              </p>
              <p className="text-sm text-[var(--color-muted)]">
                {item.expected_close_date
                  ? formatDate(item.expected_close_date)
                  : "Not set"}
              </p>
            </Link>
          ))}
        </div>
      ) : (
        <p className="p-8 text-sm text-[var(--color-muted)]">
          Qualified leads converted to opportunities will appear here.
        </p>
      )}
    </section>
  );
}

function ClosedStage({
  label,
  items,
  tone,
}: {
  label: string;
  items: Opportunity[];
  tone: "success" | "danger";
}) {
  return (
    <div className="card flex items-center justify-between gap-4 p-5">
      <div>
        <p className="text-sm font-semibold">{label}</p>
        <p className="mt-1 text-xs text-[var(--color-muted)]">
          {groupOpportunityValue(items).join(" · ") || "No closed value"}
        </p>
      </div>
      <StatusBadge tone={tone}>{items.length} records</StatusBadge>
    </div>
  );
}

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
}
