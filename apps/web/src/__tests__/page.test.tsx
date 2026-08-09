import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import HomePage from "@/app/(marketing)/page";
import WorkspaceLayout from "@/app/(workspace)/layout";
import DashboardPage from "@/app/(workspace)/dashboard/page";
import LoginPage from "@/app/login/page";
import { QualificationCard } from "@/components/workspace/qualification-card";

vi.mock("next/navigation", () => ({ usePathname: () => "/dashboard" }));
vi.mock("@/lib/api", () => ({
  apiFetch: vi.fn(async (path: string) => {
    if (path.startsWith("/api/v1/leads")) {
      return {
        items: [
          {
            id: "lead-1",
            organization_id: "org-1",
            contact_id: null,
            source_channel: "website",
            source_detail: null,
            inquiry_summary: "School kitchen for 800 meals per day.",
            status: "new",
            priority: "high",
            owner_membership_id: null,
            estimated_value: null,
            currency: null,
            target_timeline: "Q2 2027",
            project_country_code: "ID",
            project_city: "Jakarta",
            project_type: "School kitchen",
            expected_capacity: "800 meals/day",
            requirements: {},
            qualification_score: null,
            created_at: "2026-08-09T03:00:00Z",
            updated_at: "2026-08-09T03:00:00Z",
            version: 1,
          },
        ],
        next_cursor: null,
      };
    }
    if (path.startsWith("/api/v1/opportunities")) {
      return { items: [], next_cursor: null };
    }
    if (path.startsWith("/api/v1/tasks")) return [];
    if (path.startsWith("/api/v1/organizations")) {
      return [{ id: "org-1", display_name: "Synthetic School Group" }];
    }
    throw new Error(`Unexpected API path: ${path}`);
  }),
}));

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

test("renders the M6 workspace navigation and live dashboard", async () => {
  const dashboard = await DashboardPage();
  render(<WorkspaceLayout>{dashboard}</WorkspaceLayout>);
  expect(screen.getAllByRole("link", { name: "Dashboard" })).toHaveLength(2);
  expect(screen.getAllByRole("link", { name: "Leads" })).toHaveLength(2);
  expect(screen.getAllByRole("link", { name: "Opportunities" })).toHaveLength(
    2,
  );
  expect(screen.getAllByRole("link", { name: "Follow-up" })).toHaveLength(2);
  expect(
    screen.getByRole("heading", { name: "Sales command centre" }),
  ).toBeDefined();
  expect(screen.getByText("School kitchen · Jakarta")).toBeDefined();
});

test("renders the production sign-in form", () => {
  render(<LoginPage />);
  expect(
    screen.getByRole("heading", { name: "Sales workspace" }),
  ).toBeDefined();
  expect(screen.getByLabelText("Email")).toBeDefined();
  expect(screen.getByLabelText("Password")).toBeDefined();
});

test("renders structured AI qualification without hidden reasoning", () => {
  render(
    <QualificationCard
      lead={{
        id: "lead-ai",
        organization_id: null,
        contact_id: null,
        source_channel: "website",
        source_detail: null,
        inquiry_summary: "Synthetic hospital kitchen inquiry.",
        status: "qualifying",
        priority: "high",
        owner_membership_id: null,
        estimated_value: null,
        currency: null,
        target_timeline: "Q2 2027",
        project_country_code: "ID",
        project_city: "Jakarta",
        project_type: "Hospital kitchen",
        expected_capacity: "1,000 meals/day",
        requirements: {},
        qualification_score: null,
        created_at: "2026-08-09T03:00:00Z",
        updated_at: "2026-08-09T03:00:00Z",
        version: 1,
      }}
      assessment={{
        id: "assessment-1",
        lead_id: "lead-ai",
        assessment_version: 1,
        agent_run_id: "run-1",
        score: "82.00",
        tier: "hot",
        need_summary: "A defined institutional kitchen requirement.",
        qualification: {
          need_status: "confirmed",
          timeline_status: "confirmed",
          budget_status: "unknown",
          authority_status: "partial",
        },
        recommended_action: "Schedule discovery and request the floor plan.",
        missing_information: ["Approved budget"],
        confidence: "0.8200",
        review_status: "pending",
        reviewed_by: null,
        reviewed_at: null,
        created_at: "2026-08-09T03:05:00Z",
      }}
      history={[]}
      runAction={async () => {}}
      approveAction={async () => {}}
      rejectAction={async () => {}}
    />,
  );
  expect(
    screen.getByText("AI-generated assessment · Human review required"),
  ).toBeDefined();
  expect(
    screen.getByText("Schedule discovery and request the floor plan."),
  ).toBeDefined();
  expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe(
    "82",
  );
  expect(screen.queryByText(/chain-of-thought/i)).toBeNull();
});
