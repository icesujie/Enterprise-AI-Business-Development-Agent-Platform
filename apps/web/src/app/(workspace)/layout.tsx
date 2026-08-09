import Link from "next/link";

const navigation = [
  ["Leads", "/leads"],
  ["Companies", "/organizations"],
  ["Contacts", "/contacts"],
  ["Tasks", "/tasks"],
] as const;

export const dynamic = "force-dynamic";

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[var(--canvas)] text-[var(--ink)]">
      <header className="border-b border-[var(--line)] bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 lg:px-10">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.22em] text-[var(--accent)]">
              Sari Arta
            </p>
            <p className="mt-1 font-semibold">Business Development</p>
          </div>
          <span className="rounded-full bg-[var(--success-soft)] px-3 py-1 text-xs font-semibold text-[var(--success)]">
            M4 AI workbench
          </span>
        </div>
      </header>
      <div className="mx-auto grid max-w-7xl gap-8 px-6 py-8 lg:grid-cols-[190px_1fr] lg:px-10">
        <nav aria-label="Main navigation" className="space-y-1">
          {navigation.map(([label, href]) => (
            <Link
              key={href}
              href={href}
              className="block rounded-xl px-4 py-3 text-sm font-semibold text-[var(--muted)] hover:bg-white hover:text-[var(--ink)]"
            >
              {label}
            </Link>
          ))}
          <Link
            href="/inquiry"
            className="mt-6 block rounded-xl border border-[var(--line)] px-4 py-3 text-sm font-semibold"
          >
            Public inquiry form
          </Link>
        </nav>
        <main>{children}</main>
      </div>
    </div>
  );
}
