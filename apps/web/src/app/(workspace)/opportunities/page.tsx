import Link from "next/link";

import { apiFetch, type OpportunityList } from "@/lib/api";

const stages = [
  "discovery",
  "requirements_confirmed",
  "proposal",
  "negotiation",
  "won",
  "lost",
] as const;

export default async function OpportunitiesPage() {
  const data = await apiFetch<OpportunityList>("/api/v1/opportunities");
  const openValue = data.items
    .filter((item) => item.status === "open")
    .reduce((total, item) => total + Number(item.estimated_value), 0);

  return (
    <div>
      <header className="flex flex-wrap items-end justify-between gap-6">
        <div>
          <p className="eyebrow">Commercial pipeline</p>
          <h1 className="page-title">Opportunities</h1>
          <p className="mt-2 text-[var(--muted)]">
            Move qualified kitchen projects through controlled sales stages.
          </p>
        </div>
        <div className="rounded-2xl bg-white px-5 py-3 text-right shadow-sm">
          <p className="text-xs font-semibold uppercase text-[var(--muted)]">
            Open pipeline
          </p>
          <p className="mt-1 font-semibold">IDR {formatAmount(openValue)}</p>
        </div>
      </header>

      <div className="mt-7 grid gap-4 xl:grid-cols-3">
        {stages.map((stage) => {
          const items = data.items.filter((item) => item.stage === stage);
          return (
            <section key={stage} className="card h-fit overflow-hidden">
              <header className="flex items-center justify-between border-b border-[var(--line)] px-5 py-4">
                <h2 className="font-semibold capitalize">
                  {stage.replaceAll("_", " ")}
                </h2>
                <span className="status-chip">{items.length}</span>
              </header>
              <div className="divide-y divide-[var(--line)]">
                {items.length ? (
                  items.map((item) => (
                    <Link
                      key={item.id}
                      href={`/opportunities/${item.id}`}
                      className="block p-5 transition hover:bg-[#fafbf8]"
                    >
                      <p className="font-semibold">{item.name}</p>
                      <p className="mt-2 text-sm text-[var(--muted)]">
                        {item.currency}{" "}
                        {formatAmount(Number(item.estimated_value))}
                      </p>
                      <div className="mt-3 flex items-center justify-between text-xs text-[var(--muted)]">
                        <span>{item.probability}% probability</span>
                        <span>
                          {item.expected_close_date
                            ? formatDate(item.expected_close_date)
                            : "No close date"}
                        </span>
                      </div>
                    </Link>
                  ))
                ) : (
                  <p className="p-5 text-sm text-[var(--muted)]">No records</p>
                )}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}

function formatAmount(value: number) {
  return new Intl.NumberFormat("en", { maximumFractionDigits: 0 }).format(
    value,
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(
    new Date(`${value}T00:00:00Z`),
  );
}
