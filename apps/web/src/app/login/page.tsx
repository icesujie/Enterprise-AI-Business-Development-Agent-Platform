import type { Metadata } from "next";

import { login } from "./actions";
import { LanguageSwitcher } from "@/components/i18n/language-switcher";
import { getMessages } from "@/i18n/server";
import { getDemoAuthConfig } from "@/lib/demo-auth";
import { privateMetadata } from "@/lib/seo";

export const metadata: Metadata = privateMetadata;

export default async function LoginPage({
  searchParams,
}: {
  searchParams?: Promise<{ error?: string }>;
}) {
  const demo = getDemoAuthConfig();
  const { login: copy } = await getMessages();
  const error = (await searchParams)?.error;
  return (
    <main className="grid min-h-screen place-items-center bg-[var(--canvas)] px-6">
      <div className="w-full max-w-md rounded-3xl border border-[var(--line)] bg-white p-8 shadow-xl">
        <p className="text-xs font-bold uppercase tracking-[0.22em] text-[var(--accent)]">
          Sari Arta
        </p>
        <div className="mt-3 flex items-start justify-between gap-4">
          <h1 className="text-3xl font-semibold tracking-tight">
            {copy.title}
          </h1>
          <LanguageSwitcher />
        </div>
        <p className="mt-2 text-sm text-[var(--muted)]">{copy.description}</p>
        {demo ? (
          <div className="mt-6 rounded-xl border border-[var(--color-line)] bg-[var(--color-surface-subtle)] p-4 text-sm">
            <p className="font-semibold">{copy.demoAccount}</p>
            <p className="mt-2 text-[var(--color-muted)]">
              {copy.email}: {demo.email}
            </p>
            <p className="mt-1 text-[var(--color-muted)]">
              {copy.password}: {demo.password}
            </p>
          </div>
        ) : null}
        {error ? (
          <p
            className="mt-5 rounded-xl border border-[var(--color-danger)]/30 bg-[var(--color-danger-soft)] p-3 text-sm text-[var(--color-danger)]"
            role="alert"
          >
            {error === "auth_unavailable" ? copy.unavailable : copy.failed}
          </p>
        ) : null}
        <form action={login}>
          <label className="mt-8 block text-sm font-semibold" htmlFor="email">
            {copy.email}
          </label>
          <input
            className="field mt-2"
            id="email"
            name="email"
            type="email"
            required
            autoComplete="email"
          />
          <label
            className="mt-5 block text-sm font-semibold"
            htmlFor="password"
          >
            {copy.password}
          </label>
          <input
            className="field mt-2"
            id="password"
            name="password"
            type="password"
            required
            autoComplete="current-password"
          />
          <button className="button-primary mt-7 w-full" type="submit">
            {copy.signIn}
          </button>
        </form>
      </div>
    </main>
  );
}
