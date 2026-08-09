import Link from "next/link";

export function IndustryCard({
  slug,
  index,
  title,
  description,
}: {
  slug: string;
  index: string;
  title: string;
  description: string;
}) {
  return (
    <Link
      href={`/industries#${slug}`}
      className="group border-t border-[var(--color-line)] py-6 transition hover:border-[var(--color-brand)]"
    >
      <span className="text-xs font-bold tracking-[0.16em] text-[var(--color-accent)]">
        {index}
      </span>
      <h3 className="mt-7 text-xl font-semibold tracking-tight group-hover:text-[var(--color-brand)]">
        {title}
      </h3>
      <p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">
        {description}
      </p>
      <span className="mt-6 inline-block text-sm font-bold text-[var(--color-brand)]">
        Explore industry →
      </span>
    </Link>
  );
}
