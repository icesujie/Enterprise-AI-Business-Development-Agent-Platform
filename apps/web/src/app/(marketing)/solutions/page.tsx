import {
  ConsultationBand,
  ContentBand,
  InnerPageHero,
} from "@/components/marketing/inner-page";

const capabilities = [
  [
    "01",
    "Planning and workflow",
    "Translate capacity, menu, people, and site constraints into a practical operating flow.",
  ],
  [
    "02",
    "Equipment engineering",
    "Define a coordinated equipment scope around the operation rather than isolated products.",
  ],
  [
    "03",
    "Manufacturing coordination",
    "Connect approved manufacturing resources with technical review and quality gates.",
  ],
  [
    "04",
    "Installation and commissioning",
    "Coordinate site readiness, local installation, testing, training, and handover.",
  ],
] as const;

export default function SolutionsPage() {
  return (
    <>
      <InnerPageHero
        eyebrow="Solutions"
        title="One project path from requirement to operation."
        description="The foundation preview organizes Sari Arta around project responsibilities and deliverables, not an equipment catalogue."
      />
      <ContentBand tone="white">
        <div className="grid gap-px overflow-hidden rounded-2xl border border-[var(--color-line)] bg-[var(--color-line)] md:grid-cols-2">
          {capabilities.map(([index, title, description]) => (
            <article key={index} className="bg-white p-7 sm:p-9">
              <span className="text-xs font-bold text-[var(--color-accent)]">
                {index}
              </span>
              <h2 className="mt-8 text-2xl font-semibold tracking-tight">
                {title}
              </h2>
              <p className="mt-4 max-w-xl text-sm leading-7 text-[var(--color-muted)]">
                {description}
              </p>
              <span className="mt-8 inline-block text-sm font-bold text-[var(--color-brand)]">
                Detail page planned →
              </span>
            </article>
          ))}
        </div>
      </ContentBand>
      <ConsultationBand title="Which delivery responsibilities should Sari Arta support?" />
    </>
  );
}
