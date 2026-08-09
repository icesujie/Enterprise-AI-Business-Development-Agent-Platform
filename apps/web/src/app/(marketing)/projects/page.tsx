import type { Metadata } from "next";

import {
  ConsultationBand,
  ContentBand,
  InnerPageHero,
} from "@/components/marketing/inner-page";
import { ProjectCard } from "@/components/marketing/project-card";
import { deliveryStages, sampleProjects } from "@/content/public-site";

export const metadata: Metadata = {
  title: "Commercial Kitchen Project Scenarios",
  description:
    "Explore clearly labelled sample scenarios showing Sari Arta's approach to school, hospital, factory cafeteria, and central kitchen engineering projects.",
};

export default function ProjectsPage() {
  return (
    <>
      <InnerPageHero
        eyebrow="Projects & case studies"
        title="Project evidence should explain the problem, responsibility, and delivery approach."
        description="Approved customer case studies will be added when facts and permissions are available. Until then, the scenarios below are explicitly demonstration content—not claims of completed Sari Arta projects."
      />

      <ContentBand tone="white">
        <div className="rounded-2xl border border-[var(--color-info)]/20 bg-[var(--color-info-soft)] p-5 text-sm leading-6 text-[var(--color-info)]">
          <strong>Demo content notice:</strong> Names, capacities, locations,
          and challenges on this page are illustrative scenarios created to
          demonstrate the project-review format. They do not identify real
          customers or completed work.
        </div>
        <div className="mt-10 grid gap-6 lg:grid-cols-3">
          {sampleProjects.map((project) => (
            <ProjectCard key={project.title} {...project} />
          ))}
        </div>
      </ContentBand>

      <ContentBand>
        <div className="grid gap-12 lg:grid-cols-[0.7fr_1.3fr]">
          <div>
            <p className="eyebrow">Case-study standard</p>
            <h2 className="section-title mt-4">
              What a real project page will document.
            </h2>
            <p className="mt-5 max-w-lg text-sm leading-7 text-[var(--color-muted)]">
              Every published case must separate verified facts from editorial
              explanation and protect confidential project information.
            </p>
          </div>
          <ol className="grid gap-px overflow-hidden rounded-2xl border border-[var(--color-line)] bg-[var(--color-line)] sm:grid-cols-2">
            {[
              [
                "01",
                "Operating context",
                "Facility type, location, stakeholders, capacity, service pattern, and approved project facts.",
              ],
              [
                "02",
                "Challenge",
                "The workflow, site, programme, coordination, or operating constraint that shaped the project.",
              ],
              [
                "03",
                "Sari Arta responsibility",
                "The exact design, manufacturing, logistics, installation, commissioning, or support scope.",
              ],
              [
                "04",
                "Verified result",
                "Approved completion evidence and outcomes without unsupported performance claims.",
              ],
            ].map(([number, title, description]) => (
              <li key={number} className="bg-white p-6">
                <span className="text-xs font-bold text-[var(--color-accent)]">
                  {number}
                </span>
                <h3 className="mt-6 font-semibold">{title}</h3>
                <p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">
                  {description}
                </p>
              </li>
            ))}
          </ol>
        </div>
      </ContentBand>

      <ContentBand tone="dark">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#d4a48e]">
          Complete project delivery
        </p>
        <h2 className="section-title mt-4 max-w-4xl">
          Each case connects decisions across the full delivery sequence.
        </h2>
        <ol className="mt-12 grid gap-5 md:grid-cols-5">
          {deliveryStages.map((stage) => (
            <li key={stage.number} className="border-t border-white/20 pt-5">
              <span className="text-xs font-bold text-[#d4a48e]">
                {stage.number}
              </span>
              <h3 className="mt-4 text-sm font-semibold">{stage.title}</h3>
            </li>
          ))}
        </ol>
      </ContentBand>

      <ConsultationBand title="Have a project challenge that needs a coordinated kitchen-engineering response?" />
    </>
  );
}
