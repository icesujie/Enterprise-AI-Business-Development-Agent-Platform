import type { MetadataRoute } from "next";

import { buildSitemap } from "@/lib/search-foundation";

export default function sitemap(): MetadataRoute.Sitemap {
  // Future approved publication records can be passed to buildSitemap here.
  // Draft, internal, non-public, and non-published records are rejected there.
  return buildSitemap();
}
