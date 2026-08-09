"use client";

import { useRef, useState } from "react";

import { setLanguage } from "@/app/language-actions";
import { useI18n } from "@/i18n/context";

export function LanguageSwitcher({ compact = false }: { compact?: boolean }) {
  const form = useRef<HTMLFormElement>(null);
  const { locale, messages } = useI18n();
  const [selectedLocale, setSelectedLocale] = useState(locale);
  return (
    <form action={setLanguage} ref={form}>
      <label
        className="sr-only"
        htmlFor={`language-${compact ? "compact" : "full"}`}
      >
        {messages.language.label}
      </label>
      <select
        id={`language-${compact ? "compact" : "full"}`}
        name="locale"
        value={selectedLocale}
        onChange={(event) => {
          setSelectedLocale(event.target.value as "en" | "zh-CN");
          form.current?.requestSubmit();
        }}
        className={
          compact
            ? "min-h-9 rounded-lg border border-white/15 bg-white/10 px-2 text-xs font-bold text-white"
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
    </form>
  );
}
