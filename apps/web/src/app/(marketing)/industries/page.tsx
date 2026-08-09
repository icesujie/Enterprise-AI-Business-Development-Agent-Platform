import type { Metadata } from "next";

import {
  ConsultationBand,
  ContentBand,
  InnerPageHero,
} from "@/components/marketing/inner-page";
import { industries } from "@/content/public-site";

export const metadata: Metadata = {
  title: "School, Hospital & Central Kitchen Solutions",
  description:
    "Commercial kitchen engineering for schools, hospitals, factories, corporate cafeterias, and central kitchens in Indonesia.",
  keywords: [
    "school kitchen design",
    "hospital kitchen solution",
    "factory cafeteria kitchen",
    "central kitchen solution",
  ],
};

export default function IndustriesPage() {
  return (
    <>
      <InnerPageHero
        eyebrow="Industry solutions"
        title="Every food-service environment creates a different engineering problem."
        description="Sari Arta starts with operating demand: who the kitchen serves, when meals must move, how production is separated, and how the facility will be maintained."
      />

      <ContentBand>
        <div className="grid gap-6 lg:grid-cols-2">
          {industries.map((industry) => (
            <article
              key={industry.slug}
              id={industry.slug}
              className="card scroll-mt-28 overflow-hidden"
            >
              <div className="border-b border-[var(--color-line)] bg-[var(--color-brand-strong)] p-7 text-white sm:p-9">
                <span className="text-xs font-bold text-[#d4a48e]">
                  {industry.number}
                </span>
                <h2 className="mt-8 text-3xl font-semibold tracking-tight">
                  {industry.title}
                </h2>
                <p className="mt-4 max-w-xl text-sm leading-7 text-white/65">
                  {industry.description}
                </p>
              </div>
              <div className="p-7 sm:p-9">
                <p className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--color-muted)]">
                  Engineering priorities
                </p>
                <ul className="mt-5 grid gap-3">
                  {industry.priorities.map((priority) => (
                    <li
                      key={priority}
                      className="border-l-2 border-[var(--color-accent)] pl-4 text-sm leading-6"
                    >
                      {priority}
                    </li>
                  ))}
                </ul>
                <a
                  href={`/contact?industry=${industry.slug}`}
                  className="button-tertiary mt-7"
                >
                  Discuss a {industry.title.toLowerCase()} project →
                </a>
              </div>
            </article>
          ))}
        </div>
      </ContentBand>

      <ContentBand tone="white">
        <div className="grid gap-12 lg:grid-cols-[0.72fr_1.28fr]">
          <div>
            <p className="eyebrow">Shared engineering principles</p>
            <h2 className="section-title mt-4">
              Different sectors, one disciplined planning method.
            </h2>
          </div>
          <div className="grid gap-px overflow-hidden rounded-2xl border border-[var(--color-line)] bg-[var(--color-line)] sm:grid-cols-2">
            {[
              [
                "Capacity",
                "Plan equipment and flow around meals per period, peak demand, menu, and operating hours.",
              ],
              [
                "Movement",
                "Separate receiving, storage, preparation, cooking, service, return, and washing routes where required.",
              ],
              [
                "Utilities",
                "Coordinate electrical, gas, water, drainage, exhaust, access, and space around the approved design.",
              ],
              [
                "Maintainability",
                "Consider cleaning, service access, staff routines, spare capacity, and operational handover.",
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
        <p className="mt-8 max-w-3xl text-xs leading-5 text-[var(--color-muted)]">
          Sector-specific standards, clinical requirements, food-safety rules,
          and building requirements must be confirmed by the responsible project
          professionals. Website content is not a compliance guarantee.
        </p>
      </ContentBand>

      <ConsultationBand title="Tell us what your kitchen must produce, serve, and support." />
    </>
  );
}
