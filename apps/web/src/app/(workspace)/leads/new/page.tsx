import Link from "next/link";

import { PageHeader } from "@/components/workspace/page-header";
import { apiFetch, type Contact, type Organization } from "@/lib/api";

import { createLead } from "../../actions";

export default async function NewLeadPage() {
  const [organizations, contacts] = await Promise.all([
    apiFetch<Organization[]>("/api/v1/organizations?limit=100"),
    apiFetch<Contact[]>("/api/v1/contacts?limit=100"),
  ]);
  return (
    <div className="mx-auto max-w-4xl">
      <Link href="/leads" className="button-tertiary px-0">
        ← Back to leads
      </Link>
      <div className="mt-4">
        <PageHeader
          eyebrow="Manual capture"
          title="Create lead"
          description="Record an inquiry received outside the public website. Estimates are acceptable and can be refined during qualification."
        />
      </div>
      <form action={createLead} className="card mt-7 p-6 sm:p-8">
        <div className="grid gap-5 sm:grid-cols-2">
          <label className="label mt-0">
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
          <label className="label mt-0">
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
        </div>
        <label className="label">
          Inquiry summary
          <textarea
            className="field mt-2 min-h-36 resize-y"
            name="inquiry_summary"
            required
            minLength={10}
            maxLength={10000}
            placeholder="Describe the facility, operating requirement, location, known scale, timeline, and requested support."
          />
        </label>
        <div className="grid gap-5 sm:grid-cols-2">
          <label className="label">
            Priority
            <select
              className="field mt-2"
              name="priority"
              defaultValue="normal"
            >
              <option value="low">Low</option>
              <option value="normal">Normal</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </label>
          <Field
            label="Project country code"
            name="project_country_code"
            maxLength={2}
            placeholder="ID"
          />
          <Field
            label="Project city"
            name="project_city"
            placeholder="Jakarta"
          />
          <Field
            label="Project type"
            name="project_type"
            placeholder="School kitchen"
          />
          <Field
            label="Expected capacity"
            name="expected_capacity"
            placeholder="1,500 meals/day"
          />
          <Field
            label="Target timeline"
            name="target_timeline"
            placeholder="Target opening Q2 2027"
          />
        </div>
        <div className="mt-7 border-t border-[var(--color-line)] pt-6">
          <button className="button-primary">Create lead</button>
          <p className="mt-3 text-xs leading-5 text-[var(--color-muted)]">
            Creating a lead does not run AI, qualify the opportunity, or contact
            the customer automatically.
          </p>
        </div>
      </form>
    </div>
  );
}

function Field({
  label,
  name,
  placeholder,
  maxLength = 120,
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
