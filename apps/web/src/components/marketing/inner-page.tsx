import type { ReactNode } from "react";

import { SectionContainer } from "@/components/layout/section-container";
import { ButtonLink } from "@/components/ui/button";

export function InnerPageHero({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <section className="border-b border-[var(--color-line)] bg-[var(--color-surface-subtle)] py-16 sm:py-20">
      <SectionContainer>
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="section-title text-balance mt-5 max-w-4xl">{title}</h1>
        <p className="mt-6 max-w-2xl text-base leading-8 text-[var(--color-muted)] sm:text-lg">
          {description}
        </p>
      </SectionContainer>
    </section>
  );
}

export function ContentBand({
  children,
  tone = "light",
}: {
  children: ReactNode;
  tone?: "light" | "white" | "dark";
}) {
  const toneClass =
    tone === "dark"
      ? "bg-[var(--color-brand)] text-white"
      : tone === "white"
        ? "bg-white"
        : "bg-[var(--color-canvas)]";
  return (
    <section className={`${toneClass} py-16 sm:py-20 lg:py-24`}>
      <SectionContainer>{children}</SectionContainer>
    </section>
  );
}

export function ConsultationBand({
  title = "Planning a commercial kitchen project?",
}: {
  title?: string;
}) {
  return (
    <ContentBand tone="dark">
      <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#d4a48e]">
            Start with what you know
          </p>
          <h2 className="section-title mt-4 max-w-3xl">{title}</h2>
          <p className="mt-5 max-w-2xl leading-7 text-white/65">
            Incomplete drawings or early requirements are welcome. A human
            specialist reviews every inquiry before any commitment is made.
          </p>
        </div>
        <ButtonLink href="/contact" className="button-inverse shrink-0">
          Request consultation
        </ButtonLink>
      </div>
    </ContentBand>
  );
}
