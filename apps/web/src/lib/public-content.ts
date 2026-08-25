import "server-only";

import type { Locale } from "@/i18n/config";

export type PublicPageType =
  "solution" | "industry" | "case_study" | "guide" | "product";

export type PublishedMediaReference = {
  media_asset_id: string;
  role: string;
  mime_type: "image/jpeg" | "image/png" | "image/webp";
  width: number;
  height: number;
  alt_text: string;
  caption: string | null;
  url: string;
};

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
  media_references: PublishedMediaReference[];
  published_at: string;
  version_created_at: string;
};

export type PublishedCmsRoute = {
  page_type: PublicPageType;
  slug: string;
  locale: Locale;
  canonical_path: string;
  published_at: string;
};

export type GovernedPublicContentUnavailable = {
  state: "governed_unavailable";
};

const apiBaseUrl = process.env.API_BASE_URL ?? "http://localhost:8000";
const publicSiteToken = process.env.PUBLIC_SITE_TOKEN;

export async function getPublishedCmsPage(
  pageType: PublicPageType,
  slug: string,
  locale: Locale,
): Promise<PublishedCmsPage | GovernedPublicContentUnavailable | null> {
  const query = new URLSearchParams({ locale });
  const response = await fetch(
    `${apiBaseUrl}/api/v1/public-content/render/${pageType}/${encodeURIComponent(slug)}?${query}`,
    {
      headers: publicSiteToken
        ? { "X-Site-Token": publicSiteToken }
        : undefined,
      next: {
        revalidate: 300,
        tags: [
          "public-content",
          `public-content:${pageType}:${slug}:${locale}`,
        ],
      },
    },
  );
  if (
    response.status === 404 &&
    response.headers.get("X-Public-Content-State") === "governed-unavailable"
  ) {
    return { state: "governed_unavailable" };
  }
  if (response.status === 404) return null;
  if (!response.ok) {
    throw new Error(`Public content read failed (${response.status}).`);
  }
  return (await response.json()) as PublishedCmsPage;
}

export function isGovernedUnavailable(
  value: PublishedCmsPage | GovernedPublicContentUnavailable | null,
): value is GovernedPublicContentUnavailable {
  return (
    value !== null && "state" in value && value.state === "governed_unavailable"
  );
}

export async function getPublishedCmsRoutes(
  locale: Locale,
): Promise<PublishedCmsRoute[]> {
  const query = new URLSearchParams({ locale });
  const response = await fetch(
    `${apiBaseUrl}/api/v1/public-content/catalog/routes?${query}`,
    {
      next: {
        revalidate: 300,
        tags: ["public-content", `public-content-routes:${locale}`],
      },
    },
  );
  if (!response.ok) {
    throw new Error(`Published route read failed (${response.status}).`);
  }
  return (await response.json()) as PublishedCmsRoute[];
}

export async function getPublishedProducts(
  locale: Locale,
): Promise<PublishedCmsPage[]> {
  const query = new URLSearchParams({ locale });
  const response = await fetch(
    `${apiBaseUrl}/api/v1/public-content/catalog/products?${query}`,
    {
      next: {
        revalidate: 300,
        tags: ["public-content", `public-products:${locale}`],
      },
    },
  );
  if (!response.ok) {
    throw new Error(`Public product catalog read failed (${response.status}).`);
  }
  return (await response.json()) as PublishedCmsPage[];
}
