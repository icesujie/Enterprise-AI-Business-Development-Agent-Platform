import type { Lead, Opportunity, Task } from "@/lib/api";

export const leadStatusLabels: Record<string, string> = {
  new: "New inquiry",
  qualifying: "Qualifying",
  qualified: "Qualified",
  nurture: "Nurture",
  disqualified: "Disqualified",
  converted: "Converted",
  archived: "Archived",
};

export const opportunityStageLabels: Record<string, string> = {
  discovery: "New inquiry",
  requirements_confirmed: "Qualified",
  proposal: "Proposal",
  negotiation: "Negotiation",
  won: "Won",
  lost: "Lost",
};

export function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(
    new Date(value),
  );
}

export function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatCompactDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

export function formatMoney(value: string, currency: string) {
  return `${currency} ${new Intl.NumberFormat("en", {
    maximumFractionDigits: 0,
  }).format(Number(value))}`;
}

export function leadProjectLabel(lead: Lead) {
  return (
    [lead.project_type, lead.project_city].filter(Boolean).join(" · ") ||
    lead.inquiry_summary
  );
}

export function isTaskOpen(task: Task) {
  return task.status === "open" || task.status === "in_progress";
}

export function isTaskOverdue(task: Task, now = new Date()) {
  return Boolean(
    task.due_at && isTaskOpen(task) && new Date(task.due_at) < now,
  );
}

export function groupOpportunityValue(items: Opportunity[]) {
  const totals = new Map<string, number>();
  for (const item of items) {
    totals.set(
      item.currency,
      (totals.get(item.currency) ?? 0) + Number(item.estimated_value),
    );
  }
  return [...totals.entries()].map(([currency, value]) =>
    formatMoney(String(value), currency),
  );
}
