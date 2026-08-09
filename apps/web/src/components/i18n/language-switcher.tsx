"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";

import { setLanguage } from "@/app/language-actions";
import { useI18n } from "@/i18n/context";

export function LanguageSwitcher({ compact = false }: { compact?: boolean }) {
  const router = useRouter();
  const { locale, messages } = useI18n();
  const [isPending, startTransition] = useTransition();

  return (
    <div>
      <label
        className="sr-only"
        htmlFor={`language-${compact ? "compact" : "full"}`}
      >
        {messages.language.label}
      </label>
      <select
        key={locale}
        id={`language-${compact ? "compact" : "full"}`}
        defaultValue={locale}
        onChange={(event) => {
          const nextLocale = event.target.value as "en" | "zh-CN";
          startTransition(async () => {
            await setLanguage(nextLocale);
            router.refresh();
          });
        }}
        disabled={isPending}
        className={
          compact
            ? "min-h-9 min-w-[6.75rem] rounded-lg border border-[var(--color-line)] bg-[var(--color-surface-subtle)] px-3 text-xs font-bold text-[var(--color-ink)] shadow-sm outline-none transition hover:border-[var(--color-brand)] focus:border-[var(--color-brand)] focus:ring-2 focus:ring-[var(--color-brand)]/20 disabled:opacity-60"
            : "min-h-10 rounded-lg border border-[var(--color-line)] bg-white px-3 text-sm font-semibold text-[var(--color-ink)]"
        }
        aria-label={messages.language.label}
      >
        <option className="text-[var(--color-ink)]" value="en">
          English
        </option>
        <option className="text-[var(--color-ink)]" value="zh-CN">
          中文
        </option>
      </select>
    </div>
  );
}
