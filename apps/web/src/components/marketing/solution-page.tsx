import { SectionContainer } from "@/components/layout/section-container";
import { PublicConsultationCta } from "@/components/marketing/public-consultation-cta";
import { ButtonLink } from "@/components/ui/button";
import type { SolutionPageContent } from "@/content/solution-pages";

export function SolutionPage({ content }: { content: SolutionPageContent }) {
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
            <ButtonLink href="/contact" variant="secondary">
              {content.consultationFormLabel}
            </ButtonLink>
          </div>
        </SectionContainer>
      </header>

      <section className="bg-white py-16 sm:py-20 lg:py-24">
        <SectionContainer>
          <div className="grid gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:gap-16">
            <div>
              <p className="eyebrow">{content.overviewEyebrow}</p>
              <h2 className="section-title mt-4">{content.overviewTitle}</h2>
              <p className="mt-5 text-sm leading-7 text-[var(--color-muted)]">
                {content.overviewDescription}
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              {content.priorities.map((priority) => (
                <article className="card p-6" key={priority.title}>
                  <h3 className="font-semibold">{priority.title}</h3>
                  <p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">
                    {priority.description}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </SectionContainer>
      </section>

      <section className="bg-[var(--color-canvas)] py-16 sm:py-20 lg:py-24">
        <SectionContainer>
          <p className="eyebrow">{content.scopeEyebrow}</p>
          <div className="mt-4 grid gap-6 lg:grid-cols-[0.85fr_1.15fr] lg:items-end">
            <h2 className="section-title">{content.scopeTitle}</h2>
            <p className="max-w-2xl text-sm leading-7 text-[var(--color-muted)] lg:justify-self-end">
              {content.scopeDescription}
            </p>
          </div>
          <ol className="mt-10 grid gap-5 md:grid-cols-2">
            {content.scopeItems.map((item) => (
              <li className="card p-7 sm:p-8" key={item.number}>
                <span className="text-xs font-bold text-[var(--color-accent)]">
                  {item.number}
                </span>
                <h3 className="mt-6 text-xl font-semibold">{item.title}</h3>
                <p className="mt-3 text-sm leading-7 text-[var(--color-muted)]">
                  {item.description}
                </p>
              </li>
            ))}
          </ol>
        </SectionContainer>
      </section>

      <section className="bg-white py-16 sm:py-20 lg:py-24">
        <SectionContainer>
          <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr] lg:gap-16">
            <div>
              <p className="eyebrow">{content.inputsEyebrow}</p>
              <h2 className="section-title mt-4">{content.inputsTitle}</h2>
              <p className="mt-5 text-sm leading-7 text-[var(--color-muted)]">
                {content.inputsDescription}
              </p>
            </div>
            <ul className="grid gap-px overflow-hidden rounded-2xl border border-[var(--color-line)] bg-[var(--color-line)] sm:grid-cols-2">
              {content.inputs.map((input, index) => (
                <li
                  className="flex gap-4 bg-white p-6 text-sm leading-6"
                  key={input}
                >
                  <span className="font-bold text-[var(--color-accent)]">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <span>{input}</span>
                </li>
              ))}
            </ul>
          </div>
        </SectionContainer>
      </section>

      <section className="bg-[var(--color-brand)] py-16 text-white sm:py-20 lg:py-24">
        <SectionContainer>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#d4a48e]">
            {content.deliveryEyebrow}
          </p>
          <div className="mt-4 grid gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-end">
            <h2 className="section-title">{content.deliveryTitle}</h2>
            <p className="max-w-2xl leading-7 text-white/65 lg:justify-self-end">
              {content.deliveryDescription}
            </p>
          </div>
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
