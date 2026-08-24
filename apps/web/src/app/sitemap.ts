import type { MetadataRoute } from "next";

import { buildCaseStudySitemapRoutes } from "@/content/case-studies";
import { buildGuideSitemapRoutes } from "@/content/guides";
import { buildSitemap, publishedPublicRoutes } from "@/lib/search-foundation";

export default function sitemap(): MetadataRoute.Sitemap {
  return buildSitemap([
    ...publishedPublicRoutes,
    ...buildCaseStudySitemapRoutes(),
    ...buildGuideSitemapRoutes(),
  ]);
}
