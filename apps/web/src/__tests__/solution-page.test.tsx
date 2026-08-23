import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { PublicConsultationCta } from "@/components/marketing/public-consultation-cta";
import { PublicConsultationWidget } from "@/components/marketing/public-consultation-widget";
import { SolutionPage } from "@/components/marketing/solution-page";
import { schoolCanteenSolution } from "@/content/solution-pages";

vi.mock("@/app/(marketing)/public-consultation-actions", () => ({
  processConsultationTurn: vi.fn(),
  createConsultationLead: vi.fn(),
}));

afterEach(cleanup);

test("renders the reusable school canteen solution hierarchy", () => {
  render(<SolutionPage content={schoolCanteenSolution.en} />);

  expect(
    screen.getByRole("heading", {
      level: 1,
      name: "School canteen kitchens planned around the daily meal service.",
    }),
  ).toBeDefined();
  expect(
    screen.getByRole("heading", {
      level: 2,
      name: "One delivery framework from early planning to handover.",
    }),
  ).toBeDefined();
  expect(screen.getByText("Meal service rhythm")).toBeDefined();
  expect(screen.getByText("Local installation and handover")).toBeDefined();
});

test("opens the existing Public Consultation Agent from the solution CTA", () => {
  render(
    <>
      <PublicConsultationCta label="Start project consultation" />
      <PublicConsultationWidget initialLanguage="en" />
    </>,
  );

  fireEvent.click(
    screen.getByRole("button", { name: "Start project consultation" }),
  );
  expect(
    screen.getByRole("dialog", {
      name: "Commercial Kitchen Consultation Agent",
    }),
  ).toBeDefined();
});
