const services = [
  {
    name: "Frontend",
    detail: "Next.js application shell",
    state: "Operational",
  },
  {
    name: "Business API",
    detail: "FastAPI health contract",
    state: "Ready",
  },
  {
    name: "Data services",
    detail: "PostgreSQL and Redis",
    state: "Configured",
  },
] as const;

const nextMilestones = [
  "Lead and customer records",
  "Tasks and opportunity conversion",
  "AI-assisted lead qualification",
] as const;

export default function Home() {
  return (
    <main className="min-h-screen bg-[var(--canvas)] text-[var(--ink)]">
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-6 py-8 sm:px-10 lg:px-14">
        <header className="flex items-center justify-between border-b border-[var(--line)] pb-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[var(--muted)]">
              Sari Arta
            </p>
            <p className="mt-1 text-sm font-medium">AI Business Development</p>
          </div>
          <span className="rounded-full border border-[var(--accent)]/25 bg-[var(--accent-soft)] px-3 py-1 text-xs font-semibold text-[var(--accent)]">
            M2 Data foundation
          </span>
        </header>

        <section className="grid flex-1 gap-12 py-16 lg:grid-cols-[1.25fr_0.75fr] lg:items-center lg:py-20">
          <div>
            <p className="mb-5 text-sm font-semibold uppercase tracking-[0.2em] text-[var(--accent)]">
              Enterprise sales workspace
            </p>
            <h1 className="max-w-3xl text-5xl font-semibold leading-[1.05] tracking-[-0.045em] sm:text-6xl">
              Business development, built on a reliable foundation.
            </h1>
            <p className="mt-7 max-w-2xl text-lg leading-8 text-[var(--muted)]">
              The secure application foundation now includes workspace identity,
              role enforcement, and the core CRM data model needed for lead work.
            </p>

            <dl className="mt-10 grid gap-4 sm:grid-cols-3">
              {services.map((service) => (
                <div
                  key={service.name}
                  className="rounded-2xl border border-[var(--line)] bg-white p-5 shadow-[0_14px_40px_rgba(24,34,28,0.05)]"
                >
                  <div className="mb-5 flex items-center gap-2 text-xs font-semibold text-[var(--success)]">
                    <span className="size-2 rounded-full bg-current" aria-hidden="true" />
                    {service.state}
                  </div>
                  <dt className="font-semibold">{service.name}</dt>
                  <dd className="mt-1 text-sm leading-6 text-[var(--muted)]">
                    {service.detail}
                  </dd>
                </div>
              ))}
            </dl>
          </div>

          <aside className="rounded-3xl bg-[var(--panel)] p-7 text-white shadow-[0_30px_80px_rgba(20,42,31,0.18)] sm:p-9">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/55">
              Delivery sequence
            </p>
            <h2 className="mt-4 text-2xl font-semibold tracking-[-0.02em]">
              What comes after M2
            </h2>
            <ol className="mt-8 space-y-5">
              {nextMilestones.map((milestone, index) => (
                <li key={milestone} className="flex items-start gap-4">
                  <span className="flex size-8 shrink-0 items-center justify-center rounded-full border border-white/20 text-sm text-white/70">
                    {index + 1}
                  </span>
                  <span className="pt-1 text-sm leading-6 text-white/80">{milestone}</span>
                </li>
              ))}
            </ol>
            <p className="mt-9 border-t border-white/10 pt-6 text-sm leading-6 text-white/55">
              No customer data, external messages, or production AI calls are active.
            </p>
          </aside>
        </section>

        <footer className="flex flex-col gap-2 border-t border-[var(--line)] pt-5 text-xs text-[var(--muted)] sm:flex-row sm:items-center sm:justify-between">
          <span>Phase 1 · Enterprise AI Business Development Agent Platform</span>
          <span>Reference business: commercial kitchen engineering</span>
        </footer>
      </div>
    </main>
  );
}
