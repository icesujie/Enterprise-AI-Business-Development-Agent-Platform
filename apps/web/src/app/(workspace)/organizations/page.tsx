import { apiFetch, type Organization } from "@/lib/api";

import { createOrganization } from "../actions";

export default async function OrganizationsPage() {
  const organizations = await apiFetch<Organization[]>("/api/v1/organizations");
  return (
    <div>
      <PageHeading
        title="Companies"
        description="Customer and prospect organizations"
      />
      <div className="mt-7 grid gap-6 xl:grid-cols-[1fr_360px]">
        <section className="card overflow-hidden">
          {organizations.length ? (
            organizations.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between border-b border-[var(--line)] px-6 py-5 last:border-0"
              >
                <div>
                  <p className="font-semibold">{item.display_name}</p>
                  <p className="mt-1 text-sm text-[var(--muted)]">
                    {[item.city, item.country_code, item.domain]
                      .filter(Boolean)
                      .join(" · ") || "Details not added"}
                  </p>
                </div>
                <span className="status-chip">{item.lifecycle_stage}</span>
              </div>
            ))
          ) : (
            <EmptyState label="No companies yet" />
          )}
        </section>
        <form action={createOrganization} className="card h-fit p-6">
          <h2 className="text-lg font-semibold">Add company</h2>
          <FormField label="Legal name" name="legal_name" required />
          <FormField label="Website" name="website_url" type="url" />
          <FormField label="Industry" name="industry" />
          <div className="grid grid-cols-2 gap-3">
            <FormField label="Country" name="country_code" maxLength={2} />
            <FormField label="City" name="city" />
          </div>
          <button className="button-primary mt-6 w-full">Save company</button>
        </form>
      </div>
    </div>
  );
}

function PageHeading({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <header>
      <p className="eyebrow">CRM</p>
      <h1 className="page-title">{title}</h1>
      <p className="mt-2 text-[var(--muted)]">{description}</p>
    </header>
  );
}
function EmptyState({ label }: { label: string }) {
  return <p className="p-8 text-center text-sm text-[var(--muted)]">{label}</p>;
}
function FormField({
  label,
  name,
  type = "text",
  ...props
}: {
  label: string;
  name: string;
  type?: string;
  required?: boolean;
  maxLength?: number;
}) {
  return (
    <label className="mt-4 block text-sm font-semibold">
      {label}
      <input className="field mt-2" name={name} type={type} {...props} />
    </label>
  );
}
