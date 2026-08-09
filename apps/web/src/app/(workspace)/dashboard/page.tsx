import { ButtonLink } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/status";
import { MetricCard } from "@/components/workspace/metric-card";
import { TableLayout } from "@/components/workspace/table-layout";

const attention = [
  [
    "Urgent unassigned lead",
    "School kitchen expansion · Jakarta",
    "12 min ago",
    "Assign",
  ],
  [
    "Follow-up overdue",
    "Central production kitchen · Surabaya",
    "Yesterday",
    "Open task",
  ],
  ["AI review pending", "Factory cafeteria · Bekasi", "34 min ago", "Review"],
] as const;

export default function DashboardPage() {
  return (
    <div>
      <header className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Sunday, 9 August</p>
          <h1 className="page-title">Good morning.</h1>
          <p className="mt-3 text-sm text-[var(--color-muted)]">
            Focus on the records that need a human decision next.
          </p>
        </div>
        <ButtonLink href="/leads">Create lead</ButtonLink>
      </header>
      <div className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="New leads"
          value="08"
          note="3 need an owner"
          href="/leads"
        />
        <MetricCard
          label="AI review queue"
          value="03"
          note="Human decision required"
          href="/leads"
          tone="info"
        />
        <MetricCard
          label="Overdue tasks"
          value="05"
          note="Oldest is 2 days late"
          href="/follow-up"
          tone="warning"
        />
        <MetricCard
          label="Open pipeline"
          value="4 stages"
          note="Values shown by currency"
          href="/opportunities"
        />
      </div>
      <div className="mt-6 grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
        <TableLayout
          title="Attention queue"
          columns={["Reason / project", "Owner", "Age", "Action"]}
        >
          <div className="divide-y divide-[var(--color-line)]">
            {attention.map(([reason, project, age, action]) => (
              <div
                key={project}
                className="grid gap-3 px-5 py-4 md:grid-cols-[1.6fr_1fr_1fr_auto] md:items-center"
              >
                <div>
                  <p className="text-xs font-bold text-[var(--color-danger)]">
                    {reason}
                  </p>
                  <p className="mt-1 text-sm font-semibold">{project}</p>
                </div>
                <span className="text-sm text-[var(--color-muted)]">
                  Unassigned
                </span>
                <span className="text-sm text-[var(--color-muted)]">{age}</span>
                <button className="button-secondary justify-self-start">
                  {action}
                </button>
              </div>
            ))}
          </div>
        </TableLayout>
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Pipeline stages</h2>
            <StatusBadge tone="info">Preview</StatusBadge>
          </div>
          <div className="mt-7 grid gap-5">
            {[
              ["Discovery", "7", "42%"],
              ["Requirements", "4", "68%"],
              ["Proposal", "3", "30%"],
              ["Negotiation", "2", "22%"],
            ].map(([label, value, width]) => (
              <div key={label}>
                <div className="flex justify-between text-xs">
                  <span className="font-semibold">{label}</span>
                  <span className="text-[var(--color-muted)]">{value}</span>
                </div>
                <div className="mt-2 h-1.5 rounded-full bg-[var(--color-line)]">
                  <div
                    className="h-full rounded-full bg-[var(--color-brand)]"
                    style={{ width }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
