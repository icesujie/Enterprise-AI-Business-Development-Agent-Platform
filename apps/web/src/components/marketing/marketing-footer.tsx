import Link from "next/link";

import { SectionContainer } from "@/components/layout/section-container";

export function MarketingFooter() {
  return (
    <footer className="bg-[var(--color-ink)] py-14 text-white">
      <SectionContainer>
        <div className="grid gap-10 border-b border-white/15 pb-12 md:grid-cols-[1.5fr_1fr_1fr_1fr]">
          <div>
            <p className="text-sm font-extrabold tracking-[0.16em]">
              SARI ARTA
            </p>
            <p className="mt-4 max-w-sm text-sm leading-6 text-white/60">
              Commercial kitchen design, manufacturing coordination, and local
              project delivery for institutional and industrial operations in
              Indonesia.
            </p>
          </div>
          <FooterGroup
            title="Explore"
            links={[
              ["Solutions", "/solutions"],
              ["Industries", "/industries"],
              ["Projects", "/projects"],
            ]}
          />
          <FooterGroup
            title="Company"
            links={[
              ["About Us", "/about"],
              ["Contact", "/contact"],
            ]}
          />
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-white/45">
              Project inquiry
            </p>
            <Link
              href="/contact"
              className="mt-4 inline-block text-sm font-semibold underline decoration-white/30 underline-offset-4"
            >
              Request kitchen consultation
            </Link>
          </div>
        </div>
        <div className="flex flex-col gap-3 pt-7 text-xs text-white/45 sm:flex-row sm:items-center sm:justify-between">
          <p>© 2026 Sari Arta. All project scopes remain subject to review.</p>
          <div className="flex gap-5">
            <span>English</span>
            <Link href="/login">Staff access</Link>
          </div>
        </div>
      </SectionContainer>
    </footer>
  );
}

function FooterGroup({
  title,
  links,
}: {
  title: string;
  links: readonly (readonly [string, string])[];
}) {
  return (
    <div>
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-white/45">
        {title}
      </p>
      <div className="mt-4 grid gap-3">
        {links.map(([label, href]) => (
          <Link
            key={href}
            href={href}
            className="text-sm text-white/75 hover:text-white"
          >
            {label}
          </Link>
        ))}
      </div>
    </div>
  );
}
