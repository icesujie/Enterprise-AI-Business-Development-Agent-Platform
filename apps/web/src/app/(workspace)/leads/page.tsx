import Link from "next/link";

import { ButtonLink } from "@/components/ui/button";
import { LeadStatus, PriorityStatus } from "@/components/workspace/lead-status";
import { PageHeader } from "@/components/workspace/page-header";
import {
  apiFetch,
  type Lead,
  type LeadList,
  type Organization,
} from "@/lib/api";
import { formatDate, leadProjectLabel } from "@/lib/workspace-format";

const views = [
  ["All", ""],
  ["New", "new"],
  ["Qualifying", "qualifying"],
  ["Qualified", "qualified"],
  ["Converted", "converted"],
] as const;

export default async function LeadsPage({ searchParams }: PageProps<"/leads">) {
  const query = await searchParams;
  const search = single(query.search);
  const status = single(query.status);
  const priority = single(query.priority);
  const cursor = single(query.cursor);
  const apiQuery = new URLSearchParams({ limit: "25" });
  if (search) apiQuery.set("search", search);
  if (status) apiQuery.set("status", status);
  if (priority) apiQuery.set("priority", priority);
  if (cursor) apiQuery.set("cursor", cursor);

  const [data, organizations] = await Promise.all([
    apiFetch<LeadList>(`/api/v1/leads?${apiQuery}`),
    apiFetch<Organization[]>("/api/v1/organizations?limit=100"),
  ]);
  const companies = new Map(
    organizations.map((organization) => [
      organization.id,
      organization.display_name,
    ]),
  );
  const hasFilters = Boolean(search || status || priority);

  return (
    <div>
      <PageHeader
        eyebrow="Sales work queue"
        title="Leads"
        description="Prioritise incoming kitchen projects, review qualification signals, and keep every inquiry moving toward a clear human decision."
        actions={<ButtonLink href="/leads/new">Create lead</ButtonLink>}
      />

      <nav
        className="mt-7 flex gap-2 overflow-x-auto border-b border-[var(--color-line)] pb-3"
        aria-label="Lead views"
      >
        {views.map(([label, value]) => {
          const active = status === value;
          const href = value ? `/leads?status=${value}` : "/leads";
          return (
            <Link
              key={label}
              href={href}
              aria-current={active ? "page" : undefined}
              className={
                active ? "button-primary shrink-0" : "button-tertiary shrink-0"
              }
            >
              {label}
            </Link>
          );
        })}
      </nav>

      <form
        action="/leads"
        className="mt-5 grid gap-3 rounded-2xl border border-[var(--color-line)] bg-white p-4 md:grid-cols-[minmax(220px,1fr)_180px_180px_auto] md:items-end"
      >
        <label className="label mt-0">
          Search
          <input
            className="field mt-2"
            name="search"
            defaultValue={search}
            placeholder="Project, city, or inquiry text"
          />
        </label>
        <label className="label mt-0">
          Status
          <select className="field mt-2" name="status" defaultValue={status}>
            <option value="">All statuses</option>
            {[
              "new",
              "qualifying",
              "qualified",
              "nurture",
              "disqualified",
              "converted",
              "archived",
            ].map((value) => (
              <option key={value} value={value}>
                {value.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>
        <label className="label mt-0">
          Priority
          <select
            className="field mt-2"
            name="priority"
            defaultValue={priority}
          >
            <option value="">All priorities</option>
            {["urgent", "high", "normal", "low"].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <button className="button-secondary">Apply filters</button>
      </form>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-[var(--color-muted)]">
          Showing {data.items.length} lead{data.items.length === 1 ? "" : "s"}
          {hasFilters ? " for the active filters" : " in the current page"}.
        </p>
        {hasFilters ? (
          <Link href="/leads" className="button-tertiary">
            Clear filters
          </Link>
        ) : null}
      </div>

      <section className="card mt-4 overflow-hidden">
        {data.items.length ? (
          <>
            <div className="hidden grid-cols-[90px_minmax(260px,1.5fr)_minmax(160px,0.8fr)_120px_110px_120px] gap-4 border-b border-[var(--color-line)] bg-[var(--color-surface-subtle)] px-5 py-3 text-[0.68rem] font-bold uppercase tracking-[0.12em] text-[var(--color-muted)] lg:grid">
              <span>Priority</span>
              <span>Project</span>
              <span>Company</span>
              <span>Status</span>
              <span>AI score</span>
              <span>Created</span>
            </div>
            <div className="divide-y divide-[var(--color-line)]">
              {data.items.map((lead) => (
                <LeadRow key={lead.id} lead={lead} companies={companies} />
              ))}
            </div>
          </>
        ) : (
          <div className="grid min-h-72 place-items-center p-8 text-center">
            <div>
              <span
                className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-[var(--color-success-soft)] font-bold text-[var(--color-success)]"
                aria-hidden
              >
                +
              </span>
              <h2 className="mt-4 font-semibold">
                {hasFilters ? "No leads match these filters" : "No leads yet"}
              </h2>
              <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[var(--color-muted)]">
                {hasFilters
                  ? "Clear or adjust the filters to return to the full sales queue."
                  : "Website consultation submissions and manually created inquiries will appear here."}
              </p>
              <ButtonLink
                href={hasFilters ? "/leads" : "/leads/new"}
                className="mt-5"
              >
                {hasFilters ? "Clear filters" : "Create first lead"}
              </ButtonLink>
            </div>
          </div>
        )}
      </section>

      {data.next_cursor ? (
        <div className="mt-5 flex justify-end">
          <Link
            href={nextPageHref({ search, status, priority }, data.next_cursor)}
            className="button-secondary"
          >
            Load older leads
          </Link>
        </div>
      ) : null}
    </div>
  );
}

function LeadRow({
  lead,
  companies,
}: {
  lead: Lead;
  companies: Map<string, string>;
}) {
  const company = lead.organization_id
    ? (companies.get(lead.organization_id) ?? "Company record")
    : "Not linked";
  return (
    <article className="p-5 transition hover:bg-[var(--color-surface-subtle)]">
      <div className="grid gap-4 lg:grid-cols-[90px_minmax(260px,1.5fr)_minmax(160px,0.8fr)_120px_110px_120px] lg:items-center">
        <div>
          <span className="lg:hidden text-[0.65rem] font-bold uppercase tracking-wide text-[var(--color-muted)]">
            Priority
          </span>
          <div className="mt-1 lg:mt-0">
            <PriorityStatus priority={lead.priority} />
          </div>
        </div>
        <div>
          <h2 className="font-semibold leading-6">{leadProjectLabel(lead)}</h2>
          <p className="mt-1 line-clamp-2 text-xs leading-5 text-[var(--color-muted)]">
            {lead.inquiry_summary}
          </p>
          <Link
            href={`/leads/${lead.id}`}
            className="mt-2 inline-block text-xs font-bold text-[var(--color-brand)] lg:hidden"
          >
            View lead →
          </Link>
        </div>
        <div>
          <span className="lg:hidden text-[0.65rem] font-bold uppercase tracking-wide text-[var(--color-muted)]">
            Company
          </span>
          <p className="mt-1 text-sm lg:mt-0">{company}</p>
        </div>
        <LeadStatus status={lead.status} />
        <p className="text-sm font-semibold tabular-nums">
          {lead.qualification_score
            ? `${lead.qualification_score}/100`
            : "Not run"}
        </p>
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm text-[var(--color-muted)]">
            {formatDate(lead.created_at)}
          </p>
          <Link
            href={`/leads/${lead.id}`}
            className="hidden text-xs font-bold text-[var(--color-brand)] lg:inline"
            aria-label={`View lead: ${leadProjectLabel(lead)}`}
          >
            View →
          </Link>
        </div>
      </div>
    </article>
  );
}

function nextPageHref(
  filters: { search: string; status: string; priority: string },
  cursor: string,
) {
  const query = new URLSearchParams();
  if (filters.search) query.set("search", filters.search);
  if (filters.status) query.set("status", filters.status);
  if (filters.priority) query.set("priority", filters.priority);
  query.set("cursor", cursor);
  return `/leads?${query}`;
}

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
}
