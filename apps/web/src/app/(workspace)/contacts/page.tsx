import Link from "next/link";

import { getLocale } from "@/i18n/server";
import { apiFetch, type Contact, type Organization } from "@/lib/api";

import { createContact, updateContact } from "../actions";

export default async function ContactsPage({
  searchParams,
}: PageProps<"/contacts">) {
  const query = await searchParams;
  const search = single(query.search);
  const organizationId = single(query.organization_id);
  const editId = single(query.edit);
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
  const editing = contacts.find((item) => item.id === editId) ?? null;
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
        edit: "修改",
        editTitle: "修改联系人资料",
        updated: "联系人资料已保存。",
        cancel: "取消",
        add: "添加联系人",
        firstName: "名",
        lastName: "姓",
        email: "邮箱",
        phone: "电话（E.164）",
        jobTitle: "职位",
        whatsapp: "WhatsApp（E.164）",
        language: "首选语言",
        consent: "营销同意状态",
        doNotContact: "禁止联系此联系人",
        save: "保存联系人",
        saveChanges: "保存修改",
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
        edit: "Edit",
        editTitle: "Edit contact details",
        updated: "Contact details saved.",
        cancel: "Cancel",
        add: "Add contact",
        firstName: "First name",
        lastName: "Last name",
        email: "Email",
        phone: "Phone (E.164)",
        jobTitle: "Job title",
        whatsapp: "WhatsApp (E.164)",
        language: "Preferred language",
        consent: "Marketing consent",
        doNotContact: "Do not contact this person",
        save: "Save contact",
        saveChanges: "Save changes",
      };

  return (
    <div>
      <header>
        <p className="eyebrow">CRM</p>
        <h1 className="page-title">{copy.title}</h1>
        <p className="mt-2 text-[var(--muted)]">{copy.description}</p>
      </header>

      {single(query.updated) ? (
        <p className="mt-5 rounded-xl border border-[var(--color-success)]/25 bg-[var(--color-success-soft)] px-4 py-3 text-sm font-semibold text-[var(--color-success)]">
          {copy.updated}
        </p>
      ) : null}

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
                    <div className="flex flex-wrap items-center gap-2">
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
                      <Link
                        className="button-tertiary px-3 py-2"
                        href={`/contacts?edit=${item.id}`}
                      >
                        {copy.edit}
                      </Link>
                    </div>
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

        {editing ? (
          <form
            key={`${editing.id}-${editing.version}`}
            action={updateContact.bind(null, editing.id, editing.version)}
            className="card h-fit scroll-mt-24 p-6"
          >
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold">{copy.editTitle}</h2>
              <Link className="button-tertiary px-3 py-2" href="/contacts">
                {copy.cancel}
              </Link>
            </div>
            <CompanySelect
              label={copy.company}
              unlinked={copy.unlinked}
              organizations={organizations}
              value={editing.organization_id ?? ""}
            />
            <div className="grid grid-cols-2 gap-3">
              <Field
                label={copy.firstName}
                name="first_name"
                defaultValue={editing.first_name}
              />
              <Field
                label={copy.lastName}
                name="last_name"
                defaultValue={editing.last_name}
              />
            </div>
            <Field
              label={copy.email}
              name="email"
              type="email"
              defaultValue={editing.email}
            />
            <Field
              label={copy.phone}
              name="phone_e164"
              placeholder="+628..."
              defaultValue={editing.phone_e164}
            />
            <Field
              label={copy.whatsapp}
              name="whatsapp_e164"
              placeholder="+628..."
              defaultValue={editing.whatsapp_e164}
            />
            <Field
              label={copy.jobTitle}
              name="job_title"
              defaultValue={editing.job_title}
            />
            <OptionSelect
              label={copy.language}
              name="preferred_language"
              value={editing.preferred_language ?? ""}
              options={["", "en", "zh-CN", "id"]}
            />
            <OptionSelect
              label={copy.consent}
              name="marketing_consent_status"
              value={editing.marketing_consent_status}
              options={["unknown", "granted", "denied", "withdrawn"]}
            />
            <label className="mt-5 flex items-center gap-3 text-sm font-semibold">
              <input
                className="h-4 w-4 accent-[var(--color-brand)]"
                type="checkbox"
                name="do_not_contact"
                defaultChecked={editing.do_not_contact}
              />
              {copy.doNotContact}
            </label>
            <button className="button-primary mt-6 w-full">
              {copy.saveChanges}
            </button>
          </form>
        ) : (
          <form action={createContact} className="card h-fit p-6">
            <h2 className="text-lg font-semibold">{copy.add}</h2>
            <CompanySelect
              label={copy.company}
              unlinked={copy.unlinked}
              organizations={organizations}
              value=""
            />
            <div className="grid grid-cols-2 gap-3">
              <Field label={copy.firstName} name="first_name" />
              <Field label={copy.lastName} name="last_name" />
            </div>
            <Field label={copy.email} name="email" type="email" />
            <Field label={copy.phone} name="phone_e164" placeholder="+628..." />
            <Field label={copy.jobTitle} name="job_title" />
            <button className="button-primary mt-6 w-full">{copy.save}</button>
          </form>
        )}
      </div>
    </div>
  );
}

function Field({
  label,
  name,
  type = "text",
  placeholder,
  defaultValue,
}: {
  label: string;
  name: string;
  type?: string;
  placeholder?: string;
  defaultValue?: string | null;
}) {
  return (
    <label className="mt-4 block text-sm font-semibold">
      {label}
      <input
        className="field mt-2"
        name={name}
        type={type}
        placeholder={placeholder}
        defaultValue={defaultValue ?? ""}
      />
    </label>
  );
}

function CompanySelect({
  label,
  unlinked,
  organizations,
  value,
}: {
  label: string;
  unlinked: string;
  organizations: Organization[];
  value: string;
}) {
  return (
    <label className="mt-4 block text-sm font-semibold">
      {label}
      <select
        className="field mt-2"
        name="organization_id"
        defaultValue={value}
      >
        <option value="">{unlinked}</option>
        {organizations.map((item) => (
          <option key={item.id} value={item.id}>
            {item.display_name}
          </option>
        ))}
      </select>
    </label>
  );
}

function OptionSelect({
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
    <label className="mt-4 block text-sm font-semibold">
      {label}
      <select className="field mt-2" name={name} defaultValue={value}>
        {options.map((option) => (
          <option key={option || "unset"} value={option}>
            {option || "—"}
          </option>
        ))}
      </select>
    </label>
  );
}

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
}
