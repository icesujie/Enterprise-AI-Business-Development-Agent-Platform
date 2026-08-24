import { SectionContainer } from "@/components/layout/section-container";
import { PublicConsultationCta } from "@/components/marketing/public-consultation-cta";
import { ButtonLink } from "@/components/ui/button";
import {
  guideInterfaceCopy,
  type GuidePageContent,
  type GuideRelatedLink,
} from "@/content/guides";
import type { Locale } from "@/i18n/config";

export function GuidePage({
  content,
  locale,
}: {
  content: GuidePageContent;
  locale: Locale;
}) {
  const copy = guideInterfaceCopy[locale];

  return (
    <>
      <header className="border-b border-[var(--color-line)] bg-[var(--color-surface-subtle)] py-16 sm:py-20 lg:py-24">
        <SectionContainer>
          <p className="eyebrow">{content.eyebrow}</p>
          <h1 className="section-title text-balance mt-5 max-w-4xl">
            {content.title}
          </h1>
          <p className="mt-6 max-w-3xl text-base leading-8 text-[var(--color-muted)] sm:text-lg">
            {content.summary}
          </p>
          <PublicConsultationCta
            className="mt-8"
            label={content.consultationLabel ?? copy.consultationLabel}
          />
        </SectionContainer>
      </header>

      <article>
        <section className="bg-white py-16 sm:py-20 lg:py-24">
          <SectionContainer>
            <div className="grid gap-10 lg:grid-cols-[0.65fr_1.35fr] lg:gap-16">
              <p className="eyebrow">{copy.introduction}</p>
              <div className="space-y-5 text-base leading-8 text-[var(--color-muted)]">
                {content.introduction.map((paragraph) => (
                  <p key={paragraph}>{paragraph}</p>
                ))}
              </div>
            </div>
          </SectionContainer>
        </section>

        <section className="bg-[var(--color-canvas)] py-16 sm:py-20 lg:py-24">
          <SectionContainer>
            <div className="space-y-6">
              {content.sections.map((section, index) => (
                <section className="card p-7 sm:p-10" key={section.heading}>
                  <span className="text-xs font-bold text-[var(--color-accent)]">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <h2 className="section-title mt-5">{section.heading}</h2>
                  <div className="mt-5 max-w-3xl space-y-4 text-sm leading-7 text-[var(--color-muted)]">
                    {section.paragraphs.map((paragraph) => (
                      <p key={paragraph}>{paragraph}</p>
                    ))}
                  </div>
                  {section.points?.length ? (
                    <ul className="mt-7 grid gap-3 sm:grid-cols-2">
                      {section.points.map((point) => (
                        <li
                          className="rounded-xl border border-[var(--color-line)] bg-[var(--color-surface-subtle)] p-4 text-sm leading-6"
                          key={point}
                        >
                          {point}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </section>
              ))}
            </div>
          </SectionContainer>
        </section>
      </article>

      {content.faqItems.length > 0 ? (
        <section className="bg-white py-16 sm:py-20 lg:py-24">
          <SectionContainer>
            <h2 className="section-title max-w-3xl">{copy.faq}</h2>
            <div className="mt-10 grid gap-4">
              {content.faqItems.map((item) => (
                <article className="card p-6 sm:p-8" key={item.question}>
                  <h3 className="text-lg font-semibold">{item.question}</h3>
                  <p className="mt-3 max-w-4xl text-sm leading-7 text-[var(--color-muted)]">
                    {item.answer}
                  </p>
                </article>
              ))}
            </div>
          </SectionContainer>
        </section>
      ) : null}

      <section className="bg-[var(--color-brand)] py-16 text-white sm:py-20 lg:py-24">
        <SectionContainer>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#d4a48e]">
            {copy.related}
          </p>
          <div className="mt-8 grid gap-8 lg:grid-cols-3">
            <RelatedLinks
              links={content.relatedSolutions}
              title={copy.relatedSolutions}
            />
            <RelatedLinks
              links={content.relatedIndustries}
              title={copy.relatedIndustries}
            />
            {content.relatedProjects.length > 0 ? (
              <RelatedLinks
                links={content.relatedProjects}
                title={copy.relatedProjects}
              />
            ) : null}
          </div>
        </SectionContainer>
      </section>

      <section className="bg-[var(--color-surface-subtle)] py-16 sm:py-20 lg:py-24">
        <SectionContainer>
          <div className="card flex flex-col gap-8 p-7 sm:p-10 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="eyebrow">{copy.consultationEyebrow}</p>
              <h2 className="section-title mt-4 max-w-3xl">
                {copy.consultationTitle}
              </h2>
              <p className="mt-5 max-w-2xl text-sm leading-7 text-[var(--color-muted)]">
                {content.consultationDescription ??
                  copy.consultationDescription}
              </p>
            </div>
            <PublicConsultationCta
              className="shrink-0"
              label={content.consultationLabel ?? copy.consultationLabel}
            />
          </div>
        </SectionContainer>
      </section>
    </>
  );
}

function RelatedLinks({
  links,
  title,
}: {
  links: readonly GuideRelatedLink[];
  title: string;
}) {
  return (
    <div>
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="mt-4 flex flex-col items-start gap-3">
        {links.map((link) => (
          <ButtonLink href={link.href} key={link.href} variant="secondary">
            {link.label}
          </ButtonLink>
        ))}
      </div>
    </div>
  );
}
