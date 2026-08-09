import type { Metadata } from "next";

import {
  ConsultationBand,
  ContentBand,
  InnerPageHero,
} from "@/components/marketing/inner-page";
import { capabilities, deliveryStages } from "@/content/public-site";

export const metadata: Metadata = {
  title: "Commercial Kitchen Design & Project Delivery",
  description:
    "Explore Sari Arta commercial kitchen design, China manufacturing coordination, logistics, installation, commissioning, and after-sales support in Indonesia.",
  keywords: [
    "commercial kitchen design Indonesia",
    "industrial kitchen engineering",
    "commercial kitchen installation Indonesia",
  ],
};

export default function SolutionsPage() {
  return (
    <>
      <InnerPageHero
        eyebrow="Commercial kitchen solutions"
        title="A complete delivery framework, shaped around your operation."
        description="Sari Arta coordinates the project decisions that connect workflow, equipment, manufacturing, logistics, site work, and operational handover. The final responsibility matrix is agreed for every project."
      />

      <ContentBand tone="white">
        <div className="grid gap-6 lg:grid-cols-2">
          {capabilities.map((capability) => (
            <article
              key={capability.number}
              id={capability.shortTitle.toLowerCase()}
              className="card scroll-mt-28 p-7 sm:p-9"
            >
              <span className="text-xs font-bold text-[var(--color-accent)]">
                {capability.number}
              </span>
              <h2 className="mt-7 text-2xl font-semibold tracking-tight">
                {capability.title}
              </h2>
              <p className="mt-4 max-w-xl text-sm leading-7 text-[var(--color-muted)]">
                {capability.description}
              </p>
              <p className="mt-7 text-xs font-bold uppercase tracking-[0.14em] text-[var(--color-muted)]">
                Typical coordination outputs
              </p>
              <ul className="mt-4 grid gap-3 text-sm">
                {capability.deliverables.map((item) => (
                  <li
                    key={item}
                    className="border-l-2 border-[var(--color-accent)] pl-3"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </ContentBand>

      <ContentBand>
        <div className="grid gap-10 lg:grid-cols-[0.75fr_1.25fr]">
          <div>
            <p className="eyebrow">Project inputs</p>
            <h2 className="section-title mt-4">
              Better inputs create clearer engineering decisions.
            </h2>
            <p className="mt-5 max-w-lg text-sm leading-7 text-[var(--color-muted)]">
              Early estimates are acceptable. Sari Arta uses the available
              information to identify gaps before detailed equipment and site
              commitments are made.
            </p>
          </div>
          <div className="grid gap-px overflow-hidden rounded-2xl border border-[var(--color-line)] bg-[var(--color-line)] sm:grid-cols-2">
            {[
              [
                "Operation",
                "Menu, meal volume, service windows, staffing, and cleaning routines.",
              ],
              [
                "Facility",
                "Location, available area, floor plans, access, utilities, and project interfaces.",
              ],
              [
                "Commercial",
                "Target date, known budget range, decision process, and procurement requirements.",
              ],
              [
                "Technical",
                "Applicable consultant inputs, standards, existing assets, and known equipment preferences.",
              ],
            ].map(([title, description]) => (
              <article key={title} className="bg-white p-6">
                <h3 className="font-semibold">{title}</h3>
                <p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">
                  {description}
                </p>
              </article>
            ))}
          </div>
        </div>
      </ContentBand>

      <ContentBand tone="dark">
        <div className="grid gap-10 lg:grid-cols-[0.7fr_1.3fr]">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#d4a48e]">
              Delivery sequence
            </p>
            <h2 className="section-title mt-4">
              Five controlled project stages.
            </h2>
          </div>
          <ol className="grid gap-4">
            {deliveryStages.map((stage) => (
              <li
                key={stage.number}
                className="grid gap-3 border-t border-white/15 pt-5 sm:grid-cols-[80px_180px_1fr]"
              >
                <span className="text-xs font-bold text-[#d4a48e]">
                  {stage.number}
                </span>
                <h3 className="font-semibold">{stage.title}</h3>
                <p className="text-sm leading-6 text-white/60">
                  {stage.description}
                </p>
              </li>
            ))}
          </ol>
        </div>
      </ContentBand>

      <ConsultationBand title="Which parts of your kitchen project need coordinated support?" />
    </>
  );
}
