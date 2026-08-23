import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";

import { CaseStudyPage } from "@/components/marketing/case-study-page";
import {
  buildCaseStudySitemapRoutes,
  type CaseStudyPageContent,
  type CaseStudyRecord,
} from "@/content/case-studies";
import { buildPublicRouteMetadata } from "@/lib/seo";
import { buildFutureCaseStudyStructuredData } from "@/lib/structured-data";

afterEach(cleanup);

const syntheticContent: CaseStudyPageContent = {
  metadataTitle: "Synthetic school kitchen case",
  metadataDescription: "Synthetic content used only for component testing.",
  breadcrumbLabel: "Synthetic case",
  eyebrow: "Synthetic test fixture · not a customer project",
  title: "Synthetic institutional kitchen project",
  summary:
    "This test-only fixture verifies the case-study template and is not published.",
  projectType: "Synthetic test project",
  location: "Synthetic location",
  industry: "Education",
  projectRequirements: ["Test requirement one", "Test requirement two"],
  scopeOfWork: [
    { title: "Test scope", description: "Test-only scope description." },
  ],
  kitchenAreas: [
    { title: "Test area", description: "Test-only area description." },
  ],
  deliveryApproach: [
    {
      title: "Test approach",
      description: "Test-only delivery description.",
    },
  ],
  approvedProjectFacts: [
    { label: "Fixture status", value: "Synthetic and non-public" },
  ],
  images: [
    {
      src: "/sari-arta-social-card.png",
      alt: "Synthetic case-study gallery test image",
      width: 1730,
      height: 909,
      caption: "Synthetic test image",
    },
  ],
  relatedSolution: {
    label: "School canteen solution",
    href: "/solutions/school-canteen-kitchen",
  },
  relatedIndustry: {
    label: "Schools industry",
    href: "/industries/schools",
  },
};

test("renders the reusable case-study hierarchy, gallery, links, and consultation actions", () => {
  render(<CaseStudyPage content={syntheticContent} locale="en" />);

  expect(
    screen.getByRole("heading", {
      level: 1,
      name: "Synthetic institutional kitchen project",
    }),
  ).toBeDefined();
  for (const heading of [
    "Project requirements",
    "Scope of work",
    "Kitchen areas",
    "Solution and delivery approach",
    "Approved project facts",
    "Project gallery",
  ]) {
    expect(
      screen.getByRole("heading", { level: 2, name: heading }),
    ).toBeDefined();
  }
  expect(
    screen.getByRole("img", {
      name: "Synthetic case-study gallery test image",
    }),
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

test("keeps synthetic, unapproved, private, and incomplete cases out of the sitemap", () => {
  const base: CaseStudyRecord = {
    slug: "synthetic-case",
    status: "published",
    isPublic: true,
    publishedAt: "2026-08-23",
    publicationApproval: {
      versionId: "synthetic-version",
      approvedAt: "2026-08-23",
      contentChecksum: "synthetic-checksum",
      factsApproved: true,
      imagesApproved: true,
      publicUseApproved: true,
    },
    content: { en: syntheticContent, "zh-CN": syntheticContent },
  };

  expect(
    buildCaseStudySitemapRoutes([
      { ...base, status: "draft" },
      { ...base, isPublic: false },
      { ...base, publicationApproval: undefined },
      { ...base, content: { en: syntheticContent } },
    ]),
  ).toEqual([]);

  expect(buildCaseStudySitemapRoutes([base])).toEqual([
    expect.objectContaining({
      path: "/projects/synthetic-case",
      status: "published",
      isPublic: true,
    }),
  ]);
});

test("builds page-specific Open Graph and cited case-study image data", () => {
  const image = syntheticContent.images[0]!;
  const metadata = buildPublicRouteMetadata(
    {
      title: syntheticContent.metadataTitle,
      description: syntheticContent.metadataDescription,
      path: "/projects/synthetic-case",
      image: {
        url: image.src,
        width: image.width,
        height: image.height,
        alt: image.alt,
      },
    },
    "en",
  );
  const structuredData = buildFutureCaseStudyStructuredData({
    headline: syntheticContent.metadataTitle,
    description: syntheticContent.metadataDescription,
    path: "/projects/synthetic-case",
    datePublished: "2026-08-23",
    language: "en",
    industry: syntheticContent.industry,
    images: [image.src],
  });

  expect(metadata.openGraph).toEqual(
    expect.objectContaining({
      images: [
        {
          url: image.src,
          width: image.width,
          height: image.height,
          alt: image.alt,
        },
      ],
    }),
  );
  expect(structuredData).toEqual(
    expect.objectContaining({
      articleSection: ["Case Study", "Education"],
      image: [expect.stringMatching(/\/sari-arta-social-card\.png$/)],
    }),
  );
});
