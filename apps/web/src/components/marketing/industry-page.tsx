import { SectionContainer } from "@/components/layout/section-container";
import { PublicConsultationCta } from "@/components/marketing/public-consultation-cta";
import { ButtonLink } from "@/components/ui/button";
import type { IndustryPageContent } from "@/content/industry-pages";

export function IndustryPage({ content }: { content: IndustryPageContent }) {
  return (
    <>
      <header className="border-b border-[var(--color-line)] bg-[var(--color-surface-subtle)] py-16 sm:py-20 lg:py-24">
        <SectionContainer>
          <p className="eyebrow">{content.eyebrow}</p>
          <h1 className="section-title text-balance mt-5 max-w-4xl">
            {content.title}
          </h1>
          <p className="mt-6 max-w-3xl text-base leading-8 text-[var(--color-muted)] sm:text-lg">
            {content.description}
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <PublicConsultationCta label={content.consultationAgentLabel} />
            <ButtonLink href="/contact?industry=schools" variant="secondary">
              {content.consultationFormLabel}
            </ButtonLink>
          </div>
        </SectionContainer>
      </header>

      <section className="bg-white py-16 sm:py-20 lg:py-24">
        <SectionContainer>
          <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr] lg:gap-16">
            <div>
              <p className="eyebrow">{content.needsEyebrow}</p>
              <h2 className="section-title mt-4">{content.needsTitle}</h2>
              <p className="mt-5 text-sm leading-7 text-[var(--color-muted)]">
                {content.needsDescription}
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              {content.needs.map((need) => (
                <article className="card p-6" key={need.title}>
                  <h3 className="font-semibold">{need.title}</h3>
                  <p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">
                    {need.description}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </SectionContainer>
      </section>

      <section className="bg-[var(--color-canvas)] py-16 sm:py-20 lg:py-24">
        <SectionContainer>
          <p className="eyebrow">{content.projectEyebrow}</p>
          <div className="mt-4 grid gap-6 lg:grid-cols-[0.85fr_1.15fr] lg:items-end">
            <h2 className="section-title">{content.projectTitle}</h2>
            <p className="max-w-2xl text-sm leading-7 text-[var(--color-muted)] lg:justify-self-end">
              {content.projectDescription}
            </p>
          </div>
          <div className="mt-10 grid gap-5 md:grid-cols-2">
            {content.projectTypes.map((projectType, index) => (
              <article className="card p-7 sm:p-8" key={projectType.title}>
                <span className="text-xs font-bold text-[var(--color-accent)]">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3 className="mt-6 text-xl font-semibold">
                  {projectType.title}
                </h3>
                <p className="mt-3 text-sm leading-7 text-[var(--color-muted)]">
                  {projectType.description}
                </p>
              </article>
            ))}
          </div>
        </SectionContainer>
      </section>

      <section className="bg-[var(--color-brand)] py-16 text-white sm:py-20 lg:py-24">
        <SectionContainer>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#d4a48e]">
            {content.workflowEyebrow}
          </p>
          <div className="mt-4 grid gap-6 lg:grid-cols-[0.8fr_1.2fr] lg:items-end">
            <h2 className="section-title">{content.workflowTitle}</h2>
            <p className="max-w-2xl text-sm leading-7 text-white/65 lg:justify-self-end">
              {content.workflowDescription}
            </p>
          </div>
          <div className="mt-10 grid gap-px overflow-hidden rounded-2xl border border-white/15 bg-white/15 sm:grid-cols-2 lg:grid-cols-4">
            {content.workflowAreas.map((area) => (
              <article className="bg-[var(--color-brand)] p-6" key={area.title}>
                <h3 className="font-semibold">{area.title}</h3>
                <p className="mt-3 text-sm leading-6 text-white/60">
                  {area.description}
                </p>
              </article>
            ))}
          </div>
        </SectionContainer>
      </section>

      <section className="bg-white py-16 sm:py-20 lg:py-24">
        <SectionContainer>
          <article className="card grid gap-7 p-7 sm:p-10 lg:grid-cols-[1fr_auto] lg:items-end">
            <div>
              <p className="eyebrow">{content.solutionEyebrow}</p>
              <h2 className="section-title mt-4">{content.solutionTitle}</h2>
              <p className="mt-5 max-w-3xl text-sm leading-7 text-[var(--color-muted)]">
                {content.solutionDescription}
              </p>
            </div>
            <ButtonLink
              className="shrink-0"
              href="/solutions/school-canteen-kitchen"
              variant="secondary"
            >
              {content.solutionLinkLabel}
            </ButtonLink>
          </article>
        </SectionContainer>
      </section>

      <section className="bg-[var(--color-surface-subtle)] py-16 sm:py-20 lg:py-24">
        <SectionContainer>
          <div className="card flex flex-col gap-8 p-7 sm:p-10 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="eyebrow">{content.consultationEyebrow}</p>
              <h2 className="section-title mt-4 max-w-3xl">
                {content.consultationTitle}
              </h2>
              <p className="mt-5 max-w-2xl text-sm leading-7 text-[var(--color-muted)]">
                {content.consultationDescription}
              </p>
            </div>
            <PublicConsultationCta
              className="shrink-0"
              label={content.consultationAgentLabel}
            />
          </div>
        </SectionContainer>
      </section>
    </>
  );
}
