import type { Metadata } from "next";

import {
  buildPublishedPublicMetadata,
  PublishedPublicRoute,
} from "@/components/marketing/published-public-route";
import { getLocale } from "@/i18n/server";

export async function generateMetadata(): Promise<Metadata> {
  const locale = await getLocale();
  return buildPublishedPublicMetadata("industry", "schools", locale);
}

export default async function SchoolsIndustryPage() {
  const locale = await getLocale();
  return (
    <PublishedPublicRoute pageType="industry" slug="schools" locale={locale} />
  );
}
