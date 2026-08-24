import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import {
  buildPublishedPublicMetadata,
  PublishedPublicRoute,
} from "@/components/marketing/published-public-route";
import { resolvePublishedPublicPage } from "@/content/published-public-pages";
import type { PublishedCmsPage } from "@/lib/public-content";

const { getPublishedCmsPageMock } = vi.hoisted(() => ({
  getPublishedCmsPageMock: vi.fn(),
}));

vi.mock("@/lib/public-content", () => ({
  getPublishedCmsPage: getPublishedCmsPageMock,
}));
vi.mock("next/navigation", () => ({
  notFound: vi.fn(() => {
    throw new Error("NEXT_NOT_FOUND");
  }),
}));

beforeEach(() => getPublishedCmsPageMock.mockReset());
afterEach(cleanup);

test("published CMS content takes precedence and provides public metadata", async () => {
  getPublishedCmsPageMock.mockResolvedValue(solutionFixture());

  const resolved = await resolvePublishedPublicPage(
    "solution",
    "school-canteen-kitchen",
    "en",
  );
  expect(resolved).toEqual(
    expect.objectContaining({ source: "cms", pageType: "solution" }),
  );
  expect(resolved?.content.metadataTitle).toBe("Published CMS SEO title");

  const metadata = await buildPublishedPublicMetadata(
    "solution",
    "school-canteen-kitchen",
    "en",
  );
  expect(metadata.title).toBe("Published CMS SEO title");
  expect(metadata.alternates).toEqual({
    canonical: expect.stringMatching(/\/solutions\/school-canteen-kitchen$/),
  });
  expect(getPublishedCmsPageMock).toHaveBeenCalledWith(
    "solution",
    "school-canteen-kitchen",
    "en",
  );
});

test("renders structured CMS content with the consultation action", async () => {
  getPublishedCmsPageMock.mockResolvedValue(solutionFixture());
  render(
    await PublishedPublicRoute({
      pageType: "solution",
      slug: "school-canteen-kitchen",
      locale: "en",
    }),
  );

  expect(
    screen.getByRole("heading", { level: 1, name: "Published CMS solution" }),
  ).toBeDefined();
  expect(screen.getByText("Published workflow description.")).toBeDefined();
  expect(
    screen.getAllByRole("button", { name: "Start project consultation" })
      .length,
  ).toBeGreaterThan(0);
});

test("keeps the approved static school solution as isolated migration fallback", async () => {
  getPublishedCmsPageMock.mockResolvedValue(null);
  const resolved = await resolvePublishedPublicPage(
    "solution",
    "school-canteen-kitchen",
    "en",
  );

  expect(resolved).toEqual(
    expect.objectContaining({ source: "legacy", pageType: "solution" }),
  );
  render(
    await PublishedPublicRoute({
      pageType: "solution",
      slug: "school-canteen-kitchen",
      locale: "en",
    }),
  );
  expect(
    screen.getByRole("heading", {
      level: 1,
      name: /School canteen kitchens planned around the daily meal service/i,
    }),
  ).toBeDefined();
});

test("does not invent a fallback for an unknown or unpublished CMS slug", async () => {
  getPublishedCmsPageMock.mockResolvedValue(null);
  await expect(
    resolvePublishedPublicPage("guide", "unpublished-guide", "zh-CN"),
  ).resolves.toBeNull();
  expect(getPublishedCmsPageMock).toHaveBeenCalledWith(
    "guide",
    "unpublished-guide",
    "zh-CN",
  );
});

function solutionFixture(): PublishedCmsPage {
  return {
    page_type: "solution",
    slug: "school-canteen-kitchen",
    locale: "en",
    title: "Published CMS solution",
    summary: "Visible summary from the immutable published version.",
    seo_title: "Published CMS SEO title",
    seo_description: "Published CMS SEO description.",
    canonical_path: "/solutions/school-canteen-kitchen",
    structured_content: {
      overview: ["Published overview."],
      customer_needs: ["Visible customer need"],
      service_scope: [
        {
          title: "Published service",
          description: "Visible service description.",
        },
      ],
      workflow_areas: [
        {
          title: "Published workflow",
          description: "Published workflow description.",
        },
      ],
      related_industries: [],
      related_projects: [],
      cta: {
        label: "Start project consultation",
        description: "Share requirements for human review.",
        destination: "public_consultation_agent",
      },
    },
  };
}
