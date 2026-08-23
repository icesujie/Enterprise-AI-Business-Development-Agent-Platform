import type { MetadataRoute } from "next";

import { buildCaseStudySitemapRoutes } from "@/content/case-studies";
import { buildSitemap, publishedPublicRoutes } from "@/lib/search-foundation";

export default function sitemap(): MetadataRoute.Sitemap {
  return buildSitemap([
    ...publishedPublicRoutes,
    ...buildCaseStudySitemapRoutes(),
  ]);
}
