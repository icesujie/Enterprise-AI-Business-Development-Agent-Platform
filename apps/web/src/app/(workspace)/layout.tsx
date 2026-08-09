import Link from "next/link";

import { WorkspaceNav } from "@/components/workspace/workspace-nav";
import { WorkspaceTopbar } from "@/components/workspace/workspace-topbar";
import { getMessages } from "@/i18n/server";

export const dynamic = "force-dynamic";

export default async function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { workspace: copy } = await getMessages();
  return (
    <div className="min-h-screen bg-[#eef0eb] text-[var(--color-ink)]">
      <a href="#workspace-content" className="skip-link">
        {copy.skip}
      </a>
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[248px] bg-[var(--color-brand-strong)] px-5 py-6 text-white lg:flex lg:flex-col">
        <Link
          href="/dashboard"
          className="flex items-center gap-3 border-b border-white/10 pb-6"
          aria-label="Sari Arta dashboard"
        >
          <span className="grid h-10 w-10 place-items-center rounded-full bg-white text-xs font-black text-[var(--color-brand)]">
            SA
          </span>
          <span>
            <span className="block text-sm font-extrabold tracking-[0.12em]">
              SARI ARTA
            </span>
            <span className="mt-1 block text-[0.62rem] uppercase tracking-[0.14em] text-white/40">
              Business Development
            </span>
          </span>
        </Link>
        <div className="mt-7 min-h-0 flex-1">
          <WorkspaceNav />
        </div>
      </aside>
      <div className="lg:pl-[248px]">
        <WorkspaceTopbar copy={copy} />
        <div className="border-b border-[var(--color-line)] bg-[var(--color-brand-strong)] px-4 py-3 lg:hidden">
          <div
            className="flex gap-2 overflow-x-auto"
            aria-label={copy.mobileNavigation}
          >
            {[
              [copy.dashboard, "/dashboard"],
              [copy.leads, "/leads"],
              [copy.opportunities, "/opportunities"],
              [copy.followUp, "/follow-up"],
            ].map(([label, href]) => (
              <Link
                key={href}
                href={href}
                className="shrink-0 rounded-lg bg-white/8 px-4 py-2 text-xs font-semibold text-white/75"
              >
                {label}
              </Link>
            ))}
          </div>
        </div>
        <main
          id="workspace-content"
          className="mx-auto w-full max-w-[1500px] px-5 py-7 sm:px-8 sm:py-9 lg:px-10"
        >
          {children}
        </main>
      </div>
    </div>
  );
}
