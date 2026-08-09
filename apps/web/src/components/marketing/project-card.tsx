import Link from "next/link";

export function ProjectCard({
  sector,
  location,
  title,
  challenge,
  scope,
}: {
  sector: string;
  location: string;
  title: string;
  challenge: string;
  scope: string;
}) {
  return (
    <article className="card overflow-hidden">
      <div className="relative h-48 bg-[var(--color-brand-strong)]">
        <div className="absolute inset-5 border border-white/15" />
        <div className="absolute bottom-5 left-5 h-16 w-2/3 border border-[var(--color-accent)] bg-[var(--color-accent)]/15" />
        <span className="absolute left-7 top-7 rounded-full border border-white/20 bg-white/8 px-3 py-1.5 text-[0.65rem] font-bold uppercase tracking-[0.14em] text-white/75">
          Sample project scenario
        </span>
      </div>
      <div className="p-6">
        <p className="eyebrow">{sector}</p>
        <h3 className="mt-3 text-xl font-semibold tracking-tight">{title}</h3>
        <p className="mt-2 text-xs font-semibold text-[var(--color-muted)]">
          {location}
        </p>
        <p className="mt-5 text-sm leading-6 text-[var(--color-muted)]">
          <strong className="text-[var(--color-ink)]">Challenge:</strong>{" "}
          {challenge}
        </p>
        <p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">
          <strong className="text-[var(--color-ink)]">
            Illustrative scope:
          </strong>{" "}
          {scope}
        </p>
        <Link
          href="/projects"
          className="mt-6 inline-block text-sm font-bold text-[var(--color-brand)]"
        >
          Explore sample scenario →
        </Link>
      </div>
    </article>
  );
}
