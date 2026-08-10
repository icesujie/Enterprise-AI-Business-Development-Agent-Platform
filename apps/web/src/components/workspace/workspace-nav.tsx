"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useI18n } from "@/i18n/context";

export function WorkspaceNav() {
  const pathname = usePathname();
  const { messages } = useI18n();
  const copy = messages.workspace;
  const primary = [
    [copy.dashboard, "/dashboard"],
    [copy.leads, "/leads"],
    [copy.opportunities, "/opportunities"],
    [copy.followUp, "/follow-up"],
    [copy.agentPlayground, "/agent-playground"],
  ] as const;
  const records = [
    [copy.companies, "/organizations"],
    [copy.contacts, "/contacts"],
  ] as const;
  return (
    <nav aria-label={copy.navigation} className="flex h-full flex-col">
      <NavGroup items={primary} pathname={pathname} />
      <p className="mb-2 mt-8 px-3 text-[0.65rem] font-bold uppercase tracking-[0.18em] text-white/35">
        {copy.records}
      </p>
      <NavGroup items={records} pathname={pathname} />
      <div className="mt-auto border-t border-white/10 pt-5">
        <Link
          href="/"
          className="block rounded-lg px-3 py-2.5 text-sm font-semibold text-white/55 hover:bg-white/8 hover:text-white"
        >
          {copy.publicWebsite}
        </Link>
      </div>
    </nav>
  );
}

function NavGroup({
  items,
  pathname,
}: {
  items: readonly (readonly [string, string])[];
  pathname: string;
}) {
  return items.map(([label, href]) => {
    const active =
      pathname === href ||
      (href !== "/dashboard" && pathname.startsWith(`${href}/`));
    return (
      <Link
        key={href}
        href={href}
        aria-current={active ? "page" : undefined}
        className={`mb-1 block rounded-lg border-l-2 px-3 py-2.5 text-sm font-semibold transition ${active ? "border-[#d18867] bg-white/10 text-white" : "border-transparent text-white/58 hover:bg-white/7 hover:text-white"}`}
      >
        {label}
      </Link>
    );
  });
}
