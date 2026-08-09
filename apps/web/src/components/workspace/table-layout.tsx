import type { ReactNode } from "react";

export function TableLayout({
  title,
  columns,
  children,
}: {
  title: string;
  columns: string[];
  children?: ReactNode;
}) {
  return (
    <section className="card overflow-hidden">
      <header className="flex items-center justify-between border-b border-[var(--color-line)] px-5 py-4">
        <h2 className="font-semibold">{title}</h2>
        <span className="text-xs font-semibold text-[var(--color-muted)]">
          Business records
        </span>
      </header>
      <div className="hidden grid-cols-[1.6fr_1fr_1fr_auto] gap-4 border-b border-[var(--color-line)] bg-[var(--color-surface-subtle)] px-5 py-3 text-[0.68rem] font-bold uppercase tracking-[0.12em] text-[var(--color-muted)] md:grid">
        {columns.map((column) => (
          <span key={column}>{column}</span>
        ))}
      </div>
      {children}
    </section>
  );
}
