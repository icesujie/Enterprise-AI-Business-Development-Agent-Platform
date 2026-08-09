import {
  ConsultationBand,
  ContentBand,
  InnerPageHero,
} from "@/components/marketing/inner-page";

export default function AboutPage() {
  return (
    <>
      <InnerPageHero
        eyebrow="About Sari Arta"
        title="Engineering clarity. Manufacturing reach. Local accountability."
        description="This page foundation is ready for approved company history, team roles, operating evidence, and service coverage."
      />
      <ContentBand tone="white">
        <div className="grid gap-12 lg:grid-cols-2">
          <div>
            <p className="eyebrow">Operating model</p>
            <h2 className="section-title mt-4">
              China manufacturing resources, coordinated for Indonesia delivery.
            </h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <article className="card p-6">
              <span className="text-xs font-bold text-[var(--color-accent)]">
                CHINA
              </span>
              <h3 className="mt-5 text-lg font-semibold">
                Manufacturing coordination
              </h3>
              <p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">
                Approved partner language, quality controls, and
                responsibilities will be added after evidence review.
              </p>
            </article>
            <article className="card p-6">
              <span className="text-xs font-bold text-[var(--color-accent)]">
                INDONESIA
              </span>
              <h3 className="mt-5 text-lg font-semibold">
                Project and site delivery
              </h3>
              <p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">
                Local planning, coordination, installation, commissioning, and
                service scope will be stated precisely.
              </p>
            </article>
          </div>
        </div>
      </ContentBand>
      <ConsultationBand />
    </>
  );
}
