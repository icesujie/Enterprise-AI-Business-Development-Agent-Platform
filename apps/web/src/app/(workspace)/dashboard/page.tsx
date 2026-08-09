import Link from "next/link";

import { ButtonLink } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/status";
import { LeadStatus, PriorityStatus } from "@/components/workspace/lead-status";
import { MetricCard } from "@/components/workspace/metric-card";
import { PageHeader } from "@/components/workspace/page-header";
import {
  apiFetch,
  type Lead,
  type LeadList,
  type OpportunityList,
  type Organization,
  type Task,
} from "@/lib/api";
import {
  formatCompactDate,
  groupOpportunityValue,
  isTaskOpen,
  isTaskOverdue,
  leadProjectLabel,
  opportunityStageLabels,
} from "@/lib/workspace-format";

export default async function DashboardPage() {
  const [leadData, opportunityData, tasks, organizations] = await Promise.all([
    apiFetch<LeadList>("/api/v1/leads?limit=100"),
    apiFetch<OpportunityList>("/api/v1/opportunities?limit=100"),
    apiFetch<Task[]>("/api/v1/tasks?limit=200"),
    apiFetch<Organization[]>("/api/v1/organizations?limit=100"),
  ]);
  const now = new Date();
  const companyNames = new Map(
    organizations.map((organization) => [
      organization.id,
      organization.display_name,
    ]),
  );
  const newLeads = leadData.items.filter((lead) => lead.status === "new");
  const unassignedLeads = newLeads.filter((lead) => !lead.owner_membership_id);
  const assessedLeads = leadData.items.filter(
    (lead) => lead.qualification_score !== null,
  );
  const overdueTasks = tasks.filter((task) => isTaskOverdue(task, now));
  const openOpportunities = opportunityData.items.filter(
    (item) => item.status === "open",
  );
  const pipelineTotals = groupOpportunityValue(openOpportunities);
  const attention = buildAttentionQueue(
    leadData.items,
    overdueTasks,
    companyNames,
  );
  const nextTasks = tasks
    .filter(isTaskOpen)
    .sort((a, b) => dueTime(a) - dueTime(b))
    .slice(0, 5);

  return (
    <div>
      <PageHeader
        eyebrow={new Intl.DateTimeFormat("en", {
          weekday: "long",
          day: "numeric",
          month: "long",
        }).format(now)}
        title="Sales command centre"
        description="Review new inquiries, qualification signals, follow-up obligations, and open kitchen projects from one working view."
        actions={<ButtonLink href="/leads/new">Create lead</ButtonLink>}
      />

      <div className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="New inquiries"
          value={String(newLeads.length).padStart(2, "0")}
          note={`${unassignedLeads.length} need an owner`}
          href="/leads?status=new"
        />
        <MetricCard
          label="AI assessments accepted"
          value={String(assessedLeads.length).padStart(2, "0")}
          note="Scores remain advisory"
          href="/leads"
          tone="info"
        />
        <MetricCard
          label="Overdue tasks"
          value={String(overdueTasks.length).padStart(2, "0")}
          note="Deterministic due-date queue"
          href="/follow-up?view=overdue"
          tone="warning"
        />
        <MetricCard
          label="Open opportunities"
          value={String(openOpportunities.length).padStart(2, "0")}
          note={pipelineTotals.join(" · ") || "No open value yet"}
          href="/opportunities"
        />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
        <section className="card overflow-hidden">
          <div className="flex items-center justify-between border-b border-[var(--color-line)] px-5 py-4">
            <div>
              <p className="eyebrow">Prioritised by business rules</p>
              <h2 className="mt-1 font-semibold">Attention queue</h2>
            </div>
            <StatusBadge tone={attention.length ? "warning" : "success"}>
              {attention.length} actions
            </StatusBadge>
          </div>
          {attention.length ? (
            <div className="divide-y divide-[var(--color-line)]">
              {attention.slice(0, 6).map((item) => (
                <Link
                  key={item.key}
                  href={item.href}
                  className="grid gap-3 px-5 py-4 transition hover:bg-[var(--color-surface-subtle)] md:grid-cols-[1.4fr_0.8fr_auto] md:items-center"
                >
                  <div>
                    <p className="text-xs font-bold uppercase tracking-[0.08em] text-[var(--color-danger)]">
                      {item.reason}
                    </p>
                    <p className="mt-1 text-sm font-semibold">{item.title}</p>
                  </div>
                  <p className="text-sm text-[var(--color-muted)]">
                    {item.context}
                  </p>
                  <span className="text-sm font-semibold text-[var(--color-brand)]">
                    Review →
                  </span>
                </Link>
              ))}
            </div>
          ) : (
            <p className="p-8 text-sm text-[var(--color-muted)]">
              No urgent exceptions. Continue with the next scheduled task.
            </p>
          )}
        </section>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="eyebrow">Open pipeline</p>
              <h2 className="mt-1 font-semibold">Stage overview</h2>
            </div>
            <Link
              href="/opportunities"
              className="text-xs font-bold text-[var(--color-brand)]"
            >
              Open →
            </Link>
          </div>
          <div className="mt-7 grid gap-5">
            {[
              "discovery",
              "requirements_confirmed",
              "proposal",
              "negotiation",
            ].map((stage) => {
              const count = openOpportunities.filter(
                (item) => item.stage === stage,
              ).length;
              const width = openOpportunities.length
                ? Math.max(
                    6,
                    Math.round((count / openOpportunities.length) * 100),
                  )
                : 0;
              return (
                <div key={stage}>
                  <div className="flex justify-between text-xs">
                    <span className="font-semibold">
                      {opportunityStageLabels[stage]}
                    </span>
                    <span className="text-[var(--color-muted)]">{count}</span>
                  </div>
                  <div className="mt-2 h-1.5 rounded-full bg-[var(--color-line)]">
                    <div
                      className="h-full rounded-full bg-[var(--color-brand)]"
                      style={{ width: `${width}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <section className="card overflow-hidden">
          <div className="flex items-center justify-between border-b border-[var(--color-line)] px-5 py-4">
            <h2 className="font-semibold">Recent leads</h2>
            <Link
              href="/leads"
              className="text-xs font-bold text-[var(--color-brand)]"
            >
              View all →
            </Link>
          </div>
          {leadData.items.length ? (
            <div className="divide-y divide-[var(--color-line)]">
              {leadData.items.slice(0, 5).map((lead) => (
                <Link
                  key={lead.id}
                  href={`/leads/${lead.id}`}
                  className="grid gap-3 px-5 py-4 transition hover:bg-[var(--color-surface-subtle)] sm:grid-cols-[1fr_auto] sm:items-center"
                >
                  <div>
                    <p className="line-clamp-1 text-sm font-semibold">
                      {leadProjectLabel(lead)}
                    </p>
                    <p className="mt-1 text-xs text-[var(--color-muted)]">
                      {companyName(lead, companyNames)} ·{" "}
                      {formatCompactDate(lead.created_at)}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <PriorityStatus priority={lead.priority} />
                    <LeadStatus status={lead.status} />
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="p-8 text-sm text-[var(--color-muted)]">
              New website and manual inquiries will appear here.
            </p>
          )}
        </section>

        <section className="card overflow-hidden">
          <div className="flex items-center justify-between border-b border-[var(--color-line)] px-5 py-4">
            <h2 className="font-semibold">My next tasks</h2>
            <Link
              href="/follow-up"
              className="text-xs font-bold text-[var(--color-brand)]"
            >
              Open queue →
            </Link>
          </div>
          {nextTasks.length ? (
            <div className="divide-y divide-[var(--color-line)]">
              {nextTasks.map((task) => (
                <div
                  key={task.id}
                  className="grid gap-2 px-5 py-4 sm:grid-cols-[1fr_auto] sm:items-center"
                >
                  <div>
                    <p className="text-sm font-semibold">{task.title}</p>
                    <p className="mt-1 text-xs text-[var(--color-muted)]">
                      {task.due_at
                        ? `Due ${formatCompactDate(task.due_at)}`
                        : "Due date not set"}
                    </p>
                  </div>
                  <StatusBadge
                    tone={isTaskOverdue(task, now) ? "danger" : "neutral"}
                  >
                    {task.status.replaceAll("_", " ")}
                  </StatusBadge>
                </div>
              ))}
            </div>
          ) : (
            <p className="p-8 text-sm text-[var(--color-muted)]">
              No open tasks. Add a next action from a lead record.
            </p>
          )}
        </section>
      </div>
    </div>
  );
}

function buildAttentionQueue(
  leads: Lead[],
  overdueTasks: Task[],
  companyNames: Map<string, string>,
) {
  const urgent = leads
    .filter(
      (lead) =>
        lead.priority === "urgent" &&
        !lead.owner_membership_id &&
        !["converted", "archived", "disqualified"].includes(lead.status),
    )
    .map((lead) => ({
      key: `lead-${lead.id}`,
      reason: "Urgent unassigned lead",
      title: leadProjectLabel(lead),
      context: companyName(lead, companyNames),
      href: `/leads/${lead.id}`,
    }));
  const overdue = overdueTasks
    .filter((task) => task.lead_id)
    .map((task) => ({
      key: `task-${task.id}`,
      reason: "Follow-up overdue",
      title: task.title,
      context: task.due_at
        ? `Due ${formatCompactDate(task.due_at)}`
        : "Overdue",
      href: `/leads/${task.lead_id}?tab=follow-up`,
    }));
  const qualified = leads
    .filter((lead) => lead.status === "qualified")
    .map((lead) => ({
      key: `qualified-${lead.id}`,
      reason: "Qualified lead not converted",
      title: leadProjectLabel(lead),
      context: companyName(lead, companyNames),
      href: `/leads/${lead.id}`,
    }));
  return [...urgent, ...overdue, ...qualified];
}

function companyName(lead: Lead, names: Map<string, string>) {
  return lead.organization_id
    ? (names.get(lead.organization_id) ?? "Company record")
    : "Company not linked";
}

function dueTime(task: Task) {
  return task.due_at
    ? new Date(task.due_at).getTime()
    : Number.MAX_SAFE_INTEGER;
}
