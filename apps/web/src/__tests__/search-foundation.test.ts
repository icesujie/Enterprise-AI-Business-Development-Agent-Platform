import { afterEach, beforeEach, describe, expect, test } from "vitest";

import robots from "@/app/robots";
import sitemap from "@/app/sitemap";
import { serializeStructuredData } from "@/components/seo/structured-data";
import {
  classifyAcquisitionSource,
  type AcquisitionSource,
} from "@/lib/acquisition-attribution";
import {
  buildSitemap,
  isPrivateSearchRoute,
  type PublishedPublicRoute,
} from "@/lib/search-foundation";
import { eligibleIndexNowUrls, isIndexNowEnabled } from "@/lib/indexnow-policy";
import {
  buildPublicPageMetadata,
  buildPublicRouteMetadata,
  privateMetadata,
} from "@/lib/seo";
import {
  buildBreadcrumbStructuredData,
  buildFutureArticleStructuredData,
  buildFutureCaseStudyStructuredData,
  buildFutureServiceStructuredData,
  buildSiteStructuredData,
} from "@/lib/structured-data";

const originalSiteUrl = process.env.NEXT_PUBLIC_SITE_URL;

beforeEach(() => {
  process.env.NEXT_PUBLIC_SITE_URL = "https://www.sariarta.example";
});

afterEach(() => {
  if (originalSiteUrl === undefined) delete process.env.NEXT_PUBLIC_SITE_URL;
  else process.env.NEXT_PUBLIC_SITE_URL = originalSiteUrl;
});

describe("crawl boundary", () => {
  test("allows public crawling for general and named search crawlers", () => {
    const result = robots();
    expect(result.sitemap).toBe("https://www.sariarta.example/sitemap.xml");
    expect(result.host).toBe("https://www.sariarta.example");
    expect(result.rules).toEqual(
      expect.arrayContaining(
        ["*", "Googlebot", "Bingbot", "OAI-SearchBot"].map((userAgent) =>
          expect.objectContaining({
            userAgent,
            allow: "/",
            disallow: expect.arrayContaining([
              "/dashboard",
              "/knowledge",
              "/agent-playground",
              "/marketing-content",
              "/login",
            ]),
          }),
        ),
      ),
    );
  });

  test("classifies every authenticated or internal route as private", () => {
    for (const path of [
      "/dashboard",
      "/leads/lead-id",
      "/opportunities",
      "/knowledge/assistant",
      "/agent-playground",
      "/marketing-content/asset-id",
      "/login",
      "/inquiry",
    ]) {
      expect(isPrivateSearchRoute(path)).toBe(true);
    }
    for (const path of [
      "/",
      "/solutions",
      "/industries",
      "/projects",
      "/about",
      "/contact",
    ]) {
      expect(isPrivateSearchRoute(path)).toBe(false);
    }
    expect(privateMetadata.robots).toEqual(
      expect.objectContaining({ index: false, follow: false }),
    );
  });
});

describe("sitemap publication rules", () => {
  test("contains canonical public routes and no internal routes", () => {
    const urls = sitemap().map((entry) => entry.url);
    expect(urls).toEqual([
      "https://www.sariarta.example/",
      "https://www.sariarta.example/solutions",
      "https://www.sariarta.example/industries",
      "https://www.sariarta.example/projects",
      "https://www.sariarta.example/about",
      "https://www.sariarta.example/contact",
      "https://www.sariarta.example/solutions/school-canteen-kitchen",
      "https://www.sariarta.example/industries/schools",
    ]);
    expect(urls.some((url) => url.includes("knowledge"))).toBe(false);
  });

  test("adds only explicitly public published future pages", () => {
    const candidates: PublishedPublicRoute[] = [
      { path: "/guides/kitchen-capacity", status: "published", isPublic: true },
      { path: "/projects/approved-case", status: "published", isPublic: true },
      { path: "/guides/draft", status: "draft", isPublic: true },
      { path: "/projects/private", status: "published", isPublic: false },
      { path: "/knowledge/internal", status: "published", isPublic: true },
      { path: "/guides/query?internal=1", status: "published", isPublic: true },
    ];
    const urls = buildSitemap(candidates).map((entry) => entry.url);
    expect(urls).toContain(
      "https://www.sariarta.example/guides/kitchen-capacity",
    );
    expect(urls).toContain(
      "https://www.sariarta.example/projects/approved-case",
    );
    expect(urls).not.toContain("https://www.sariarta.example/guides/draft");
    expect(urls.some((url) => url.includes("knowledge"))).toBe(false);
    expect(urls.some((url) => url.includes("?"))).toBe(false);
  });
});

describe("metadata and structured data", () => {
  test("renders canonical bilingual metadata without keyword stuffing", () => {
    const english = buildPublicPageMetadata("solutions", "en");
    const chinese = buildPublicPageMetadata("solutions", "zh-CN");
    expect(english.alternates).toEqual({
      canonical: "https://www.sariarta.example/solutions",
    });
    expect(english.openGraph).toEqual(
      expect.objectContaining({ locale: "en_US" }),
    );
    expect(chinese.openGraph).toEqual(
      expect.objectContaining({ locale: "zh_CN" }),
    );
    expect(english.keywords).toBeUndefined();
    const school = buildPublicRouteMetadata(
      {
        title: "School Canteen Kitchen Solutions Indonesia",
        description: "Approved public solution description.",
        path: "/solutions/school-canteen-kitchen",
      },
      "en",
    );
    expect(school.alternates).toEqual({
      canonical:
        "https://www.sariarta.example/solutions/school-canteen-kitchen",
    });
    expect(school.openGraph).toEqual(
      expect.objectContaining({
        url: "https://www.sariarta.example/solutions/school-canteen-kitchen",
      }),
    );
  });

  test("uses supported Organization, WebSite, Breadcrumb and future Article data", () => {
    const site = buildSiteStructuredData("en");
    const breadcrumbs = buildBreadcrumbStructuredData([
      { name: "Home", path: "/" },
      { name: "Solutions", path: "/solutions" },
    ]);
    const article = buildFutureArticleStructuredData({
      headline: "Capacity planning guide",
      description: "A synthetic structured-data contract test.",
      path: "/guides/capacity-planning",
      datePublished: "2026-08-16",
      language: "en",
    });
    const caseStudy = buildFutureCaseStudyStructuredData({
      headline: "Approved school kitchen case",
      description: "Approved public case description.",
      path: "/projects/approved-school-kitchen",
      datePublished: "2026-08-16",
      language: "en",
      industry: "Education",
    });
    const service = buildFutureServiceStructuredData({
      name: "Commercial kitchen design",
      description: "Approved public service description.",
      path: "/solutions/commercial-kitchen-design",
      language: "en",
    });
    expect(site["@graph"]).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ "@type": "Organization", name: "Sari Arta" }),
        expect.objectContaining({ "@type": "WebSite", inLanguage: "en" }),
      ]),
    );
    expect(breadcrumbs).toEqual(
      expect.objectContaining({ "@type": "BreadcrumbList" }),
    );
    expect(article).toEqual(expect.objectContaining({ "@type": "Article" }));
    expect(caseStudy.articleSection).toEqual(["Case Study", "Education"]);
    expect(service["@type"]).toBe("Service");
    expect(
      serializeStructuredData({ value: "</script><script>alert(1)</script>" }),
    ).not.toContain("</script>");
  });
});

test("classifies lightweight acquisition sources without changing lead channel", () => {
  const cases: Array<[string, string | null, AcquisitionSource]> = [
    ["utm_source=google&utm_medium=organic", null, "organic_google"],
    ["utm_source=bing", null, "organic_bing"],
    ["", "chatgpt.com", "ai_search"],
    ["utm_medium=social", null, "social"],
    ["", "partner.example", "referral"],
    ["", null, "direct"],
  ];
  for (const [query, referrer, expected] of cases) {
    expect(
      classifyAcquisitionSource(new URLSearchParams(query), referrer),
    ).toBe(expected);
  }
});

test("keeps IndexNow disabled and filters every non-public candidate", () => {
  const candidates = [
    { path: "/solutions", status: "published" as const, isPublic: true },
    {
      path: "/guides/approved-guide",
      status: "published" as const,
      isPublic: true,
    },
    { path: "/guides/draft", status: "draft" as const, isPublic: true },
    {
      path: "/marketing-content/internal",
      status: "published" as const,
      isPublic: true,
    },
  ];
  expect(eligibleIndexNowUrls(candidates)).toEqual([
    "https://www.sariarta.example/solutions",
    "https://www.sariarta.example/guides/approved-guide",
  ]);
  expect(isIndexNowEnabled("false")).toBe(false);
});
