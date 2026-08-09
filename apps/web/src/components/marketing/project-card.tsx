import Link from "next/link";

export function ProjectCard({
  sector,
  title,
  scope,
}: {
  sector: string;
  title: string;
  scope: string;
}) {
  return (
    <article className="card overflow-hidden">
      <div className="relative h-48 bg-[var(--color-brand-strong)]">
        <div className="absolute inset-5 border border-white/15" />
        <div className="absolute bottom-5 left-5 h-16 w-2/3 border border-[var(--color-accent)] bg-[var(--color-accent)]/15" />
        <span className="absolute left-7 top-7 text-xs font-bold uppercase tracking-[0.16em] text-white/60">
          Project study
        </span>
      </div>
      <div className="p-6">
        <p className="eyebrow">{sector}</p>
        <h3 className="mt-3 text-xl font-semibold tracking-tight">{title}</h3>
        <p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">
          {scope}
        </p>
        <Link
          href="/projects"
          className="mt-6 inline-block text-sm font-bold text-[var(--color-brand)]"
        >
          View project approach →
        </Link>
      </div>
    </article>
  );
}
