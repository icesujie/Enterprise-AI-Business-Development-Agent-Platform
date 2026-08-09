import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import HomePage from "@/app/(marketing)/page";
import WorkspaceLayout from "@/app/(workspace)/layout";
import DashboardPage from "@/app/(workspace)/dashboard/page";
import LoginPage from "@/app/login/page";

vi.mock("next/navigation", () => ({ usePathname: () => "/dashboard" }));

afterEach(cleanup);

test("renders the public engineering positioning and consultation action", () => {
  render(<HomePage />);
  expect(
    screen.getByRole("heading", {
      name: "Commercial kitchens engineered for real operating demands.",
    }),
  ).toBeDefined();
  expect(
    screen.getAllByRole("link", { name: "Request kitchen consultation" }),
  ).toHaveLength(2);
});

test("renders the M6 workspace navigation and dashboard", () => {
  render(
    <WorkspaceLayout>
      <DashboardPage />
    </WorkspaceLayout>,
  );
  expect(screen.getAllByRole("link", { name: "Dashboard" })).toHaveLength(2);
  expect(screen.getAllByRole("link", { name: "Leads" })).toHaveLength(2);
  expect(screen.getAllByRole("link", { name: "Opportunities" })).toHaveLength(
    2,
  );
  expect(screen.getAllByRole("link", { name: "Follow-up" })).toHaveLength(2);
  expect(screen.getByRole("heading", { name: "Good morning." })).toBeDefined();
});

test("renders the production sign-in form", () => {
  render(<LoginPage />);
  expect(
    screen.getByRole("heading", { name: "Sales workspace" }),
  ).toBeDefined();
  expect(screen.getByLabelText("Email")).toBeDefined();
  expect(screen.getByLabelText("Password")).toBeDefined();
});
