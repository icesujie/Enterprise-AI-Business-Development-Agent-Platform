import Link from "next/link";

export function MetricCard({
  label,
  value,
  note,
  href,
  tone = "neutral",
}: {
  label: string;
  value: string;
  note: string;
  href: string;
  tone?: "neutral" | "info" | "warning";
}) {
  const accent =
    tone === "info"
      ? "bg-[var(--color-info)]"
      : tone === "warning"
        ? "bg-[var(--color-warning)]"
        : "bg-[var(--color-brand)]";
  return (
    <Link
      href={href}
      className="card group relative overflow-hidden p-5 transition hover:-translate-y-0.5 hover:shadow-xl"
    >
      <span className={`absolute left-0 top-0 h-full w-1 ${accent}`} />
      <p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--color-muted)]">
        {label}
      </p>
      <p className="mt-5 text-3xl font-semibold tabular-nums tracking-tight">
        {value}
      </p>
      <p className="mt-2 text-xs leading-5 text-[var(--color-muted)]">{note}</p>
    </Link>
  );
}
