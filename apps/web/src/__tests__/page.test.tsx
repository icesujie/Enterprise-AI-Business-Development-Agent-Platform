import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import WorkspaceLayout from "@/app/(workspace)/layout";
import LoginPage from "@/app/login/page";

test("renders the M4 workspace navigation", () => {
  render(
    <WorkspaceLayout>
      <p>Workspace content</p>
    </WorkspaceLayout>,
  );
  expect(screen.getByText("M4 AI workbench")).toBeDefined();
  expect(screen.getByRole("link", { name: "Leads" })).toBeDefined();
  expect(screen.getByRole("link", { name: "Companies" })).toBeDefined();
  expect(screen.getByRole("link", { name: "Contacts" })).toBeDefined();
  expect(screen.getByRole("link", { name: "Tasks" })).toBeDefined();
});

test("renders the production sign-in form", () => {
  render(<LoginPage />);
  expect(
    screen.getByRole("heading", { name: "Sales workspace" }),
  ).toBeDefined();
  expect(screen.getByLabelText("Email")).toBeDefined();
  expect(screen.getByLabelText("Password")).toBeDefined();
});
