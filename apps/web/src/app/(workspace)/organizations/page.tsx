import Link from "next/link";

import { getLocale } from "@/i18n/server";
import { apiFetch, type Organization } from "@/lib/api";

import { createOrganization, updateOrganization } from "../actions";

export default async function OrganizationsPage({
  searchParams,
}: PageProps<"/organizations">) {
  const query = await searchParams;
  const search = single(query.search);
  const editId = single(query.edit);
  const params = new URLSearchParams({ limit: "100" });
  if (search) params.set("search", search);

  const [organizations, locale] = await Promise.all([
    apiFetch<Organization[]>(`/api/v1/organizations?${params}`),
    getLocale(),
  ]);
  const editing = organizations.find((item) => item.id === editId) ?? null;
  const zh = locale === "zh-CN";
  const copy = zh
    ? {
        title: "公司",
        description: "管理客户公司，并查看每家公司关联的联系人。",
        search: "查找公司",
        searchPlaceholder: "按公司名称或域名查找",
        searchAction: "查找",
        clear: "清除",
        noCompanies: "没有找到公司",
        noDetails: "尚未添加详细信息",
        contacts: "位联系人",
        viewContacts: "查看联系人",
        edit: "修改",
        editTitle: "修改公司资料",
        updated: "公司资料已保存。",
        cancel: "取消",
        add: "添加公司",
        legalName: "公司法定名称",
        displayName: "显示名称",
        website: "网站",
        domain: "网站域名",
        industry: "行业",
        country: "国家代码",
        city: "城市",
        language: "首选语言",
        lifecycle: "客户阶段",
        save: "保存公司",
        saveChanges: "保存修改",
      }
    : {
        title: "Companies",
        description: "Manage customer companies and their linked contacts.",
        search: "Find a company",
        searchPlaceholder: "Search by company name or domain",
        searchAction: "Search",
        clear: "Clear",
        noCompanies: "No companies found",
        noDetails: "Details not added",
        contacts: " contacts",
        viewContacts: "View contacts",
        edit: "Edit",
        editTitle: "Edit company details",
        updated: "Company details saved.",
        cancel: "Cancel",
        add: "Add company",
        legalName: "Legal name",
        displayName: "Display name",
        website: "Website",
        domain: "Website domain",
        industry: "Industry",
        country: "Country code",
        city: "City",
        language: "Preferred language",
        lifecycle: "Customer stage",
        save: "Save company",
        saveChanges: "Save changes",
      };

  return (
    <div>
      <PageHeading title={copy.title} description={copy.description} />

      {single(query.updated) ? (
        <p className="mt-5 rounded-xl border border-[var(--color-success)]/25 bg-[var(--color-success-soft)] px-4 py-3 text-sm font-semibold text-[var(--color-success)]">
          {copy.updated}
        </p>
      ) : null}

      <form
        action="/organizations"
        className="mt-7 flex flex-col gap-3 rounded-2xl border border-[var(--color-line)] bg-white p-4 sm:flex-row sm:items-end"
      >
        <label className="label mt-0 min-w-0 flex-1">
          {copy.search}
          <input
            className="field mt-2"
            name="search"
            defaultValue={search}
            placeholder={copy.searchPlaceholder}
          />
        </label>
        <button className="button-primary sm:mb-px" type="submit">
          {copy.searchAction}
        </button>
        {search ? (
          <Link className="button-tertiary sm:mb-px" href="/organizations">
            {copy.clear}
          </Link>
        ) : null}
      </form>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_360px]">
        <section className="card overflow-hidden">
          {organizations.length ? (
            organizations.map((item) => (
              <article
                key={item.id}
                className="border-b border-[var(--color-line)] px-5 py-5 last:border-0 sm:px-6"
              >
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold">{item.display_name}</p>
                      <span className="status-chip">
                        {item.lifecycle_stage}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-[var(--muted)]">
                      {[item.city, item.country_code, item.domain]
                        .filter(Boolean)
                        .join(" · ") || copy.noDetails}
                    </p>
                  </div>
                  <div className="flex shrink-0 flex-wrap items-center justify-between gap-4 sm:justify-end">
                    <span className="rounded-full bg-[var(--color-surface-soft)] px-3 py-1.5 text-xs font-bold text-[var(--color-ink)]">
                      {item.contact_count ?? 0}
                      {copy.contacts}
                    </span>
                    <Link
                      className="text-sm font-bold text-[var(--color-brand)] hover:underline"
                      href={`/contacts?organization_id=${item.id}`}
                    >
                      {copy.viewContacts} →
                    </Link>
                    <Link
                      className="button-tertiary px-3 py-2"
                      href={`/organizations?edit=${item.id}`}
                    >
                      {copy.edit}
                    </Link>
                  </div>
                </div>
              </article>
            ))
          ) : (
            <EmptyState label={copy.noCompanies} />
          )}
        </section>

        {editing ? (
          <form
            key={`${editing.id}-${editing.version}`}
            action={updateOrganization.bind(null, editing.id, editing.version)}
            className="card h-fit scroll-mt-24 p-6"
          >
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold">{copy.editTitle}</h2>
              <Link className="button-tertiary px-3 py-2" href="/organizations">
                {copy.cancel}
              </Link>
            </div>
            <FormField
              label={copy.legalName}
              name="legal_name"
              defaultValue={editing.legal_name}
              required
            />
            <FormField
              label={copy.displayName}
              name="display_name"
              defaultValue={editing.display_name}
              required
            />
            <FormField
              label={copy.website}
              name="website_url"
              type="url"
              defaultValue={editing.website_url}
            />
            <FormField
              label={copy.domain}
              name="domain"
              defaultValue={editing.domain}
            />
            <FormField
              label={copy.industry}
              name="industry"
              defaultValue={editing.industry}
            />
            <div className="grid grid-cols-2 gap-3">
              <FormField
                label={copy.country}
                name="country_code"
                maxLength={2}
                defaultValue={editing.country_code}
              />
              <FormField
                label={copy.city}
                name="city"
                defaultValue={editing.city}
              />
            </div>
            <SelectField
              label={copy.language}
              name="preferred_language"
              value={editing.preferred_language ?? ""}
              options={["", "en", "zh-CN", "id"]}
            />
            <SelectField
              label={copy.lifecycle}
              name="lifecycle_stage"
              value={editing.lifecycle_stage}
              options={["prospect", "qualified", "customer", "inactive"]}
            />
            <button className="button-primary mt-6 w-full">
              {copy.saveChanges}
            </button>
          </form>
        ) : (
          <form action={createOrganization} className="card h-fit p-6">
            <h2 className="text-lg font-semibold">{copy.add}</h2>
            <FormField label={copy.legalName} name="legal_name" required />
            <FormField label={copy.website} name="website_url" type="url" />
            <FormField label={copy.industry} name="industry" />
            <div className="grid grid-cols-2 gap-3">
              <FormField
                label={copy.country}
                name="country_code"
                maxLength={2}
              />
              <FormField label={copy.city} name="city" />
            </div>
            <button className="button-primary mt-6 w-full">{copy.save}</button>
          </form>
        )}
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
  defaultValue,
  ...props
}: {
  label: string;
  name: string;
  type?: string;
  required?: boolean;
  maxLength?: number;
  defaultValue?: string | null;
}) {
  return (
    <label className="mt-4 block text-sm font-semibold">
      {label}
      <input
        className="field mt-2"
        name={name}
        type={type}
        defaultValue={defaultValue ?? ""}
        {...props}
      />
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
