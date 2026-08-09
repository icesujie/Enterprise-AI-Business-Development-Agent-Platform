import Link from "next/link";

import { LanguageSwitcher } from "@/components/i18n/language-switcher";
import { SectionContainer } from "@/components/layout/section-container";
import { ButtonLink } from "@/components/ui/button";
import { getMessages } from "@/i18n/server";

export async function MarketingHeader() {
  const { public: copy } = await getMessages();
  const links = [
    [copy.solutions, "/solutions"],
    [copy.industries, "/industries"],
    [copy.projects, "/projects"],
    [copy.about, "/about"],
    [copy.contact, "/contact"],
  ] as const;
  return (
    <header className="sticky top-0 z-50 border-b border-[var(--color-line)]/80 bg-[var(--color-canvas)]/95 backdrop-blur">
      <SectionContainer className="flex h-[74px] items-center justify-between gap-6">
        <Link
          href="/"
          className="group flex items-center gap-3"
          aria-label="Sari Arta home"
        >
          <span className="grid h-10 w-10 place-items-center rounded-full bg-[var(--color-brand)] text-xs font-black tracking-wider text-white">
            SA
          </span>
          <span>
            <span className="block text-sm font-extrabold tracking-[0.14em]">
              SARI ARTA
            </span>
            <span className="hidden text-[0.62rem] font-semibold uppercase tracking-[0.18em] text-[var(--color-muted)] sm:block">
              {copy.kitchenEngineering}
            </span>
          </span>
        </Link>

        <nav
          className="hidden items-center gap-7 lg:flex"
          aria-label={copy.navigation}
        >
          {links.map(([label, href]) => (
            <Link
              key={href}
              href={href}
              className="text-sm font-semibold text-[var(--color-muted)] transition hover:text-[var(--color-ink)]"
            >
              {label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-4 lg:flex">
          <LanguageSwitcher />
          <ButtonLink href="/contact">{copy.consultation}</ButtonLink>
        </div>

        <details className="mobile-menu relative lg:hidden">
          <summary
            className="button-secondary"
            aria-label={copy.openNavigation}
          >
            {copy.menu}
          </summary>
          <div className="absolute right-0 top-14 w-[min(21rem,calc(100vw-2.5rem))] rounded-2xl border border-[var(--color-line)] bg-white p-4 shadow-2xl">
            <nav className="grid" aria-label={copy.navigation}>
              {links.map(([label, href]) => (
                <Link
                  key={href}
                  href={href}
                  className="rounded-lg px-3 py-3 text-sm font-semibold hover:bg-[var(--color-canvas)]"
                >
                  {label}
                </Link>
              ))}
            </nav>
            <div className="mt-3">
              <LanguageSwitcher />
            </div>
            <ButtonLink href="/contact" className="mt-3 w-full">
              {copy.consultation}
            </ButtonLink>
          </div>
        </details>
      </SectionContainer>
    </header>
  );
}
