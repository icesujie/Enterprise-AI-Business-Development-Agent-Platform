import Link from "next/link";

import { StatusBadge } from "@/components/ui/status";
import { LeadStatus, PriorityStatus } from "@/components/workspace/lead-status";
import { QualificationCard } from "@/components/workspace/qualification-card";
import {
  apiFetch,
  type Activity,
  type Contact,
  type Lead,
  type LeadAssessment,
  type Opportunity,
  type OpportunityList,
  type Organization,
  type QualificationRun,
  type Task,
} from "@/lib/api";
import {
  formatDate,
  formatDateTime,
  isTaskOpen,
  leadProjectLabel,
} from "@/lib/workspace-format";

import {
  createNote,
  createTask,
  convertLead,
  reviewQualification,
  runQualification,
  updateLead,
  updateTask,
} from "../../actions";

const tabs = [
  ["Overview", "overview"],
  ["Qualification", "qualification"],
  ["Follow-up", "follow-up"],
  ["Activity", "activity"],
] as const;

export default async function LeadDetailPage({
  params,
  searchParams,
}: PageProps<"/leads/[id]">) {
  const { id } = await params;
  const query = await searchParams;
  const requestedTab = single(query.tab);
  const tab = tabs.some(([, value]) => value === requestedTab)
    ? requestedTab
    : "overview";
  const lead = await apiFetch<Lead>(`/api/v1/leads/${id}`);
  const [tasks, activities, assessments, runs, organization, contact, linked] =
    await Promise.all([
      apiFetch<Task[]>(`/api/v1/tasks?lead_id=${id}`),
      apiFetch<Activity[]>(`/api/v1/leads/${id}/activities`),
      apiFetch<LeadAssessment[]>(
        `/api/v1/leads/${id}/qualification-assessments`,
      ),
      apiFetch<QualificationRun[]>(`/api/v1/leads/${id}/qualification-runs`),
      lead.organization_id
        ? apiFetch<Organization>(
            `/api/v1/organizations/${lead.organization_id}`,
          )
        : Promise.resolve(null),
      lead.contact_id
        ? apiFetch<Contact>(`/api/v1/contacts/${lead.contact_id}`)
        : Promise.resolve(null),
      lead.status === "converted"
        ? apiFetch<OpportunityList>("/api/v1/opportunities?limit=100").then(
            (data) =>
              data.items.find((item) => item.source_lead_id === lead.id) ??
              null,
          )
        : Promise.resolve(null),
    ]);
  const latestAssessment = assessments[0];
  const latestRun = runs[0];
  const qualificationAction = runQualification.bind(null, lead.id);
  const approveAction = latestAssessment
    ? reviewQualification.bind(null, lead.id, latestAssessment.id, "approved")
    : undefined;
  const rejectAction = latestAssessment
    ? reviewQualification.bind(null, lead.id, latestAssessment.id, "rejected")
    : undefined;

  return (
    <div>
      <Link href="/leads" className="button-tertiary px-0">
        ← Back to leads
      </Link>

      <header className="mt-5 rounded-2xl border border-[var(--color-line)] bg-white p-6 shadow-[var(--shadow-card)] sm:p-7">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
          <div className="max-w-4xl">
            <div className="flex flex-wrap gap-2">
              <LeadStatus status={lead.status} />
              <PriorityStatus priority={lead.priority} />
              {lead.qualification_score ? (
                <StatusBadge tone="info">
                  AI {Math.round(Number(lead.qualification_score))}/100
                </StatusBadge>
              ) : null}
            </div>
            <p className="eyebrow mt-5">Lead record</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
              {leadProjectLabel(lead)}
            </h1>
            <p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">
              {organization?.display_name ?? "Company not linked"} ·{" "}
              {contactName(contact)} · Created {formatDate(lead.created_at)}
            </p>
          </div>
          <PrimaryAction lead={lead} linked={linked} />
        </div>

        <dl className="mt-7 grid gap-4 border-t border-[var(--color-line)] pt-5 sm:grid-cols-2 lg:grid-cols-4">
          <SummaryFact
            label="Location"
            value={
              [lead.project_city, lead.project_country_code]
                .filter(Boolean)
                .join(", ") || "Not confirmed"
            }
          />
          <SummaryFact
            label="Capacity"
            value={lead.expected_capacity || "Not confirmed"}
          />
          <SummaryFact
            label="Timeline"
            value={lead.target_timeline || "Not confirmed"}
          />
          <SummaryFact
            label="Source"
            value={lead.source_channel.replaceAll("_", " ")}
          />
        </dl>
      </header>

      <nav
        className="mt-6 flex gap-2 overflow-x-auto border-b border-[var(--color-line)] pb-3"
        aria-label="Lead record sections"
      >
        {tabs.map(([label, value]) => (
          <Link
            key={value}
            href={`/leads/${lead.id}?tab=${value}`}
            aria-current={tab === value ? "page" : undefined}
            className={
              tab === value
                ? "button-primary shrink-0"
                : "button-tertiary shrink-0"
            }
          >
            {label}
            {value === "follow-up" && tasks.filter(isTaskOpen).length
              ? ` ${tasks.filter(isTaskOpen).length}`
              : ""}
          </Link>
        ))}
      </nav>

      <div className="mt-6">
        {tab === "overview" ? (
          <OverviewTab
            lead={lead}
            organization={organization}
            contact={contact}
            assessment={latestAssessment}
            tasks={tasks}
            linked={linked}
          />
        ) : null}
        {tab === "qualification" ? (
          <QualificationCard
            lead={lead}
            contact={contact}
            assessment={latestAssessment}
            history={assessments}
            run={latestRun}
            runAction={qualificationAction}
            approveAction={approveAction}
            rejectAction={rejectAction}
          />
        ) : null}
        {tab === "follow-up" ? <FollowUpTab lead={lead} tasks={tasks} /> : null}
        {tab === "activity" ? (
          <ActivityTab lead={lead} activities={activities} />
        ) : null}
      </div>
    </div>
  );
}

function OverviewTab({
  lead,
  organization,
  contact,
  assessment,
  tasks,
  linked,
}: {
  lead: Lead;
  organization: Organization | null;
  contact: Contact | null;
  assessment?: LeadAssessment;
  tasks: Task[];
  linked: Opportunity | null;
}) {
  const editAction = updateLead.bind(null, lead.id, lead.version);
  const conversionAction = convertLead.bind(null, lead.id, lead.version);
  const nextTask = tasks
    .filter(isTaskOpen)
    .sort((a, b) => taskTime(a) - taskTime(b))[0];
  const missing = [
    !lead.project_type && "Project type",
    !lead.expected_capacity && "Operating capacity",
    !lead.target_timeline && "Target timeline",
    !lead.estimated_value && "Budget indication",
    !contact?.job_title && "Decision role",
  ].filter(Boolean) as string[];

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <div className="space-y-6">
        <section className="rounded-2xl border border-[var(--color-info)]/20 bg-[var(--color-info-soft)] p-6">
          <p className="eyebrow text-[var(--color-info)]">Recommended focus</p>
          <h2 className="mt-2 text-xl font-semibold">
            {assessment?.recommended_action ??
              "Confirm the project facts and run qualification when ready."}
          </h2>
          <p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">
            This is a working recommendation. A salesperson remains responsible
            for the next business action.
          </p>
        </section>

        <section className="card p-6 sm:p-7">
          <p className="eyebrow">Original inquiry message</p>
          <blockquote className="mt-4 border-l-2 border-[var(--color-accent)] pl-5 text-base leading-8">
            {lead.inquiry_summary}
          </blockquote>
          <p className="mt-4 text-xs text-[var(--color-muted)]">
            Captured via {lead.source_channel.replaceAll("_", " ")} ·{" "}
            {formatDateTime(lead.created_at)}
          </p>
        </section>

        <section className="card p-6 sm:p-7">
          <p className="eyebrow">Project facts</p>
          <dl className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            <Detail label="Project type" value={lead.project_type} />
            <Detail label="Expected capacity" value={lead.expected_capacity} />
            <Detail label="Target timeline" value={lead.target_timeline} />
            <Detail label="Project city" value={lead.project_city} />
            <Detail label="Country" value={lead.project_country_code} />
            <Detail
              label="Budget indication"
              value={
                lead.estimated_value && lead.currency
                  ? `${lead.currency} ${Number(lead.estimated_value).toLocaleString("en")}`
                  : null
              }
            />
          </dl>
          {Object.keys(lead.requirements).length ? (
            <dl className="mt-6 grid gap-5 border-t border-[var(--color-line)] pt-5 sm:grid-cols-2">
              {Object.entries(lead.requirements).map(([key, value]) => (
                <Detail
                  key={key}
                  label={key.replaceAll("_", " ")}
                  value={String(value)}
                />
              ))}
            </dl>
          ) : null}
        </section>

        <section className="card p-6 sm:p-7">
          <div className="grid gap-8 lg:grid-cols-2">
            <div>
              <p className="eyebrow">Customer company</p>
              <h2 className="mt-3 text-xl font-semibold">
                {organization?.display_name ?? "Not linked"}
              </h2>
              <p className="mt-2 text-sm text-[var(--color-muted)]">
                {[
                  organization?.industry,
                  organization?.city,
                  organization?.country_code,
                ]
                  .filter(Boolean)
                  .join(" · ") || "Company profile is incomplete"}
              </p>
            </div>
            <div>
              <p className="eyebrow">Primary contact</p>
              <h2 className="mt-3 text-xl font-semibold">
                {contactName(contact)}
              </h2>
              <p className="mt-2 text-sm text-[var(--color-muted)]">
                {[contact?.job_title, contact?.email, contact?.phone_e164]
                  .filter(Boolean)
                  .join(" · ") || "Contact details are incomplete"}
              </p>
            </div>
          </div>
        </section>

        <form
          key={lead.version}
          action={editAction}
          className="card p-6 sm:p-7"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="eyebrow">Human-owned record</p>
              <h2 className="mt-2 text-xl font-semibold">
                Update project facts
              </h2>
            </div>
            <span className="text-xs text-[var(--color-muted)]">
              Version {lead.version}
            </span>
          </div>
          <label className="label">
            Inquiry summary
            <textarea
              className="field mt-2 min-h-28 resize-y"
              name="inquiry_summary"
              defaultValue={lead.inquiry_summary}
              minLength={10}
              required
            />
          </label>
          <div className="grid gap-4 sm:grid-cols-2">
            <SelectField
              label="Status"
              name="status"
              value={lead.status}
              options={[
                "new",
                "qualifying",
                "qualified",
                "nurture",
                "disqualified",
                "converted",
                "archived",
              ]}
            />
            <SelectField
              label="Priority"
              name="priority"
              value={lead.priority}
              options={["low", "normal", "high", "urgent"]}
            />
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
          <button className="button-primary mt-6">Save changes</button>
        </form>
      </div>

      <aside className="space-y-6">
        <section className="card p-6">
          <p className="eyebrow">Next follow-up</p>
          {nextTask ? (
            <>
              <h2 className="mt-3 text-lg font-semibold">{nextTask.title}</h2>
              <p className="mt-2 text-sm text-[var(--color-muted)]">
                {nextTask.due_at
                  ? `Due ${formatDateTime(nextTask.due_at)}`
                  : "No due date set"}
              </p>
              <Link
                href={`/leads/${lead.id}?tab=follow-up`}
                className="button-secondary mt-5 w-full justify-center"
              >
                Open follow-up
              </Link>
            </>
          ) : (
            <>
              <h2 className="mt-3 text-lg font-semibold">No next task</h2>
              <p className="mt-2 text-sm leading-6 text-[var(--color-muted)]">
                Add a human-owned next action so this inquiry does not stall.
              </p>
              <Link
                href={`/leads/${lead.id}?tab=follow-up`}
                className="button-secondary mt-5 w-full justify-center"
              >
                Create task
              </Link>
            </>
          )}
        </section>

        <section className="card p-6">
          <p className="eyebrow">Missing information</p>
          {missing.length ? (
            <ul className="mt-4 space-y-3 text-sm text-[var(--color-muted)]">
              {missing.map((item) => (
                <li key={item} className="flex gap-2">
                  <span aria-hidden>□</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-[var(--color-muted)]">
              Core qualification fields are present.
            </p>
          )}
        </section>

        {lead.status === "qualified" ? (
          <ConversionCard lead={lead} action={conversionAction} />
        ) : null}
        {lead.status === "converted" ? (
          <section className="card p-6">
            <p className="eyebrow">Converted</p>
            <p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">
              The source lead remains preserved and protected from duplicate
              conversion.
            </p>
            <Link
              href={linked ? `/opportunities/${linked.id}` : "/opportunities"}
              className="button-primary mt-5 w-full justify-center"
            >
              Open opportunity
            </Link>
          </section>
        ) : null}
      </aside>
    </div>
  );
}

function FollowUpTab({ lead, tasks }: { lead: Lead; tasks: Task[] }) {
  const taskAction = createTask.bind(null, lead.id);
  const openTasks = tasks.filter(isTaskOpen);
  const completedTasks = tasks.filter((task) => !isTaskOpen(task));
  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <section className="card overflow-hidden">
        <div className="border-b border-[var(--color-line)] p-6">
          <p className="eyebrow">Human action queue</p>
          <h2 className="mt-2 text-xl font-semibold">Open tasks</h2>
        </div>
        {openTasks.length ? (
          <div className="divide-y divide-[var(--color-line)] px-6">
            {openTasks.map((task) => (
              <TaskRow key={task.id} leadId={lead.id} task={task} />
            ))}
          </div>
        ) : (
          <p className="p-8 text-sm text-[var(--color-muted)]">
            No open task. Create the next follow-up action.
          </p>
        )}
        {completedTasks.length ? (
          <details className="border-t border-[var(--color-line)] p-6">
            <summary className="cursor-pointer text-sm font-semibold">
              Completed and cancelled tasks ({completedTasks.length})
            </summary>
            <div className="mt-4 divide-y divide-[var(--color-line)]">
              {completedTasks.map((task) => (
                <TaskRow key={task.id} leadId={lead.id} task={task} />
              ))}
            </div>
          </details>
        ) : null}
      </section>

      <form action={taskAction} className="card h-fit p-6">
        <p className="eyebrow">Create next action</p>
        <label className="label">
          Task title
          <input className="field mt-2" name="title" maxLength={250} required />
        </label>
        <label className="label">
          Due date and time
          <input className="field mt-2" name="due_at" type="datetime-local" />
        </label>
        <label className="label">
          Priority
          <select className="field mt-2" name="priority" defaultValue="normal">
            <option value="normal">Normal</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
            <option value="low">Low</option>
          </select>
        </label>
        <label className="label">
          Instructions
          <textarea className="field mt-2 min-h-24" name="description" />
        </label>
        <button className="button-primary mt-5 w-full">Add task</button>
        <p className="mt-3 text-xs leading-5 text-[var(--color-muted)]">
          No customer message is sent. This creates an internal follow-up task.
        </p>
      </form>
    </div>
  );
}

function ActivityTab({
  lead,
  activities,
}: {
  lead: Lead;
  activities: Activity[];
}) {
  const noteAction = createNote.bind(null, lead.id);
  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <section className="card p-6 sm:p-7">
        <p className="eyebrow">Business history</p>
        <h2 className="mt-2 text-xl font-semibold">Activity timeline</h2>
        {activities.length ? (
          <ol className="timeline mt-7">
            {activities.map((activity) => (
              <li key={activity.id} className="timeline-item">
                <div className="flex flex-wrap items-center gap-2">
                  <strong className="text-sm">{activity.subject}</strong>
                  <StatusBadge>
                    {activity.activity_type.replaceAll("_", " ")}
                  </StatusBadge>
                </div>
                {activity.description ? (
                  <p className="mt-2 text-sm leading-6 text-[var(--color-muted)]">
                    {activity.description}
                  </p>
                ) : null}
                <p className="mt-2 text-xs text-[var(--color-muted)]">
                  {formatDateTime(activity.occurred_at)}
                </p>
              </li>
            ))}
          </ol>
        ) : (
          <p className="mt-6 text-sm text-[var(--color-muted)]">
            No activity has been recorded.
          </p>
        )}
      </section>
      <form action={noteAction} className="card h-fit p-6">
        <p className="eyebrow">Internal note</p>
        <label className="label">
          Subject
          <input
            className="field mt-2"
            name="subject"
            maxLength={250}
            required
          />
        </label>
        <label className="label">
          Note
          <textarea
            className="field mt-2 min-h-28"
            name="description"
            required
          />
        </label>
        <button className="button-primary mt-5 w-full">Add note</button>
        <p className="mt-3 text-xs leading-5 text-[var(--color-muted)]">
          Internal notes are part of the business record and are not sent to the
          customer.
        </p>
      </form>
    </div>
  );
}

function PrimaryAction({
  lead,
  linked,
}: {
  lead: Lead;
  linked: Opportunity | null;
}) {
  if (lead.status === "converted") {
    return (
      <Link
        href={linked ? `/opportunities/${linked.id}` : "/opportunities"}
        className="button-primary justify-center"
      >
        Open linked opportunity
      </Link>
    );
  }
  if (lead.status === "qualified") {
    return (
      <Link
        href={`/leads/${lead.id}?tab=overview#conversion`}
        className="button-primary justify-center"
      >
        Convert to opportunity
      </Link>
    );
  }
  return (
    <Link
      href={`/leads/${lead.id}?tab=qualification`}
      className="button-primary justify-center"
    >
      {lead.qualification_score
        ? "Review qualification"
        : "Start qualification"}
    </Link>
  );
}

function ConversionCard({
  lead,
  action,
}: {
  lead: Lead;
  action: (formData: FormData) => Promise<void>;
}) {
  return (
    <section id="conversion" className="card scroll-mt-24 p-6">
      <p className="eyebrow">Sales handoff</p>
      <h2 className="mt-3 text-xl font-semibold">Create opportunity</h2>
      {lead.organization_id ? (
        <form action={action} className="mt-5 space-y-4">
          <label className="label mt-0">
            Opportunity name
            <input
              className="field mt-2"
              name="name"
              defaultValue={leadProjectLabel(lead)}
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
        <p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">
          Link a customer company before conversion.
        </p>
      )}
    </section>
  );
}

function TaskRow({ leadId, task }: { leadId: string; task: Task }) {
  const nextStatus =
    task.status === "open"
      ? "in_progress"
      : task.status === "in_progress"
        ? "completed"
        : "open";
  const action = updateTask.bind(
    null,
    leadId,
    task.id,
    task.version,
    nextStatus,
  );
  return (
    <div className="py-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-semibold">{task.title}</p>
          <p className="mt-1 text-xs text-[var(--color-muted)]">
            {task.due_at ? `Due ${formatDateTime(task.due_at)}` : "No due date"}
          </p>
        </div>
        <StatusBadge tone={task.status === "completed" ? "success" : "neutral"}>
          {task.status.replaceAll("_", " ")}
        </StatusBadge>
      </div>
      {task.description ? (
        <p className="mt-2 text-sm leading-6 text-[var(--color-muted)]">
          {task.description}
        </p>
      ) : null}
      <form action={action} className="mt-3">
        <button className="button-secondary">
          {nextStatus === "in_progress"
            ? "Start"
            : nextStatus === "completed"
              ? "Complete"
              : "Reopen"}
        </button>
      </form>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <dt className="text-xs font-bold uppercase tracking-[0.09em] text-[var(--color-muted)]">
        {label}
      </dt>
      <dd className="mt-2 text-sm font-semibold">{value || "Not confirmed"}</dd>
    </div>
  );
}

function SummaryFact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[0.65rem] font-bold uppercase tracking-[0.12em] text-[var(--color-muted)]">
        {label}
      </dt>
      <dd className="mt-1 text-sm font-semibold capitalize">{value}</dd>
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

function SelectField({
  label,
  name,
  value,
  options,
}: {
  label: string;
  name: string;
  value: string;
  options: string[];
}) {
  return (
    <label className="label">
      {label}
      <select className="field mt-2" name={name} defaultValue={value}>
        {options.map((option) => (
          <option key={option} value={option}>
            {option.replaceAll("_", " ")}
          </option>
        ))}
      </select>
    </label>
  );
}

function contactName(contact: Contact | null) {
  if (!contact) return "Contact not linked";
  return (
    [contact.first_name, contact.last_name].filter(Boolean).join(" ") ||
    contact.email ||
    "Contact record"
  );
}

function taskTime(task: Task) {
  return task.due_at
    ? new Date(task.due_at).getTime()
    : Number.MAX_SAFE_INTEGER;
}

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
}
