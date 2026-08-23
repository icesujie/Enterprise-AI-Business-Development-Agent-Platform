import Image from "next/image";

import { SectionContainer } from "@/components/layout/section-container";
import { PublicConsultationCta } from "@/components/marketing/public-consultation-cta";
import { ButtonLink } from "@/components/ui/button";
import {
  caseStudyInterfaceCopy,
  type CaseStudyPageContent,
} from "@/content/case-studies";
import type { Locale } from "@/i18n/config";

export function CaseStudyPage({
  content,
  locale,
}: {
  content: CaseStudyPageContent;
  locale: Locale;
}) {
  const copy = caseStudyInterfaceCopy[locale];

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
          <dl className="mt-8 grid max-w-4xl gap-px overflow-hidden rounded-2xl border border-[var(--color-line)] bg-[var(--color-line)] sm:grid-cols-3">
            {[
              [
                locale === "zh-CN" ? "项目类型" : "Project type",
                content.projectType,
              ],
              [locale === "zh-CN" ? "地点" : "Location", content.location],
              [locale === "zh-CN" ? "行业" : "Industry", content.industry],
            ].map(([label, value]) => (
              <div className="bg-white p-5" key={label}>
                <dt className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--color-muted)]">
                  {label}
                </dt>
                <dd className="mt-2 text-sm font-semibold">{value}</dd>
              </div>
            ))}
          </dl>
          <PublicConsultationCta
            className="mt-8"
            label={copy.consultationLabel}
          />
        </SectionContainer>
      </header>

      <section className="bg-white py-16 sm:py-20 lg:py-24">
        <SectionContainer>
          <div className="grid gap-12 lg:grid-cols-[0.75fr_1.25fr] lg:gap-16">
            <div>
              <p className="eyebrow">{copy.overview}</p>
              <h2 className="section-title mt-4">{copy.requirements}</h2>
            </div>
            <ul className="grid gap-4 sm:grid-cols-2">
              {content.projectRequirements.map((requirement) => (
                <li className="card p-6 text-sm leading-7" key={requirement}>
                  {requirement}
                </li>
              ))}
            </ul>
          </div>
        </SectionContainer>
      </section>

      <CaseStudySection
        items={content.scopeOfWork}
        title={copy.scope}
        tone="canvas"
      />
      <CaseStudySection
        items={content.kitchenAreas}
        title={copy.kitchenAreas}
      />
      <CaseStudySection
        items={content.deliveryApproach}
        title={copy.deliveryApproach}
        tone="dark"
      />

      <section className="bg-[var(--color-canvas)] py-16 sm:py-20 lg:py-24">
        <SectionContainer>
          <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:gap-16">
            <h2 className="section-title">{copy.approvedFacts}</h2>
            <dl className="grid gap-px overflow-hidden rounded-2xl border border-[var(--color-line)] bg-[var(--color-line)] sm:grid-cols-2">
              {content.approvedProjectFacts.map((fact) => (
                <div className="bg-white p-6" key={fact.label}>
                  <dt className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--color-muted)]">
                    {fact.label}
                  </dt>
                  <dd className="mt-3 text-sm leading-7">{fact.value}</dd>
                </div>
              ))}
            </dl>
          </div>
        </SectionContainer>
      </section>

      {content.images.length > 0 ? (
        <section className="bg-white py-16 sm:py-20 lg:py-24">
          <SectionContainer>
            <h2 className="section-title">{copy.gallery}</h2>
            <div className="mt-10 grid gap-6 lg:grid-cols-2">
              {content.images.map((image) => (
                <figure
                  className="overflow-hidden rounded-2xl border border-[var(--color-line)]"
                  key={image.src}
                >
                  <Image
                    alt={image.alt}
                    className="h-auto w-full object-cover"
                    height={image.height}
                    sizes="(min-width: 1024px) 50vw, 100vw"
                    src={image.src}
                    width={image.width}
                  />
                  {image.caption ? (
                    <figcaption className="px-5 py-4 text-sm leading-6 text-[var(--color-muted)]">
                      {image.caption}
                    </figcaption>
                  ) : null}
                </figure>
              ))}
            </div>
          </SectionContainer>
        </section>
      ) : null}

      <section className="bg-white py-16 sm:py-20 lg:py-24">
        <SectionContainer>
          <article className="card grid gap-7 p-7 sm:p-10 lg:grid-cols-[1fr_auto] lg:items-end">
            <div>
              <p className="eyebrow">{copy.related}</p>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-[var(--color-muted)]">
                {copy.relatedDescription}
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <ButtonLink
                href={content.relatedSolution.href}
                variant="secondary"
              >
                {content.relatedSolution.label}
              </ButtonLink>
              <ButtonLink
                href={content.relatedIndustry.href}
                variant="secondary"
              >
                {content.relatedIndustry.label}
              </ButtonLink>
            </div>
          </article>
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
                {copy.consultationDescription}
              </p>
            </div>
            <PublicConsultationCta
              className="shrink-0"
              label={copy.consultationLabel}
            />
          </div>
        </SectionContainer>
      </section>
    </>
  );
}

function CaseStudySection({
  items,
  title,
  tone = "white",
}: {
  items: readonly { title: string; description: string }[];
  title: string;
  tone?: "white" | "canvas" | "dark";
}) {
  const dark = tone === "dark";
  const background = dark
    ? "bg-[var(--color-brand)] text-white"
    : tone === "canvas"
      ? "bg-[var(--color-canvas)]"
      : "bg-white";

  return (
    <section className={`${background} py-16 sm:py-20 lg:py-24`}>
      <SectionContainer>
        <h2 className="section-title max-w-3xl">{title}</h2>
        <div
          className={`mt-10 grid gap-px overflow-hidden rounded-2xl border ${dark ? "border-white/15 bg-white/15" : "border-[var(--color-line)] bg-[var(--color-line)]"} md:grid-cols-2`}
        >
          {items.map((item, index) => (
            <article
              className={dark ? "bg-[var(--color-brand)] p-7" : "bg-white p-7"}
              key={item.title}
            >
              <span
                className={
                  dark
                    ? "text-xs font-bold text-[#d4a48e]"
                    : "text-xs font-bold text-[var(--color-accent)]"
                }
              >
                {String(index + 1).padStart(2, "0")}
              </span>
              <h3 className="mt-5 text-lg font-semibold">{item.title}</h3>
              <p
                className={`mt-3 text-sm leading-7 ${dark ? "text-white/65" : "text-[var(--color-muted)]"}`}
              >
                {item.description}
              </p>
            </article>
          ))}
        </div>
      </SectionContainer>
    </section>
  );
}
