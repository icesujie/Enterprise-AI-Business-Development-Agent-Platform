import type { Metadata } from "next";
import Link from "next/link";

import { SectionContainer } from "@/components/layout/section-container";
import { InnerPageHero } from "@/components/marketing/inner-page";
import { Card } from "@/components/ui/card";

import { ConsultationForm } from "./consultation-form";

export const metadata: Metadata = {
  title: "Request a Commercial Kitchen Consultation",
  description:
    "Share your commercial kitchen project location, facility type, estimated size, timeline, and requirements with Sari Arta.",
  robots: { index: true, follow: true },
};

export default async function ContactPage({
  searchParams,
}: PageProps<"/contact">) {
  const submitted = (await searchParams).submitted === "1";

  return (
    <>
      <InnerPageHero
        eyebrow="Contact & project consultation"
        title={
          submitted
            ? "Your project brief has been received."
            : "Start with the project information you already have."
        }
        description={
          submitted
            ? "The Sari Arta team can now review the operating context and determine the appropriate human follow-up."
            : "Tell Sari Arta what the kitchen must serve, where the project is located, and when it needs to operate. Early-stage estimates are welcome."
        }
      />
      <section className="py-16 sm:py-20 lg:py-24">
        <SectionContainer>
          {submitted ? (
            <Confirmation />
          ) : (
            <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_360px]">
              <ConsultationForm />
              <aside className="space-y-6 xl:sticky xl:top-28 xl:self-start">
                <Card className="bg-[var(--color-brand)] p-7 text-white">
                  <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#d4a48e]">
                    Useful starting information
                  </p>
                  <ul className="mt-6 grid gap-4 text-sm leading-6 text-white/70">
                    {[
                      "Facility type and project location",
                      "Approximate area or meals per service period",
                      "Target opening or renovation schedule",
                      "Menu, operating hours, and shift pattern",
                      "Current drawing and site-readiness status",
                    ].map((item) => (
                      <li key={item} className="border-l border-white/30 pl-3">
                        {item}
                      </li>
                    ))}
                  </ul>
                  <p className="mt-7 border-t border-white/15 pt-5 text-xs leading-5 text-white/50">
                    Floor-plan upload is intentionally unavailable until secure
                    file handling is implemented.
                  </p>
                </Card>
                <Card id="privacy" className="scroll-mt-28 p-7">
                  <p className="eyebrow">How the information is used</p>
                  <p className="mt-4 text-sm leading-7 text-[var(--color-muted)]">
                    The submitted details are recorded in the Sari Arta business
                    development system for project review and requested
                    follow-up. Marketing permission is separate and optional.
                  </p>
                </Card>
              </aside>
            </div>
          )}
        </SectionContainer>
      </section>
    </>
  );
}

function Confirmation() {
  return (
    <Card className="mx-auto max-w-3xl p-8 text-center sm:p-12">
      <span className="mx-auto grid h-14 w-14 place-items-center rounded-full bg-[var(--color-success-soft)] text-xl font-bold text-[var(--color-success)]">
        ✓
      </span>
      <h2 className="mt-6 text-3xl font-semibold tracking-tight">
        Thank you for sharing the project.
      </h2>
      <p className="mx-auto mt-4 max-w-xl text-sm leading-7 text-[var(--color-muted)]">
        A person will review the facility type, location, scale, timeline, and
        requirements. If further information is needed, the team can use the
        contact details you provided.
      </p>
      <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
        <Link href="/solutions" className="button-primary">
          Review delivery approach
        </Link>
        <Link href="/" className="button-secondary">
          Return to homepage
        </Link>
      </div>
    </Card>
  );
}
