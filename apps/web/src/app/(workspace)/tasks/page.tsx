import Link from "next/link";

import { apiFetch, type Task } from "@/lib/api";

import { updateTask } from "../actions";

export default async function TasksPage() {
  const tasks = await apiFetch<Task[]>("/api/v1/tasks");
  const activeCount = tasks.filter(
    (task) => task.status === "open" || task.status === "in_progress",
  ).length;
  return (
    <div>
      <p className="eyebrow">Sales execution</p>
      <h1 className="page-title">Follow-up tasks</h1>
      <p className="mt-3 text-[var(--muted)]">
        {activeCount} active tasks ordered by due date.
      </p>
      <div className="card mt-7 divide-y divide-[var(--line)] overflow-hidden">
        {tasks.length ? (
          tasks.map((task) => <TaskCard key={task.id} task={task} />)
        ) : (
          <p className="p-8 text-sm text-[var(--muted)]">
            Tasks created from a lead will appear here.
          </p>
        )}
      </div>
    </div>
  );
}

function TaskCard({ task }: { task: Task }) {
  const leadId = task.lead_id ?? "";
  const nextStatus = task.status === "completed" ? "open" : "completed";
  const action = updateTask.bind(
    null,
    leadId,
    task.id,
    task.version,
    nextStatus,
  );
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 p-6">
      <div>
        {task.lead_id ? (
          <Link
            href={"/leads/" + task.lead_id}
            className="font-semibold hover:underline"
          >
            {task.title}
          </Link>
        ) : (
          <p className="font-semibold">{task.title}</p>
        )}
        <p className="mt-2 text-sm text-[var(--muted)]">
          {task.due_at
            ? "Due " +
              new Intl.DateTimeFormat("en", {
                dateStyle: "medium",
              }).format(new Date(task.due_at))
            : "No due date"}
          {" · " + task.priority + " priority"}
        </p>
      </div>
      <div className="flex items-center gap-3">
        <span className="status-chip">{task.status}</span>
        {task.lead_id ? (
          <form action={action}>
            <button className="button-secondary">
              {task.status === "completed" ? "Reopen" : "Complete"}
            </button>
          </form>
        ) : null}
      </div>
    </div>
  );
}
