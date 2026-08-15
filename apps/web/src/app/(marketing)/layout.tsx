import { MarketingFooter } from "@/components/marketing/marketing-footer";
import { MarketingHeader } from "@/components/marketing/marketing-header";
import { PublicConsultationWidget } from "@/components/marketing/public-consultation-widget";
import { getLocale, getMessages } from "@/i18n/server";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export default async function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const locale = await getLocale();
  const { public: copy } = await getMessages();
  const structuredData = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Organization",
        "@id": `${siteUrl}/#organization`,
        name: "Sari Arta",
        url: siteUrl,
        description:
          "Indonesia commercial kitchen engineering partner coordinating design, manufacturing capability, logistics, installation, and commissioning.",
      },
      {
        "@type": "WebSite",
        "@id": `${siteUrl}/#website`,
        url: siteUrl,
        name: "Sari Arta",
        publisher: { "@id": `${siteUrl}/#organization` },
        inLanguage: locale,
      },
    ],
  };

  return (
    <div className="min-h-screen bg-[var(--color-canvas)]">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <a href="#main-content" className="skip-link">
        {copy.skip}
      </a>
      <MarketingHeader />
      <main id="main-content">{children}</main>
      <MarketingFooter />
      <PublicConsultationWidget
        key={locale}
        initialLanguage={locale === "zh-CN" ? "zh-CN" : "en"}
      />
    </div>
  );
}
