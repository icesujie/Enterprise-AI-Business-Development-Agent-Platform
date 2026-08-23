import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";

import { IndustryPage } from "@/components/marketing/industry-page";
import { schoolsIndustry } from "@/content/industry-pages";
import { buildPublicRouteMetadata } from "@/lib/seo";

afterEach(cleanup);

test("renders the reusable schools industry hierarchy and solution link", () => {
  render(<IndustryPage content={schoolsIndustry.en} />);

  expect(
    screen.getByRole("heading", {
      level: 1,
      name: "School kitchens shaped around meals, movement, and daily routines.",
    }),
  ).toBeDefined();
  expect(
    screen.getByRole("heading", {
      level: 2,
      name: "Support for new school kitchens and canteen renovation.",
    }),
  ).toBeDefined();
  expect(screen.getByText("Institutional meal preparation")).toBeDefined();
  expect(screen.getByText("Return, washing, and cleaning")).toBeDefined();
  expect(
    screen
      .getByRole("link", {
        name: "Explore school canteen kitchen solutions",
      })
      .getAttribute("href"),
  ).toBe("/solutions/school-canteen-kitchen");
  expect(
    screen.getAllByRole("button", { name: "Start project consultation" }),
  ).toHaveLength(2);
});

test("builds canonical and Open Graph metadata for the schools page", () => {
  const content = schoolsIndustry.en;
  const metadata = buildPublicRouteMetadata(
    {
      title: content.metadataTitle,
      description: content.metadataDescription,
      path: content.path,
    },
    "en",
  );

  expect(metadata.alternates).toEqual({
    canonical: expect.stringMatching(/\/industries\/schools$/),
  });
  expect(metadata.openGraph).toEqual(
    expect.objectContaining({
      url: expect.stringMatching(/\/industries\/schools$/),
      locale: "en_US",
    }),
  );
});
