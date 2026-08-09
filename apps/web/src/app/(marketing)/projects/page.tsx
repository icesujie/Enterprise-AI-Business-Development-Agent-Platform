import {
  ConsultationBand,
  ContentBand,
  InnerPageHero,
} from "@/components/marketing/inner-page";
import { ProjectCard } from "@/components/marketing/project-card";

export default function ProjectsPage() {
  return (
    <>
      <InnerPageHero
        eyebrow="Projects & case studies"
        title="Proof will be presented as a project story, not a logo wall."
        description="This initial layout shows the evidence structure. Real project names, facts, images, and outcomes will appear only after business approval."
      />
      <ContentBand tone="white">
        <div className="mb-10 flex flex-wrap gap-3">
          {[
            "All projects",
            "Education",
            "Healthcare",
            "Industrial dining",
            "Central kitchens",
          ].map((label, index) => (
            <span
              key={label}
              className={index === 0 ? "button-primary" : "button-secondary"}
            >
              {label}
            </span>
          ))}
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          <ProjectCard
            sector="Project template"
            title="Evidence-led school kitchen case"
            scope="Context, constraints, operating requirements, Sari Arta responsibility, delivery approach, and verified result."
          />
          <ProjectCard
            sector="Project template"
            title="Evidence-led central kitchen case"
            scope="A clear separation of project facts, engineering decisions, manufacturing coordination, and local installation."
          />
        </div>
      </ContentBand>
      <ConsultationBand title="Planning a project with similar operating challenges?" />
    </>
  );
}
