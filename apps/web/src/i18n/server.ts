import { cookies } from "next/headers";

import { defaultLocale, isLocale, localeCookie, type Locale } from "./config";
import { messagesFor } from "./messages";

export async function getLocale(): Promise<Locale> {
  const value = (await cookies()).get(localeCookie)?.value;
  return isLocale(value) ? value : defaultLocale;
}

export async function getMessages() {
  return messagesFor(await getLocale());
}
