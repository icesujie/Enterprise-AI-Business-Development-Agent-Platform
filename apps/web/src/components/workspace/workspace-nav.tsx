"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const primary = [
  ["Dashboard", "/dashboard"],
  ["Leads", "/leads"],
  ["Opportunities", "/opportunities"],
  ["Follow-up", "/follow-up"],
] as const;
const records = [
  ["Companies", "/organizations"],
  ["Contacts", "/contacts"],
] as const;

export function WorkspaceNav() {
  const pathname = usePathname();
  return (
    <nav aria-label="Workspace navigation" className="flex h-full flex-col">
      <NavGroup items={primary} pathname={pathname} />
      <p className="mb-2 mt-8 px-3 text-[0.65rem] font-bold uppercase tracking-[0.18em] text-white/35">
        Records
      </p>
      <NavGroup items={records} pathname={pathname} />
      <div className="mt-auto border-t border-white/10 pt-5">
        <Link
          href="/"
          className="block rounded-lg px-3 py-2.5 text-sm font-semibold text-white/55 hover:bg-white/8 hover:text-white"
        >
          Public website
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
