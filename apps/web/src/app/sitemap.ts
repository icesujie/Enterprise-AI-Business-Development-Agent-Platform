import type { MetadataRoute } from "next";

import { buildCaseStudySitemapRoutes } from "@/content/case-studies";
import { buildGuideSitemapRoutes } from "@/content/guides";
import { getPublishedCmsRoutes } from "@/lib/public-content";
import { buildSitemap, publishedPublicRoutes } from "@/lib/search-foundation";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const cmsRoutes = await publishedCmsSitemapRoutes();
  return buildSitemap([
    ...publishedPublicRoutes,
    ...buildCaseStudySitemapRoutes(),
    ...buildGuideSitemapRoutes(),
    ...cmsRoutes,
  ]);
}

async function publishedCmsSitemapRoutes() {
  const results = await Promise.allSettled([
    getPublishedCmsRoutes("en"),
    getPublishedCmsRoutes("zh-CN"),
  ]);
  return results
    .flatMap((result) => (result.status === "fulfilled" ? result.value : []))
    .map((route) => ({
      path: route.canonical_path,
      status: "published" as const,
      isPublic: true,
      lastModified: new Date(route.published_at),
      changeFrequency: "monthly" as const,
      priority: route.page_type === "product" ? 0.7 : 0.8,
    }));
}
