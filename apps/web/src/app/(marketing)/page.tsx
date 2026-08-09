import { SectionContainer } from "@/components/layout/section-container";
import { HeroSection } from "@/components/marketing/hero-section";
import { IndustryCard } from "@/components/marketing/industry-card";
import {
  ConsultationBand,
  ContentBand,
} from "@/components/marketing/inner-page";
import { ProjectCard } from "@/components/marketing/project-card";

const industries = [
  [
    "01",
    "School kitchens",
    "Safe, maintainable food-service flow for concentrated meal periods.",
  ],
  [
    "02",
    "Hospital kitchens",
    "Reliable production and distribution planned around separation and hygiene.",
  ],
  [
    "03",
    "Factory cafeterias",
    "High-throughput preparation and service for demanding shift patterns.",
  ],
  [
    "04",
    "Central kitchens",
    "Scalable production flow from receiving through dispatch.",
  ],
] as const;

export default function HomePage() {
  return (
    <>
      <HeroSection />
      <ContentBand>
        <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr]">
          <div>
            <p className="eyebrow">Designed for operations</p>
            <h2 className="section-title mt-4">
              A kitchen is a system, not a catalogue.
            </h2>
          </div>
          <p className="max-w-2xl text-lg leading-8 text-[var(--color-muted)]">
            Capacity, people, workflow, utilities, equipment, hygiene, and
            service must work together. Sari Arta’s project approach starts with
            the operation, then coordinates the right technical delivery.
          </p>
        </div>
        <div className="mt-14 grid gap-7 sm:grid-cols-2 lg:grid-cols-4">
          {industries.map(([index, title, description]) => (
            <IndustryCard
              key={index}
              index={index}
              title={title}
              description={description}
            />
          ))}
        </div>
      </ContentBand>

      <section className="bg-white py-16 sm:py-20 lg:py-24">
        <SectionContainer>
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="eyebrow">Coordinated delivery</p>
              <h2 className="section-title mt-4 max-w-3xl">
                From operating brief to a commissioned kitchen.
              </h2>
            </div>
            <p className="max-w-md text-sm leading-7 text-[var(--color-muted)]">
              A single project rhythm connects engineering decisions,
              manufacturing controls, logistics, and local site work.
            </p>
          </div>
          <ol className="mt-14 grid gap-px overflow-hidden rounded-2xl border border-[var(--color-line)] bg-[var(--color-line)] md:grid-cols-3 lg:grid-cols-6">
            {[
              "Discover",
              "Plan flow",
              "Engineer",
              "Coordinate",
              "Install",
              "Commission",
            ].map((step, index) => (
              <li key={step} className="bg-[var(--color-surface)] p-5">
                <span className="text-xs font-bold text-[var(--color-accent)]">
                  0{index + 1}
                </span>
                <p className="mt-8 text-sm font-semibold">{step}</p>
              </li>
            ))}
          </ol>
        </SectionContainer>
      </section>

      <ContentBand>
        <div className="flex items-end justify-between gap-6">
          <div>
            <p className="eyebrow">Project evidence</p>
            <h2 className="section-title mt-4">
              How complete delivery is structured.
            </h2>
          </div>
          <p className="hidden max-w-sm text-sm text-[var(--color-muted)] lg:block">
            Placeholder studies demonstrate the case-study layout without
            presenting invented customer work.
          </p>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-2">
          <ProjectCard
            sector="Education"
            title="School food-service planning approach"
            scope="Example layout showing how project context, challenge, scope, and delivery evidence will be presented."
          />
          <ProjectCard
            sector="Industrial dining"
            title="High-volume cafeteria delivery approach"
            scope="A transparent preview of the case-study format, pending approved Sari Arta project evidence."
          />
        </div>
      </ContentBand>
      <ConsultationBand />
    </>
  );
}
