import { SectionContainer } from "@/components/layout/section-container";
import { ButtonLink } from "@/components/ui/button";

export function HeroSection() {
  return (
    <section className="marketing-grid overflow-hidden bg-[var(--color-brand)] py-16 text-white sm:py-20 lg:py-24">
      <SectionContainer className="grid items-center gap-14 lg:grid-cols-[0.88fr_1.12fr]">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#d4a48e]">
            Indonesia Commercial Kitchen Engineering Partner
          </p>
          <h1 className="display-title text-balance mt-6 max-w-3xl">
            Commercial kitchens engineered for real operating demands.
          </h1>
          <p className="mt-7 max-w-xl text-base leading-8 text-white/68 sm:text-lg">
            Sari Arta brings together commercial kitchen design, China-based
            manufacturing capability, and local Indonesia installation to help
            institutional and industrial projects move from requirement to
            operation.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <ButtonLink href="/contact" className="button-inverse">
              Request kitchen consultation
            </ButtonLink>
            <ButtonLink
              href="/solutions"
              variant="secondary"
              className="border-white/25 bg-transparent text-white hover:bg-white/10"
            >
              See how we deliver
            </ButtonLink>
          </div>
          <dl className="mt-12 grid grid-cols-3 gap-4 border-t border-white/15 pt-6">
            {[
              ["01", "Kitchen engineering"],
              ["02", "China manufacturing"],
              ["03", "Indonesia installation"],
            ].map(([value, label]) => (
              <div key={value}>
                <dt className="text-xs font-bold tracking-[0.18em] text-[#d4a48e]">
                  {value}
                </dt>
                <dd className="mt-2 text-xs font-semibold text-white/70 sm:text-sm">
                  {label}
                </dd>
              </div>
            ))}
          </dl>
        </div>
        <div
          className="technical-visual"
          aria-label="Abstract commercial kitchen workflow plan"
        >
          <span className="technical-label left-[7%] top-[12%]">
            Workflow planning
          </span>
          <span className="technical-label bottom-[13%] left-[12%]">
            Indonesia installation
          </span>
          <span className="technical-label right-[7%] top-[35%]">
            Quality gate 03
          </span>
        </div>
      </SectionContainer>
    </section>
  );
}
