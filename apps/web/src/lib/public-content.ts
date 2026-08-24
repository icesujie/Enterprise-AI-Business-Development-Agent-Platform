import "server-only";

import type { Locale } from "@/i18n/config";

export type PublicPageType = "solution" | "industry" | "case_study" | "guide";

export type PublishedCmsPage = {
  page_type: PublicPageType;
  slug: string;
  locale: Locale;
  title: string;
  summary: string;
  seo_title: string;
  seo_description: string;
  canonical_path: string;
  structured_content: Record<string, unknown>;
};

const apiBaseUrl = process.env.API_BASE_URL ?? "http://localhost:8000";

export async function getPublishedCmsPage(
  pageType: PublicPageType,
  slug: string,
  locale: Locale,
): Promise<PublishedCmsPage | null> {
  const query = new URLSearchParams({ locale });
  const response = await fetch(
    `${apiBaseUrl}/api/v1/public-content/render/${pageType}/${encodeURIComponent(slug)}?${query}`,
    {
      next: {
        revalidate: 30,
        tags: [
          "public-content",
          `public-content:${pageType}:${slug}:${locale}`,
        ],
      },
    },
  );
  if (response.status === 404) return null;
  if (!response.ok) {
    throw new Error(`Public content read failed (${response.status}).`);
  }
  return (await response.json()) as PublishedCmsPage;
}
