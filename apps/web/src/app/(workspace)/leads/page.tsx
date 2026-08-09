import Link from "next/link";

import {
  apiFetch,
  type Contact,
  type LeadList,
  type Organization,
} from "@/lib/api";

import { createLead } from "../actions";

export default async function LeadsPage() {
  const [data, organizations, contacts] = await Promise.all([
    apiFetch<LeadList>("/api/v1/leads"),
    apiFetch<Organization[]>("/api/v1/organizations"),
    apiFetch<Contact[]>("/api/v1/contacts"),
  ]);
  return (
    <div>
      <header className="flex items-end justify-between gap-6">
        <div>
          <p className="eyebrow">Sales queue</p>
          <h1 className="page-title">Leads</h1>
          <p className="mt-2 text-[var(--muted)]">
            Capture, prioritize, and qualify commercial-kitchen opportunities
          </p>
        </div>
        <span className="rounded-2xl bg-white px-5 py-3 text-sm font-semibold shadow-sm">
          {data.items.length} active records
        </span>
      </header>
      <div className="mt-7 grid gap-6 xl:grid-cols-[1fr_380px]">
        <section className="card overflow-hidden">
          {data.items.length ? (
            data.items.map((lead) => (
              <Link
                href={`/leads/${lead.id}`}
                key={lead.id}
                className="grid gap-3 border-b border-[var(--line)] px-6 py-5 transition hover:bg-[#fafbf8] last:border-0 sm:grid-cols-[1fr_auto] sm:items-center"
              >
                <div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`priority-dot priority-${lead.priority}`}
                      aria-hidden="true"
                    />
                    <p className="font-semibold">{lead.inquiry_summary}</p>
                  </div>
                  <p className="mt-2 text-sm text-[var(--muted)]">
                    {[
                      lead.project_city,
                      lead.project_country_code,
                      lead.project_type,
                    ]
                      .filter(Boolean)
                      .join(" · ") || "Project details pending"}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="status-chip">{lead.status}</span>
                  <span className="text-xs font-semibold uppercase text-[var(--muted)]">
                    {lead.priority}
                  </span>
                </div>
              </Link>
            ))
          ) : (
            <div className="p-10 text-center">
              <p className="font-semibold">No leads yet</p>
              <p className="mt-2 text-sm text-[var(--muted)]">
                Add the first inquiry using the form.
              </p>
            </div>
          )}
        </section>
        <form action={createLead} className="card h-fit p-6">
          <h2 className="text-lg font-semibold">Add lead</h2>
          <label className="label">
            Company
            <select className="field mt-2" name="organization_id">
              <option value="">Not selected</option>
              {organizations.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.display_name}
                </option>
              ))}
            </select>
          </label>
          <label className="label">
            Contact
            <select className="field mt-2" name="contact_id">
              <option value="">Not selected</option>
              {contacts.map((item) => (
                <option key={item.id} value={item.id}>
                  {[item.first_name, item.last_name]
                    .filter(Boolean)
                    .join(" ") || item.email}
                </option>
              ))}
            </select>
          </label>
          <label className="label">
            Inquiry
            <textarea
              className="field mt-2 min-h-28 resize-y"
              name="inquiry_summary"
              required
              minLength={10}
            />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="label">
              Priority
              <select
                className="field mt-2"
                name="priority"
                defaultValue="normal"
              >
                <option>low</option>
                <option>normal</option>
                <option>high</option>
                <option>urgent</option>
              </select>
            </label>
            <Field label="Country" name="project_country_code" maxLength={2} />
          </div>
          <Field label="Project city" name="project_city" />
          <Field
            label="Project type"
            name="project_type"
            placeholder="Hotel, central kitchen…"
          />
          <Field
            label="Expected capacity"
            name="expected_capacity"
            placeholder="2,000 meals/day"
          />
          <Field label="Target timeline" name="target_timeline" />
          <button className="button-primary mt-6 w-full">Create lead</button>
        </form>
      </div>
    </div>
  );
}
function Field({
  label,
  name,
  placeholder,
  maxLength,
}: {
  label: string;
  name: string;
  placeholder?: string;
  maxLength?: number;
}) {
  return (
    <label className="label">
      {label}
      <input
        className="field mt-2"
        name={name}
        placeholder={placeholder}
        maxLength={maxLength}
      />
    </label>
  );
}
