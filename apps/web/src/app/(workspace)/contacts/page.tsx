import { apiFetch, type Contact, type Organization } from "@/lib/api";

import { createContact } from "../actions";

export default async function ContactsPage() {
  const [contacts, organizations] = await Promise.all([
    apiFetch<Contact[]>("/api/v1/contacts"),
    apiFetch<Organization[]>("/api/v1/organizations"),
  ]);
  return (
    <div>
      <header>
        <p className="eyebrow">CRM</p>
        <h1 className="page-title">Contacts</h1>
        <p className="mt-2 text-[var(--muted)]">
          People connected to active projects and inquiries
        </p>
      </header>
      <div className="mt-7 grid gap-6 xl:grid-cols-[1fr_360px]">
        <section className="card overflow-hidden">
          {contacts.length ? (
            contacts.map((item) => (
              <div
                key={item.id}
                className="border-b border-[var(--line)] px-6 py-5 last:border-0"
              >
                <p className="font-semibold">
                  {[item.first_name, item.last_name]
                    .filter(Boolean)
                    .join(" ") || item.email}
                </p>
                <p className="mt-1 text-sm text-[var(--muted)]">
                  {[item.job_title, item.email, item.phone_e164]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
              </div>
            ))
          ) : (
            <p className="p-8 text-center text-sm text-[var(--muted)]">
              No contacts yet
            </p>
          )}
        </section>
        <form action={createContact} className="card h-fit p-6">
          <h2 className="text-lg font-semibold">Add contact</h2>
          <label className="mt-4 block text-sm font-semibold">
            Company
            <select className="field mt-2" name="organization_id">
              <option value="">Unlinked</option>
              {organizations.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.display_name}
                </option>
              ))}
            </select>
          </label>
          <div className="grid grid-cols-2 gap-3">
            <Field label="First name" name="first_name" />
            <Field label="Last name" name="last_name" />
          </div>
          <Field label="Email" name="email" type="email" />
          <Field
            label="Phone (E.164)"
            name="phone_e164"
            placeholder="+628..."
          />
          <Field label="Job title" name="job_title" />
          <button className="button-primary mt-6 w-full">Save contact</button>
        </form>
      </div>
    </div>
  );
}
function Field({
  label,
  name,
  type = "text",
  placeholder,
}: {
  label: string;
  name: string;
  type?: string;
  placeholder?: string;
}) {
  return (
    <label className="mt-4 block text-sm font-semibold">
      {label}
      <input
        className="field mt-2"
        name={name}
        type={type}
        placeholder={placeholder}
      />
    </label>
  );
}
