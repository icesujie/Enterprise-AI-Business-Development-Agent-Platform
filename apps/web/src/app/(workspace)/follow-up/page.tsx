import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status";
import { EmptyState } from "@/components/workspace/states";
import { TableLayout } from "@/components/workspace/table-layout";

export default function FollowUpPage() {
  return (
    <div>
      <header className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Sales execution</p>
          <h1 className="page-title">Follow-up</h1>
          <p className="mt-3 text-sm text-[var(--color-muted)]">
            A unified queue for the next human action on every active project.
          </p>
        </div>
        <Button>Create task</Button>
      </header>
      <div className="mt-7 flex gap-2 overflow-x-auto border-b border-[var(--color-line)] pb-3">
        {["Overdue", "Today", "Upcoming", "Completed", "All"].map(
          (item, index) => (
            <button
              key={item}
              className={
                index === 0
                  ? "button-primary shrink-0"
                  : "button-tertiary shrink-0"
              }
            >
              {item}
              {index === 0 ? " 5" : ""}
            </button>
          ),
        )}
      </div>
      <div className="mt-6">
        <TableLayout
          title="Overdue tasks"
          columns={["Task / record", "Assignee", "Due", "Status"]}
        >
          <div className="grid gap-3 px-5 py-5 md:grid-cols-[1.6fr_1fr_1fr_auto] md:items-center">
            <div>
              <p className="font-semibold">
                Confirm operating capacity and service window
              </p>
              <p className="mt-1 text-xs text-[var(--color-muted)]">
                School kitchen expansion · Jakarta
              </p>
            </div>
            <span className="text-sm text-[var(--color-muted)]">
              Sales owner
            </span>
            <span className="text-sm font-semibold text-[var(--color-danger)]">
              2 days overdue
            </span>
            <StatusBadge tone="warning">Open</StatusBadge>
          </div>
        </TableLayout>
      </div>
      <div className="mt-6">
        <TableLayout
          title="Records without a next task"
          columns={["Record", "Owner", "Last activity", "Action"]}
        >
          <EmptyState
            title="Exception queue placeholder"
            description="This section will connect to the existing task and activity APIs during the business-feature stage."
          />
        </TableLayout>
      </div>
    </div>
  );
}
