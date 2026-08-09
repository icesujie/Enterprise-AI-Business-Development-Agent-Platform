"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";

import { isLocale, localeCookie } from "@/i18n/config";

export async function setLanguage(locale: string) {
  if (!isLocale(locale)) return;
  (await cookies()).set(localeCookie, locale, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 365,
  });
  revalidatePath("/", "layout");
}
