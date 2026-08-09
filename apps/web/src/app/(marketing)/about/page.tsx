import type { Metadata } from "next";

import {
  ConsultationBand,
  ContentBand,
  InnerPageHero,
} from "@/components/marketing/inner-page";

export const metadata: Metadata = {
  title: "About Sari Arta",
  description:
    "Learn how Sari Arta coordinates commercial kitchen engineering, China-based manufacturing capability, and local installation in Indonesia.",
};

export default function AboutPage() {
  return (
    <>
      <InnerPageHero
        eyebrow="About Sari Arta"
        title="An Indonesia commercial kitchen engineering partner built around project coordination."
        description="Sari Arta helps project owners connect operating requirements, commercial kitchen design, equipment manufacturing, logistics, local installation, and handover through one clear delivery framework."
      />

      <ContentBand tone="white">
        <div className="grid gap-12 lg:grid-cols-[0.78fr_1.22fr]">
          <div>
            <p className="eyebrow">Our role</p>
            <h2 className="section-title mt-4">
              Keep the operating need connected to every technical decision.
            </h2>
          </div>
          <div className="space-y-6 text-base leading-8 text-[var(--color-muted)]">
            <p>
              Commercial kitchen projects involve more than selecting cooking
              equipment. Menu, meal volume, staff routes, hygiene flow,
              utilities, site access, procurement, installation, and service all
              affect whether the completed kitchen can operate as intended.
            </p>
            <p>
              Sari Arta provides a coordination point across those decisions.
              The team develops the project requirement with the customer,
              aligns the approved equipment scope with China-based manufacturing
              capability, and coordinates local delivery and installation in
              Indonesia.
            </p>
            <p>
              Exact deliverables, partner responsibilities, standards,
              commercial terms, and service coverage are confirmed for each
              project before commitment.
            </p>
          </div>
        </div>
      </ContentBand>

      <ContentBand tone="dark">
        <div className="grid gap-12 lg:grid-cols-2">
          <OperatingCard
            label="China manufacturing capability"
            title="Turn an approved equipment scope into coordinated production information."
            description="Sari Arta works with approved manufacturing resources to align technical requirements, equipment information, quality checkpoints, release status, and shipping inputs. The website does not imply ownership of a partner factory."
          />
          <OperatingCard
            label="Indonesia local delivery"
            title="Keep site preparation, installation, and handover accountable locally."
            description="Indonesia-based project coordination connects site access, utilities, delivery sequence, installation, testing, commissioning, and operator handover to the agreed project scope."
          />
        </div>
      </ContentBand>

      <ContentBand>
        <div className="grid gap-12 lg:grid-cols-[0.68fr_1.32fr]">
          <div>
            <p className="eyebrow">Working principles</p>
            <h2 className="section-title mt-4">Clarity before commitment.</h2>
          </div>
          <div className="grid gap-px overflow-hidden rounded-2xl border border-[var(--color-line)] bg-[var(--color-line)] sm:grid-cols-2">
            {[
              [
                "Start with the operation",
                "Define who the kitchen serves, what it produces, and when demand peaks before finalising equipment.",
              ],
              [
                "Make responsibility visible",
                "Identify customer, consultant, contractor, manufacturer, logistics, installation, and service interfaces.",
              ],
              [
                "Use controlled quality gates",
                "Review technical information and readiness at agreed points before manufacturing release, delivery, and handover.",
              ],
              [
                "Keep humans accountable",
                "People approve commercial, technical, schedule, warranty, and contractual commitments.",
              ],
            ].map(([title, description]) => (
              <article key={title} className="bg-white p-7">
                <h3 className="text-lg font-semibold">{title}</h3>
                <p className="mt-3 text-sm leading-7 text-[var(--color-muted)]">
                  {description}
                </p>
              </article>
            ))}
          </div>
        </div>
      </ContentBand>

      <ConsultationBand />
    </>
  );
}

function OperatingCard({
  label,
  title,
  description,
}: {
  label: string;
  title: string;
  description: string;
}) {
  return (
    <article className="rounded-2xl border border-white/15 bg-white/5 p-7 sm:p-9">
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#d4a48e]">
        {label}
      </p>
      <h2 className="mt-6 text-2xl font-semibold leading-tight">{title}</h2>
      <p className="mt-5 text-sm leading-7 text-white/60">{description}</p>
    </article>
  );
}
