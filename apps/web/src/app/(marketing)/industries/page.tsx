import { IndustryCard } from "@/components/marketing/industry-card";
import {
  ConsultationBand,
  ContentBand,
  InnerPageHero,
} from "@/components/marketing/inner-page";

const industries = [
  [
    "01",
    "School kitchens",
    "Meal volume, service windows, safe workflow, training, and maintainability.",
  ],
  [
    "02",
    "Hospital kitchens",
    "Production separation, distribution, washing, cleaning, and operational reliability.",
  ],
  [
    "03",
    "Factory & corporate cafeterias",
    "Peak-shift throughput, bulk preparation, fast service, and durable equipment planning.",
  ],
  [
    "04",
    "Central kitchens",
    "High-volume production, repeatable flow, dispatch, utilities, and future expansion.",
  ],
] as const;

export default function IndustriesPage() {
  return (
    <>
      <InnerPageHero
        eyebrow="Industries"
        title="Engineering starts with the operating environment."
        description="Different facilities create different flows, risks, service peaks, and stakeholder needs. Industry pages will make that context visible before equipment selection."
      />
      <ContentBand>
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
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
      <ConsultationBand title="Tell us how your operation needs to perform." />
    </>
  );
}
