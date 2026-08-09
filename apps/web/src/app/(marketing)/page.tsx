import type { Metadata } from "next";

import { SectionContainer } from "@/components/layout/section-container";
import { HeroSection } from "@/components/marketing/hero-section";
import { IndustryCard } from "@/components/marketing/industry-card";
import {
  ConsultationBand,
  ContentBand,
} from "@/components/marketing/inner-page";
import { ProjectCard } from "@/components/marketing/project-card";
import { ButtonLink } from "@/components/ui/button";
import {
  capabilities,
  deliveryStages,
  industries,
  sampleProjects,
} from "@/content/public-site";

export const metadata: Metadata = {
  title: "Commercial Kitchen Engineering Indonesia",
  description:
    "Sari Arta coordinates commercial kitchen design, China-based manufacturing capability, logistics, local installation, and commissioning for projects in Indonesia.",
  keywords: [
    "commercial kitchen Indonesia",
    "industrial kitchen engineering",
    "commercial kitchen design",
    "central kitchen solution",
  ],
};

export default function HomePage() {
  return (
    <>
      <HeroSection />

      <ContentBand>
        <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr]">
          <div>
            <p className="eyebrow">Designed for operations</p>
            <h2 className="section-title mt-4">
              A kitchen is an operating system, not a list of equipment.
            </h2>
          </div>
          <div>
            <p className="max-w-2xl text-lg leading-8 text-[var(--color-muted)]">
              Menu, meal volume, staff movement, hygiene zones, utilities,
              equipment, site access, and service must work together. Sari Arta
              starts with the way food must move through the facility, then
              coordinates the technical delivery around it.
            </p>
            <ButtonLink href="/solutions" variant="tertiary" className="mt-5">
              Explore our engineering approach →
            </ButtonLink>
          </div>
        </div>
        <div className="mt-14 grid gap-7 sm:grid-cols-2 lg:grid-cols-4">
          {industries.map((industry) => (
            <IndustryCard
              key={industry.slug}
              slug={industry.slug}
              index={industry.number}
              title={industry.title}
              description={industry.description}
            />
          ))}
        </div>
      </ContentBand>

      <section className="bg-white py-16 sm:py-20 lg:py-24">
        <SectionContainer>
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="eyebrow">Engineering capability</p>
              <h2 className="section-title mt-4 max-w-3xl">
                One coordinated path from kitchen brief to handover.
              </h2>
            </div>
            <p className="max-w-md text-sm leading-7 text-[var(--color-muted)]">
              The exact scope is confirmed project by project. These five
              capabilities create a clear framework for ownership and
              coordination.
            </p>
          </div>
          <div className="mt-14 grid gap-px overflow-hidden rounded-2xl border border-[var(--color-line)] bg-[var(--color-line)] md:grid-cols-2 xl:grid-cols-5">
            {capabilities.map((capability) => (
              <article
                key={capability.number}
                className="bg-[var(--color-surface)] p-6"
              >
                <span className="text-xs font-bold text-[var(--color-accent)]">
                  {capability.number}
                </span>
                <h3 className="mt-8 text-lg font-semibold tracking-tight">
                  {capability.shortTitle}
                </h3>
                <p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">
                  {capability.description}
                </p>
              </article>
            ))}
          </div>
        </SectionContainer>
      </section>

      <ContentBand tone="dark">
        <div className="grid gap-12 lg:grid-cols-[0.82fr_1.18fr] lg:items-start">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#d4a48e]">
              China–Indonesia delivery model
            </p>
            <h2 className="section-title mt-4 max-w-2xl">
              Manufacturing reach with accountable local project delivery.
            </h2>
            <p className="mt-6 max-w-xl leading-7 text-white/65">
              Sari Arta coordinates manufacturing capability in China with
              project engineering, site readiness, installation, and
              commissioning in Indonesia. Responsibilities and quality gates are
              agreed before equipment is released.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <DeliveryCard
              label="China coordination"
              title="Equipment and manufacturing"
              items={[
                "Technical scope alignment",
                "Manufacturing information",
                "Quality and release checkpoints",
                "Shipping documentation inputs",
              ]}
            />
            <DeliveryCard
              label="Indonesia delivery"
              title="Site and operational handover"
              items={[
                "Site-readiness coordination",
                "Delivery and installation sequence",
                "Testing and commissioning",
                "Operator handover support",
              ]}
            />
          </div>
        </div>
        <ol className="mt-14 grid gap-px overflow-hidden rounded-2xl border border-white/15 bg-white/15 md:grid-cols-5">
          {deliveryStages.map((stage) => (
            <li key={stage.number} className="bg-[var(--color-brand)] p-5">
              <span className="text-xs font-bold text-[#d4a48e]">
                {stage.number}
              </span>
              <h3 className="mt-6 text-sm font-semibold">{stage.title}</h3>
              <p className="mt-3 text-xs leading-5 text-white/55">
                {stage.description}
              </p>
            </li>
          ))}
        </ol>
      </ContentBand>

      <ContentBand>
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="eyebrow">Project showcase</p>
            <h2 className="section-title mt-4">
              See how project decisions connect.
            </h2>
          </div>
          <p className="max-w-md text-sm leading-7 text-[var(--color-muted)]">
            The scenarios below are clearly marked demonstration content. They
            show how Sari Arta will present project context without claiming a
            completed customer project.
          </p>
        </div>
        <div className="mt-12 grid gap-6 lg:grid-cols-3">
          {sampleProjects.map((project) => (
            <ProjectCard key={project.title} {...project} />
          ))}
        </div>
      </ContentBand>

      <section className="border-y border-[var(--color-line)] bg-white py-16 sm:py-20">
        <SectionContainer className="grid gap-10 lg:grid-cols-[0.75fr_1.25fr]">
          <div>
            <p className="eyebrow">Start with what you know</p>
            <h2 className="section-title mt-4">
              A useful first brief is simple.
            </h2>
          </div>
          <ul className="grid gap-3 sm:grid-cols-2">
            {[
              "Facility type and project location",
              "Approximate kitchen size or meal volume",
              "Menu and operating schedule",
              "Target opening or required timeline",
              "Available floor plans and utility information",
              "Known equipment or service scope",
            ].map((item) => (
              <li
                key={item}
                className="border-l-2 border-[var(--color-accent)] py-1 pl-4 text-sm leading-6 text-[var(--color-muted)]"
              >
                {item}
              </li>
            ))}
          </ul>
        </SectionContainer>
      </section>

      <ConsultationBand />

      <ContentBand>
        <div className="grid gap-10 lg:grid-cols-[0.65fr_1.35fr]">
          <div>
            <p className="eyebrow">Common questions</p>
            <h2 className="section-title mt-4">Before the first discussion.</h2>
          </div>
          <div className="divide-y divide-[var(--color-line)] border-y border-[var(--color-line)]">
            <Faq
              question="Can we contact Sari Arta before the floor plan is final?"
              answer="Yes. Early information about the operation, location, capacity, and timeline can identify the next engineering inputs. A final scope is confirmed only after review."
            />
            <Faq
              question="Does Sari Arta only supply equipment?"
              answer="The project approach can include kitchen planning, equipment and manufacturing coordination, logistics interfaces, local installation, commissioning, and handover support, subject to the agreed scope."
            />
            <Faq
              question="How does the China–Indonesia model work?"
              answer="Manufacturing capability and technical information are coordinated with the approved project scope, while site readiness, installation, commissioning, and project communication are managed locally in Indonesia."
            />
            <Faq
              question="What happens after an inquiry is submitted?"
              answer="The inquiry is recorded for the Sari Arta sales team. A person reviews the project information and determines the appropriate follow-up; submission does not create a quotation or delivery commitment."
            />
          </div>
        </div>
      </ContentBand>
    </>
  );
}

function DeliveryCard({
  label,
  title,
  items,
}: {
  label: string;
  title: string;
  items: string[];
}) {
  return (
    <article className="rounded-2xl border border-white/15 bg-white/5 p-6">
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#d4a48e]">
        {label}
      </p>
      <h3 className="mt-4 text-xl font-semibold">{title}</h3>
      <ul className="mt-6 grid gap-3 text-sm text-white/65">
        {items.map((item) => (
          <li key={item} className="border-l border-white/25 pl-3">
            {item}
          </li>
        ))}
      </ul>
    </article>
  );
}

function Faq({ question, answer }: { question: string; answer: string }) {
  return (
    <details className="group py-5">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-5 font-semibold">
        {question}
        <span className="text-xl text-[var(--color-accent)] group-open:rotate-45">
          +
        </span>
      </summary>
      <p className="max-w-2xl pt-4 text-sm leading-7 text-[var(--color-muted)]">
        {answer}
      </p>
    </details>
  );
}
