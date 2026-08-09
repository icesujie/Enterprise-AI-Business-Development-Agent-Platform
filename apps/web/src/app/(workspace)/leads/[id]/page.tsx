import Link from "next/link";

import {
  apiFetch,
  type Activity,
  type Lead,
  type LeadAssessment,
  type QualificationRun,
  type Task,
} from "@/lib/api";

import {
  createNote,
  createTask,
  convertLead,
  reviewQualification,
  runQualification,
  updateLead,
  updateTask,
} from "../../actions";

export default async function LeadDetailPage({
  params,
}: PageProps<"/leads/[id]">) {
  const { id } = await params;
  const [lead, tasks, activities, assessments, runs] = await Promise.all([
    apiFetch<Lead>("/api/v1/leads/" + id),
    apiFetch<Task[]>("/api/v1/tasks?lead_id=" + id),
    apiFetch<Activity[]>("/api/v1/leads/" + id + "/activities"),
    apiFetch<LeadAssessment[]>(
      "/api/v1/leads/" + id + "/qualification-assessments",
    ),
    apiFetch<QualificationRun[]>("/api/v1/leads/" + id + "/qualification-runs"),
  ]);
  const editAction = updateLead.bind(null, lead.id, lead.version);
  const taskAction = createTask.bind(null, lead.id);
  const noteAction = createNote.bind(null, lead.id);
  const qualificationAction = runQualification.bind(null, lead.id);
  const conversionAction = convertLead.bind(null, lead.id, lead.version);

  return (
    <div>
      <Link
        href="/leads"
        className="text-sm font-semibold text-[var(--accent)]"
      >
        ← Back to leads
      </Link>
      <header className="mt-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow">Lead workspace</p>
          <h1 className="mt-2 max-w-3xl text-3xl font-semibold tracking-tight">
            {lead.inquiry_summary}
          </h1>
          <p className="mt-3 text-sm text-[var(--muted)]">
            Created {formatDate(lead.created_at)} · Version {lead.version}
          </p>
        </div>
        <div className="flex gap-2">
          <span className="status-chip">{lead.status}</span>
          <span className="status-chip">{lead.priority}</span>
        </div>
      </header>

      <div className="mt-7 grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <form key={lead.version} action={editAction} className="card p-7">
            <h2 className="text-lg font-semibold">Project information</h2>
            <label className="label">
              Inquiry summary
              <textarea
                className="field mt-2 min-h-32 resize-y"
                name="inquiry_summary"
                defaultValue={lead.inquiry_summary}
                minLength={10}
                required
              />
            </label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="label">
                Status
                <select
                  className="field mt-2"
                  name="status"
                  defaultValue={lead.status}
                >
                  {[
                    "new",
                    "qualifying",
                    "qualified",
                    "nurture",
                    "disqualified",
                    "archived",
                  ].map((value) => (
                    <option key={value}>{value}</option>
                  ))}
                </select>
              </label>
              <label className="label">
                Priority
                <select
                  className="field mt-2"
                  name="priority"
                  defaultValue={lead.priority}
                >
                  {["low", "normal", "high", "urgent"].map((value) => (
                    <option key={value}>{value}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <EditField
                label="Project city"
                name="project_city"
                value={lead.project_city}
              />
              <EditField
                label="Project type"
                name="project_type"
                value={lead.project_type}
              />
              <EditField
                label="Expected capacity"
                name="expected_capacity"
                value={lead.expected_capacity}
              />
              <EditField
                label="Target timeline"
                name="target_timeline"
                value={lead.target_timeline}
              />
            </div>
            <button className="button-primary mt-7">Save changes</button>
          </form>

          <section className="card p-7">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="eyebrow">Follow-up</p>
                <h2 className="mt-2 text-xl font-semibold">Tasks</h2>
              </div>
              <span className="status-chip">
                {
                  tasks.filter(
                    (task) =>
                      task.status === "open" || task.status === "in_progress",
                  ).length
                }{" "}
                active
              </span>
            </div>
            <form
              action={taskAction}
              className="mt-5 grid gap-3 sm:grid-cols-2"
            >
              <input
                className="field sm:col-span-2"
                name="title"
                placeholder="Next action"
                maxLength={250}
                required
              />
              <input
                className="field"
                name="due_at"
                type="datetime-local"
                aria-label="Due date"
              />
              <select className="field" name="priority" aria-label="Priority">
                <option>normal</option>
                <option>high</option>
                <option>urgent</option>
                <option>low</option>
              </select>
              <textarea
                className="field min-h-20 sm:col-span-2"
                name="description"
                placeholder="Optional instructions"
              />
              <button className="button-primary w-fit">Add task</button>
            </form>
            <div className="mt-6 divide-y divide-[var(--line)]">
              {tasks.length ? (
                tasks.map((task) => (
                  <TaskRow key={task.id} leadId={lead.id} task={task} />
                ))
              ) : (
                <p className="py-5 text-sm text-[var(--muted)]">
                  No follow-up tasks yet.
                </p>
              )}
            </div>
          </section>

          <section className="card p-7">
            <p className="eyebrow">History</p>
            <h2 className="mt-2 text-xl font-semibold">Activity timeline</h2>
            <form action={noteAction} className="mt-5 grid gap-3">
              <input
                className="field"
                name="subject"
                placeholder="Note title"
                maxLength={250}
                required
              />
              <textarea
                className="field min-h-24"
                name="description"
                placeholder="What did you learn or agree internally?"
                required
              />
              <button className="button-primary w-fit">Add note</button>
            </form>
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
                    <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
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
          {lead.status === "qualified" ? (
            <section className="card p-6">
              <p className="eyebrow">Sales handoff</p>
              <h2 className="mt-3 text-xl font-semibold">Create opportunity</h2>
              {lead.organization_id ? (
                <form action={conversionAction} className="mt-5 space-y-4">
                  <label className="label">
                    Opportunity name
                    <input
                      className="field mt-2"
                      name="name"
                      defaultValue={
                        lead.project_type
                          ? `${lead.project_type} · ${lead.project_city ?? "Project"}`
                          : lead.inquiry_summary.slice(0, 80)
                      }
                      minLength={3}
                      maxLength={250}
                      required
                    />
                  </label>
                  <label className="label">
                    Expected close
                    <input
                      className="field mt-2"
                      name="expected_close_date"
                      type="date"
                    />
                  </label>
                  <div className="grid grid-cols-[1fr_90px] gap-3">
                    <label className="label">
                      Estimated value
                      <input
                        className="field mt-2"
                        name="estimated_value"
                        type="number"
                        min="0"
                        step="0.01"
                        defaultValue={lead.estimated_value ?? ""}
                      />
                    </label>
                    <label className="label">
                      Currency
                      <input
                        className="field mt-2 uppercase"
                        name="currency"
                        defaultValue={lead.currency ?? "IDR"}
                        minLength={3}
                        maxLength={3}
                      />
                    </label>
                  </div>
                  <button className="button-primary w-full">
                    Convert to opportunity
                  </button>
                </form>
              ) : (
                <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
                  Select a customer company on this lead before conversion.
                </p>
              )}
            </section>
          ) : null}
          {lead.status === "converted" ? (
            <section className="card p-6">
              <p className="eyebrow">Converted</p>
              <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
                This source lead is preserved and locked against duplicate
                conversion.
              </p>
              <Link
                href="/opportunities"
                className="button-secondary mt-5 block text-center"
              >
                View sales pipeline
              </Link>
            </section>
          ) : null}
          <section className="card p-6">
            <p className="eyebrow">AI qualification</p>
            <QualificationPanel
              lead={lead}
              assessment={assessments[0]}
              run={runs[0]}
              runAction={qualificationAction}
            />
          </section>
          <section className="card p-6">
            <p className="eyebrow">Human control</p>
            <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
              AI output is advisory. It cannot change lead status, create
              customer commitments, or send messages. Accepting an assessment
              records its score; a salesperson still decides the business
              status.
            </p>
          </section>
        </aside>
      </div>
    </div>
  );
}

function TaskRow({ leadId, task }: { leadId: string; task: Task }) {
  const complete = updateTask.bind(
    null,
    leadId,
    task.id,
    task.version,
    "completed",
  );
  const start = updateTask.bind(
    null,
    leadId,
    task.id,
    task.version,
    "in_progress",
  );
  const reopen = updateTask.bind(null, leadId, task.id, task.version, "open");
  return (
    <div className="py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-semibold">{task.title}</p>
          <p className="mt-1 text-xs text-[var(--muted)]">
            {task.due_at ? "Due " + formatDateTime(task.due_at) : "No due date"}
          </p>
        </div>
        <span className="status-chip">{task.status}</span>
      </div>
      {task.description ? (
        <p className="mt-2 text-sm text-[var(--muted)]">{task.description}</p>
      ) : null}
      <div className="mt-3 flex gap-2">
        {task.status === "open" ? (
          <form action={start}>
            <button className="button-secondary">Start</button>
          </form>
        ) : null}
        {task.status === "open" || task.status === "in_progress" ? (
          <form action={complete}>
            <button className="button-secondary">Complete</button>
          </form>
        ) : null}
        {task.status === "completed" || task.status === "cancelled" ? (
          <form action={reopen}>
            <button className="button-secondary">Reopen</button>
          </form>
        ) : null}
      </div>
    </div>
  );
}

function QualificationPanel({
  lead,
  assessment,
  run,
  runAction,
}: {
  lead: Lead;
  assessment: LeadAssessment | undefined;
  run: QualificationRun | undefined;
  runAction: () => Promise<void>;
}) {
  if (assessment) {
    const approve = reviewQualification.bind(
      null,
      lead.id,
      assessment.id,
      "approved",
    );
    const reject = reviewQualification.bind(
      null,
      lead.id,
      assessment.id,
      "rejected",
    );
    return (
      <div className="mt-4">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-4xl font-semibold">{assessment.score}</p>
            <p className="mt-1 text-sm text-[var(--muted)]">out of 100</p>
          </div>
          <span className="status-chip">{assessment.tier}</span>
        </div>
        <p className="mt-5 text-sm leading-6">{assessment.need_summary}</p>
        <dl className="mt-5 grid grid-cols-2 gap-3">
          {Object.entries(assessment.qualification).map(([key, value]) => (
            <div key={key} className="rounded-xl bg-[var(--canvas)] p-3">
              <dt className="text-xs text-[var(--muted)]">
                {key.replace("_status", "")}
              </dt>
              <dd className="mt-1 text-sm font-semibold">{value}</dd>
            </div>
          ))}
        </dl>
        <h3 className="mt-5 text-sm font-semibold">Recommended action</h3>
        <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
          {assessment.recommended_action}
        </p>
        {assessment.missing_information.length ? (
          <>
            <h3 className="mt-5 text-sm font-semibold">Missing information</h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-[var(--muted)]">
              {assessment.missing_information.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </>
        ) : null}
        <p className="mt-5 text-xs text-[var(--muted)]">
          Confidence {Math.round(Number(assessment.confidence) * 100)}% · Review{" "}
          {assessment.review_status}
        </p>
        {assessment.review_status === "pending" ? (
          <div className="mt-5 grid grid-cols-2 gap-2">
            <form action={approve}>
              <button className="button-primary w-full">Accept</button>
            </form>
            <form action={reject}>
              <button className="button-secondary w-full">Reject</button>
            </form>
          </div>
        ) : (
          <form action={runAction} className="mt-5">
            <button className="button-secondary w-full">Run again</button>
          </form>
        )}
      </div>
    );
  }

  if (run?.status === "queued" || run?.status === "running") {
    return (
      <div className="mt-4">
        <h2 className="text-xl font-semibold">Qualification in progress</h2>
        <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
          The run is {run.status}. You can leave this page safely; the result is
          stored in PostgreSQL.
        </p>
        <Link
          href={"/leads/" + lead.id}
          className="button-secondary mt-5 block text-center"
        >
          Refresh status
        </Link>
      </div>
    );
  }

  return (
    <div className="mt-4">
      <h2 className="text-xl font-semibold">
        {run?.status === "failed" ? "Qualification unavailable" : "Not run yet"}
      </h2>
      <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
        {run?.error_message ??
          "Score project fit, timeline, budget evidence, and decision authority."}
      </p>
      <form action={runAction} className="mt-5">
        <button className="button-primary w-full">
          {run?.status === "failed"
            ? "Retry qualification"
            : "Run AI qualification"}
        </button>
      </form>
    </div>
  );
}

function EditField({
  label,
  name,
  value,
}: {
  label: string;
  name: string;
  value: string | null;
}) {
  return (
    <label className="label">
      {label}
      <input className="field mt-2" name={name} defaultValue={value ?? ""} />
    </label>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(
    new Date(value),
  );
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
