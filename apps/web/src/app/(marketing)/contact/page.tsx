import { SectionContainer } from "@/components/layout/section-container";
import { InnerPageHero } from "@/components/marketing/inner-page";
import { ButtonLink } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function ContactPage() {
  return (
    <>
      <InnerPageHero
        eyebrow="Contact & consultation"
        title="Start with the project information you already have."
        description="A Sari Arta specialist will review the inquiry before any technical or commercial commitment is made."
      />
      <section className="py-16 sm:py-20 lg:py-24">
        <SectionContainer className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
          <Card className="p-7 sm:p-10">
            <p className="eyebrow">Project consultation</p>
            <h2 className="mt-5 text-3xl font-semibold tracking-tight">
              Share the essentials.
            </h2>
            <p className="mt-4 max-w-xl leading-7 text-[var(--color-muted)]">
              The existing API-connected inquiry form remains the submission
              path during this foundation stage. It collects contact,
              organization, project context, requirements, and consent.
            </p>
            <ul className="mt-7 grid gap-3 text-sm text-[var(--color-muted)] sm:grid-cols-2">
              {[
                "Organization and contact",
                "Facility and location",
                "Capacity and timeline",
                "Known project requirements",
              ].map((item) => (
                <li
                  key={item}
                  className="border-l-2 border-[var(--color-accent)] pl-3"
                >
                  {item}
                </li>
              ))}
            </ul>
            <ButtonLink href="/inquiry" className="mt-8">
              Start project brief
            </ButtonLink>
          </Card>
          <Card className="bg-[var(--color-brand)] p-7 text-white sm:p-10">
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#d4a48e]">
              Before you begin
            </p>
            <h2 className="mt-5 text-2xl font-semibold">
              Incomplete information is acceptable.
            </h2>
            <p className="mt-4 text-sm leading-7 text-white/65">
              A facility type, location, rough capacity, and target date are
              enough to start a useful conversation. File upload remains
              postponed until secure handling is implemented.
            </p>
            <p className="mt-8 border-t border-white/15 pt-6 text-xs leading-5 text-white/45">
              Preview contact details are intentionally omitted until business
              approval.
            </p>
          </Card>
        </SectionContainer>
      </section>
    </>
  );
}
