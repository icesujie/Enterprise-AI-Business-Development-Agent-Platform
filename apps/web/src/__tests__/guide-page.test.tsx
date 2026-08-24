import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";

import { GuidePage } from "@/components/marketing/guide-page";
import {
  buildGuideSitemapRoutes,
  type GuidePageContent,
  type GuideRecord,
} from "@/content/guides";
import { buildPublicRouteMetadata } from "@/lib/seo";
import {
  buildFaqStructuredData,
  buildFutureArticleStructuredData,
} from "@/lib/structured-data";

afterEach(cleanup);

const syntheticGuide: GuidePageContent = {
  metadataTitle: "Synthetic school kitchen planning guide",
  metadataDescription:
    "Synthetic guide content used only for architecture testing.",
  breadcrumbLabel: "Synthetic planning guide",
  eyebrow: "Synthetic test fixture · not published",
  title: "Synthetic guide page architecture",
  summary:
    "This fixture validates the reusable guide layout and is not business content.",
  introduction: [
    "This introduction is synthetic and exists only in the test suite.",
  ],
  sections: [
    {
      heading: "Synthetic planning section",
      paragraphs: ["Test-only explanatory paragraph."],
      points: ["Test-only planning point"],
    },
  ],
  faqItems: [
    {
      question: "Is this a published Sari Arta guide?",
      answer: "No. It is a synthetic, non-indexable test fixture.",
    },
  ],
  relatedSolutions: [
    {
      label: "School canteen solution",
      href: "/solutions/school-canteen-kitchen",
    },
  ],
  relatedIndustries: [
    { label: "Schools industry", href: "/industries/schools" },
  ],
  relatedProjects: [],
};

test("renders the reusable guide hierarchy, visible FAQ, links, and consultation actions", () => {
  render(<GuidePage content={syntheticGuide} locale="en" />);

  expect(
    screen.getByRole("heading", {
      level: 1,
      name: "Synthetic guide page architecture",
    }),
  ).toBeDefined();
  expect(
    screen.getByRole("heading", {
      level: 2,
      name: "Synthetic planning section",
    }),
  ).toBeDefined();
  expect(
    screen.getByRole("heading", {
      level: 2,
      name: "Frequently asked questions",
    }),
  ).toBeDefined();
  expect(
    screen.getByText("No. It is a synthetic, non-indexable test fixture."),
  ).toBeDefined();
  expect(
    screen
      .getByRole("link", { name: "School canteen solution" })
      .getAttribute("href"),
  ).toBe("/solutions/school-canteen-kitchen");
  expect(
    screen.getByRole("link", { name: "Schools industry" }).getAttribute("href"),
  ).toBe("/industries/schools");
  expect(
    screen.getAllByRole("button", { name: "Start project consultation" }),
  ).toHaveLength(2);
});

test("keeps draft, private, incomplete, and unlinked guides out of the sitemap", () => {
  const base: GuideRecord = {
    slug: "synthetic-guide",
    status: "published",
    isPublic: true,
    publishedAt: "2026-08-23",
    publicationApproval: {
      versionId: "synthetic-version",
      approvedAt: "2026-08-23",
      contentChecksum: "synthetic-checksum",
      factualContentApproved: true,
      publicUseApproved: true,
    },
    content: { en: syntheticGuide, "zh-CN": syntheticGuide },
  };
  const missingProject = {
    ...syntheticGuide,
    relatedProjects: [
      {
        label: "Unpublished synthetic project",
        href: "/projects/unpublished-synthetic-project" as const,
      },
    ],
  };

  expect(
    buildGuideSitemapRoutes([
      { ...base, status: "draft" },
      { ...base, isPublic: false },
      { ...base, publicationApproval: undefined },
      { ...base, content: { en: syntheticGuide } },
      { ...base, content: { en: missingProject, "zh-CN": missingProject } },
    ]),
  ).toEqual([]);
  expect(buildGuideSitemapRoutes([base])).toEqual([
    expect.objectContaining({
      path: "/guides/synthetic-guide",
      status: "published",
      isPublic: true,
    }),
  ]);
});

test("builds canonical Article and FAQ data from the visible guide content", () => {
  const path = "/guides/synthetic-guide";
  const metadata = buildPublicRouteMetadata(
    {
      title: syntheticGuide.metadataTitle,
      description: syntheticGuide.metadataDescription,
      path,
    },
    "en",
  );
  const article = buildFutureArticleStructuredData({
    headline: syntheticGuide.metadataTitle,
    description: syntheticGuide.metadataDescription,
    path,
    datePublished: "2026-08-23",
    language: "en",
  });
  const faq = buildFaqStructuredData(syntheticGuide.faqItems);

  expect(metadata.alternates).toEqual({
    canonical: expect.stringMatching(/\/guides\/synthetic-guide$/),
  });
  expect(metadata.openGraph).toEqual(
    expect.objectContaining({
      url: expect.stringMatching(/\/guides\/synthetic-guide$/),
    }),
  );
  expect(article).toEqual(
    expect.objectContaining({
      "@type": "Article",
      headline: syntheticGuide.metadataTitle,
    }),
  );
  expect(faq).toEqual(
    expect.objectContaining({
      "@type": "FAQPage",
      mainEntity: [
        expect.objectContaining({
          name: syntheticGuide.faqItems[0]!.question,
          acceptedAnswer: expect.objectContaining({
            text: syntheticGuide.faqItems[0]!.answer,
          }),
        }),
      ],
    }),
  );
});
