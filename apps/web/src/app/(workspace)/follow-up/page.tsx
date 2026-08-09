import Link from "next/link";

import { ButtonLink } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status";
import { PageHeader } from "@/components/workspace/page-header";
import { apiFetch, type LeadList, type Task } from "@/lib/api";
import {
  formatDateTime,
  isTaskOpen,
  isTaskOverdue,
  leadProjectLabel,
} from "@/lib/workspace-format";

const views = ["overdue", "today", "upcoming", "completed", "all"] as const;

export default async function FollowUpPage({
  searchParams,
}: PageProps<"/follow-up">) {
  const query = await searchParams;
  const requested = single(query.view);
  const view = views.includes(requested as (typeof views)[number])
    ? requested
    : "overdue";
  const [tasks, leads] = await Promise.all([
    apiFetch<Task[]>("/api/v1/tasks?limit=200"),
    apiFetch<LeadList>("/api/v1/leads?limit=100"),
  ]);
  const leadNames = new Map(
    leads.items.map((lead) => [lead.id, leadProjectLabel(lead)]),
  );
  const now = new Date();
  const filtered = tasks
    .filter((task) => matchesView(task, view, now))
    .sort((a, b) => taskTime(a) - taskTime(b));
  const withoutNextTask = leads.items.filter(
    (lead) =>
      !["converted", "archived", "disqualified"].includes(lead.status) &&
      !tasks.some((task) => task.lead_id === lead.id && isTaskOpen(task)),
  );

  return (
    <div>
      <PageHeader
        eyebrow="Sales execution"
        title="Follow-up"
        description="Keep the next human action visible for every active inquiry. AI recommendations never create or send follow-up automatically."
        actions={<ButtonLink href="/leads">Choose lead to add task</ButtonLink>}
      />
      <nav
        className="mt-7 flex gap-2 overflow-x-auto border-b border-[var(--color-line)] pb-3"
        aria-label="Follow-up views"
      >
        {views.map((item) => {
          const active = view === item;
          const count = tasks.filter((task) =>
            matchesView(task, item, now),
          ).length;
          return (
            <Link
              key={item}
              href={`/follow-up?view=${item}`}
              aria-current={active ? "page" : undefined}
              className={
                active ? "button-primary shrink-0" : "button-tertiary shrink-0"
              }
            >
              {capitalize(item)} {count}
            </Link>
          );
        })}
      </nav>

      <section className="card mt-6 overflow-hidden">
        <div className="hidden grid-cols-[minmax(260px,1.4fr)_minmax(180px,1fr)_140px_120px] gap-4 border-b border-[var(--color-line)] bg-[var(--color-surface-subtle)] px-5 py-3 text-[0.68rem] font-bold uppercase tracking-[0.12em] text-[var(--color-muted)] md:grid">
          <span>Task</span>
          <span>Related lead</span>
          <span>Due</span>
          <span>Status</span>
        </div>
        {filtered.length ? (
          <div className="divide-y divide-[var(--color-line)]">
            {filtered.map((task) => (
              <Link
                key={task.id}
                href={
                  task.lead_id
                    ? `/leads/${task.lead_id}?tab=follow-up`
                    : "/follow-up"
                }
                className="grid gap-3 px-5 py-5 transition hover:bg-[var(--color-surface-subtle)] md:grid-cols-[minmax(260px,1.4fr)_minmax(180px,1fr)_140px_120px] md:items-center"
              >
                <div>
                  <p className="font-semibold">{task.title}</p>
                  <p className="mt-1 text-xs capitalize text-[var(--color-muted)]">
                    {task.priority} priority
                  </p>
                </div>
                <p className="text-sm text-[var(--color-muted)]">
                  {task.lead_id
                    ? (leadNames.get(task.lead_id) ?? "Lead record")
                    : "Related record"}
                </p>
                <p
                  className={
                    isTaskOverdue(task, now)
                      ? "text-sm font-semibold text-[var(--color-danger)]"
                      : "text-sm text-[var(--color-muted)]"
                  }
                >
                  {task.due_at ? formatDateTime(task.due_at) : "Not set"}
                </p>
                <StatusBadge
                  tone={
                    task.status === "completed"
                      ? "success"
                      : isTaskOverdue(task, now)
                        ? "danger"
                        : "neutral"
                  }
                >
                  {task.status.replaceAll("_", " ")}
                </StatusBadge>
              </Link>
            ))}
          </div>
        ) : (
          <p className="p-8 text-sm text-[var(--color-muted)]">
            No tasks in this view.
          </p>
        )}
      </section>

      <section className="card mt-6 overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-line)] px-5 py-4">
          <div>
            <p className="eyebrow">Exception queue</p>
            <h2 className="mt-1 font-semibold">
              Active leads without a next task
            </h2>
          </div>
          <StatusBadge tone={withoutNextTask.length ? "warning" : "success"}>
            {withoutNextTask.length} records
          </StatusBadge>
        </div>
        {withoutNextTask.length ? (
          <div className="grid gap-3 p-5 sm:grid-cols-2 xl:grid-cols-3">
            {withoutNextTask.slice(0, 9).map((lead) => (
              <Link
                key={lead.id}
                href={`/leads/${lead.id}?tab=follow-up`}
                className="rounded-xl border border-[var(--color-line)] p-4 transition hover:border-[var(--color-brand)]"
              >
                <p className="text-sm font-semibold">
                  {leadProjectLabel(lead)}
                </p>
                <p className="mt-2 text-xs text-[var(--color-muted)]">
                  Add next action →
                </p>
              </Link>
            ))}
          </div>
        ) : (
          <p className="p-8 text-sm text-[var(--color-muted)]">
            Every active lead currently has an open next task.
          </p>
        )}
      </section>
    </div>
  );
}

function matchesView(task: Task, view: string, now: Date) {
  if (view === "all") return true;
  if (view === "completed") return task.status === "completed";
  if (!isTaskOpen(task)) return false;
  if (view === "overdue") return isTaskOverdue(task, now);
  if (!task.due_at) return view === "upcoming";
  const due = new Date(task.due_at);
  if (view === "today") return sameDay(due, now);
  return due > endOfDay(now);
}

function sameDay(a: Date, b: Date) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function endOfDay(value: Date) {
  const result = new Date(value);
  result.setHours(23, 59, 59, 999);
  return result;
}

function taskTime(task: Task) {
  return task.due_at
    ? new Date(task.due_at).getTime()
    : Number.MAX_SAFE_INTEGER;
}

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
}
