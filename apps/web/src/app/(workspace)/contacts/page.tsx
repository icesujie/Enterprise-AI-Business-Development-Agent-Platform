import Link from "next/link";

import { getLocale } from "@/i18n/server";
import { apiFetch, type Contact, type Organization } from "@/lib/api";

import { createContact } from "../actions";

export default async function ContactsPage({
  searchParams,
}: PageProps<"/contacts">) {
  const query = await searchParams;
  const search = single(query.search);
  const organizationId = single(query.organization_id);
  const params = new URLSearchParams({ limit: "100" });
  if (search) params.set("search", search);
  if (organizationId) params.set("organization_id", organizationId);

  const [contacts, organizations, locale] = await Promise.all([
    apiFetch<Contact[]>(`/api/v1/contacts?${params}`),
    apiFetch<Organization[]>("/api/v1/organizations?limit=100"),
    getLocale(),
  ]);
  const companies = new Map(
    organizations.map((organization) => [
      organization.id,
      organization.display_name,
    ]),
  );
  const zh = locale === "zh-CN";
  const copy = zh
    ? {
        title: "联系人",
        description: "管理客户联系人，并明确显示其所属公司。",
        search: "查找联系人",
        searchPlaceholder: "姓名、邮箱、电话或公司",
        company: "公司",
        allCompanies: "所有公司",
        searchAction: "查找",
        clear: "清除",
        unlinked: "未关联公司",
        noContacts: "没有找到联系人",
        add: "添加联系人",
        firstName: "名",
        lastName: "姓",
        email: "邮箱",
        phone: "电话（E.164）",
        jobTitle: "职位",
        save: "保存联系人",
      }
    : {
        title: "Contacts",
        description:
          "Manage customer contacts with a clear company relationship.",
        search: "Find a contact",
        searchPlaceholder: "Name, email, phone, or company",
        company: "Company",
        allCompanies: "All companies",
        searchAction: "Search",
        clear: "Clear",
        unlinked: "Unlinked contact",
        noContacts: "No contacts found",
        add: "Add contact",
        firstName: "First name",
        lastName: "Last name",
        email: "Email",
        phone: "Phone (E.164)",
        jobTitle: "Job title",
        save: "Save contact",
      };

  return (
    <div>
      <header>
        <p className="eyebrow">CRM</p>
        <h1 className="page-title">{copy.title}</h1>
        <p className="mt-2 text-[var(--muted)]">{copy.description}</p>
      </header>

      <form
        action="/contacts"
        className="mt-7 grid gap-3 rounded-2xl border border-[var(--color-line)] bg-white p-4 md:grid-cols-[minmax(220px,1fr)_260px_auto_auto] md:items-end"
      >
        <label className="label mt-0">
          {copy.search}
          <input
            className="field mt-2"
            name="search"
            defaultValue={search}
            placeholder={copy.searchPlaceholder}
          />
        </label>
        <label className="label mt-0">
          {copy.company}
          <select
            className="field mt-2"
            name="organization_id"
            defaultValue={organizationId}
          >
            <option value="">{copy.allCompanies}</option>
            {organizations.map((item) => (
              <option key={item.id} value={item.id}>
                {item.display_name}
              </option>
            ))}
          </select>
        </label>
        <button className="button-primary md:mb-px" type="submit">
          {copy.searchAction}
        </button>
        {search || organizationId ? (
          <Link className="button-tertiary md:mb-px" href="/contacts">
            {copy.clear}
          </Link>
        ) : null}
      </form>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_360px]">
        <section className="card overflow-hidden">
          {contacts.length ? (
            contacts.map((item) => {
              const companyName = item.organization_id
                ? companies.get(item.organization_id)
                : null;
              return (
                <article
                  key={item.id}
                  className="border-b border-[var(--color-line)] px-5 py-5 last:border-0 sm:px-6"
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0">
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
                    {item.organization_id && companyName ? (
                      <Link
                        className="w-fit rounded-full bg-[var(--color-surface-soft)] px-3 py-1.5 text-xs font-bold text-[var(--color-brand)] hover:underline"
                        href={`/organizations?search=${encodeURIComponent(companyName)}`}
                      >
                        {companyName}
                      </Link>
                    ) : (
                      <span className="w-fit rounded-full border border-dashed border-[var(--color-line)] px-3 py-1.5 text-xs font-semibold text-[var(--color-muted)]">
                        {copy.unlinked}
                      </span>
                    )}
                  </div>
                </article>
              );
            })
          ) : (
            <p className="p-8 text-center text-sm text-[var(--muted)]">
              {copy.noContacts}
            </p>
          )}
        </section>

        <form action={createContact} className="card h-fit p-6">
          <h2 className="text-lg font-semibold">{copy.add}</h2>
          <label className="mt-4 block text-sm font-semibold">
            {copy.company}
            <select className="field mt-2" name="organization_id">
              <option value="">{copy.unlinked}</option>
              {organizations.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.display_name}
                </option>
              ))}
            </select>
          </label>
          <div className="grid grid-cols-2 gap-3">
            <Field label={copy.firstName} name="first_name" />
            <Field label={copy.lastName} name="last_name" />
          </div>
          <Field label={copy.email} name="email" type="email" />
          <Field label={copy.phone} name="phone_e164" placeholder="+628..." />
          <Field label={copy.jobTitle} name="job_title" />
          <button className="button-primary mt-6 w-full">{copy.save}</button>
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

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
}
