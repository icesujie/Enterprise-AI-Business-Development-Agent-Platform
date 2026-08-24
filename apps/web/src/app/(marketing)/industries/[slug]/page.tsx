import type { Metadata } from "next";

import {
  buildPublishedPublicMetadata,
  PublishedPublicRoute,
} from "@/components/marketing/published-public-route";
import { getLocale } from "@/i18n/server";

type RouteProps = { params: Promise<{ slug: string }> };

export async function generateMetadata({
  params,
}: RouteProps): Promise<Metadata> {
  const [{ slug }, locale] = await Promise.all([params, getLocale()]);
  return buildPublishedPublicMetadata("industry", slug, locale);
}

export default async function PublicIndustryPage({ params }: RouteProps) {
  const [{ slug }, locale] = await Promise.all([params, getLocale()]);
  return (
    <PublishedPublicRoute pageType="industry" slug={slug} locale={locale} />
  );
}
