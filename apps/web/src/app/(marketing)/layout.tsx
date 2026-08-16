import { MarketingFooter } from "@/components/marketing/marketing-footer";
import { MarketingHeader } from "@/components/marketing/marketing-header";
import { PublicConsultationWidget } from "@/components/marketing/public-consultation-widget";
import { StructuredData } from "@/components/seo/structured-data";
import { getLocale, getMessages } from "@/i18n/server";
import { buildSiteStructuredData } from "@/lib/structured-data";

export default async function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const locale = await getLocale();
  const { public: copy } = await getMessages();

  return (
    <div className="min-h-screen bg-[var(--color-canvas)]">
      <StructuredData data={buildSiteStructuredData(locale)} />
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
