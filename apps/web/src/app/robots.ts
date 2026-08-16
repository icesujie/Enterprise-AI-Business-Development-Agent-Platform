import type { MetadataRoute } from "next";

import {
  absolutePublicUrl,
  getSiteUrl,
  privateRoutePrefixes,
} from "@/lib/search-foundation";

export default function robots(): MetadataRoute.Robots {
  const crawlRules = {
    allow: "/",
    disallow: [...privateRoutePrefixes],
  };
  return {
    rules: [
      { userAgent: "*", ...crawlRules },
      { userAgent: "Googlebot", ...crawlRules },
      { userAgent: "Bingbot", ...crawlRules },
      { userAgent: "OAI-SearchBot", ...crawlRules },
    ],
    sitemap: absolutePublicUrl("/sitemap.xml"),
    host: getSiteUrl(),
  };
}
