"use client";

import { createContext, useContext } from "react";

import type { Locale } from "./config";
import { messagesFor, type Messages } from "./messages";

const I18nContext = createContext<{ locale: Locale; messages: Messages }>({
  locale: "en",
  messages: messagesFor("en"),
});

export function I18nProvider({
  locale,
  children,
}: {
  locale: Locale;
  children: React.ReactNode;
}) {
  return (
    <I18nContext.Provider value={{ locale, messages: messagesFor(locale) }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  return useContext(I18nContext);
}
