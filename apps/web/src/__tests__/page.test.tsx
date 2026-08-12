import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import HomePage from "@/app/(marketing)/page";
import WorkspaceLayout from "@/app/(workspace)/layout";
import DashboardPage from "@/app/(workspace)/dashboard/page";
import ContactsPage from "@/app/(workspace)/contacts/page";
import OrganizationsPage from "@/app/(workspace)/organizations/page";
import LoginPage from "@/app/login/page";
import { QualificationCard } from "@/components/workspace/qualification-card";
import { LanguageSwitcher } from "@/components/i18n/language-switcher";
import { I18nProvider } from "@/i18n/context";
import {
  createDemoSessionToken,
  verifyDemoCredentials,
  verifyDemoSessionToken,
} from "@/lib/demo-auth";

const { refreshMock, setLanguageMock } = vi.hoisted(() => ({
  refreshMock: vi.fn(),
  setLanguageMock: vi.fn(async () => undefined),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
  useRouter: () => ({ refresh: refreshMock }),
}));
vi.mock("@/app/language-actions", () => ({
  setLanguage: setLanguageMock,
}));
vi.mock("@/i18n/server", async () => {
  const { messagesFor } = await import("@/i18n/messages");
  return {
    getLocale: vi.fn(async () => "en"),
    getMessages: vi.fn(async () => messagesFor("en")),
  };
});
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
    if (path.startsWith("/api/v1/contacts")) {
      return [
        {
          id: "contact-1",
          organization_id: "org-1",
          first_name: "Dewi",
          last_name: "Santoso",
          email: "dewi@example.invalid",
          phone_e164: "+6281234567890",
          whatsapp_e164: null,
          job_title: "Facility Manager",
          preferred_language: "en",
          marketing_consent_status: "unknown",
          do_not_contact: false,
          version: 1,
        },
      ];
    }
    if (path.startsWith("/api/v1/organizations")) {
      return [
        {
          id: "org-1",
          legal_name: "Synthetic School Group Ltd",
          display_name: "Synthetic School Group",
          website_url: "https://school.example.invalid",
          domain: "school.example.invalid",
          industry: "Education",
          country_code: "ID",
          city: "Jakarta",
          preferred_language: "en",
          lifecycle_stage: "prospect",
          contact_count: 1,
          version: 1,
        },
      ];
    }
    throw new Error(`Unexpected API path: ${path}`);
  }),
}));

afterEach(cleanup);

test("switches from Chinese back to English and refreshes server content", async () => {
  render(
    <I18nProvider locale="zh-CN">
      <LanguageSwitcher />
    </I18nProvider>,
  );

  const selector = screen.getByRole("combobox", { name: "语言" });
  expect((selector as HTMLSelectElement).value).toBe("zh-CN");
  fireEvent.change(selector, { target: { value: "en" } });

  await waitFor(() => expect(setLanguageMock).toHaveBeenCalledWith("en"));
  await waitFor(() => expect(refreshMock).toHaveBeenCalled());
  expect((selector as HTMLSelectElement).value).toBe("en");
});

test("uses a readable light theme for the workspace language selector", () => {
  render(
    <I18nProvider locale="en">
      <LanguageSwitcher compact />
    </I18nProvider>,
  );

  const selector = screen.getByRole("combobox", { name: "Language" });
  expect(selector.className).toContain("text-[var(--color-ink)]");
  expect(selector.className).toContain("bg-[var(--color-surface-subtle)]");
  expect(selector.className).not.toContain("text-white");
});

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
  render(await WorkspaceLayout({ children: dashboard }));
  expect(screen.getAllByRole("link", { name: "Dashboard" })).toHaveLength(2);
  expect(screen.getAllByRole("link", { name: "Leads" })).toHaveLength(2);
  expect(screen.getAllByRole("link", { name: "Opportunities" })).toHaveLength(
    2,
  );
  expect(screen.getAllByRole("link", { name: "Follow-up" })).toHaveLength(2);
  expect(screen.getAllByRole("link", { name: "Knowledge" })).toHaveLength(2);
  expect(
    screen.getByRole("heading", { name: "Sales command centre" }),
  ).toBeDefined();
  expect(screen.getByText("School kitchen · Jakarta")).toBeDefined();
});

test("renders the production sign-in form", async () => {
  render(await LoginPage({}));
  expect(
    screen.getByRole("heading", { name: "Sales workspace" }),
  ).toBeDefined();
  expect(screen.getByLabelText("Email")).toBeDefined();
  expect(screen.getByLabelText("Password")).toBeDefined();
});

test("shows edit controls for companies and contacts", async () => {
  render(
    await OrganizationsPage({
      params: Promise.resolve({}),
      searchParams: Promise.resolve({}),
    }),
  );
  expect(screen.getByRole("link", { name: "Edit" })).toBeDefined();
  cleanup();

  render(
    await ContactsPage({
      params: Promise.resolve({}),
      searchParams: Promise.resolve({}),
    }),
  );
  expect(screen.getByRole("link", { name: "Edit" })).toBeDefined();
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
        qualification_level: "A",
        tier: "hot",
        need_summary: "A defined institutional kitchen requirement.",
        business_summary: "A defined institutional kitchen requirement.",
        qualification: {
          need_status: "confirmed",
          timeline_status: "confirmed",
          budget_status: "unknown",
          authority_status: "partial",
        },
        key_qualification_factors: [
          { key: "need", label: "Need and project fit", status: "confirmed" },
        ],
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
  expect(screen.getByText("Level A")).toBeDefined();
  expect(screen.queryByText(/chain-of-thought/i)).toBeNull();
});

test("validates the development-only demo login and signed session", async () => {
  const previous = {
    environment: process.env.APP_ENVIRONMENT,
    email: process.env.DEMO_AUTH_EMAIL,
    password: process.env.DEMO_AUTH_PASSWORD,
    secret: process.env.DEMO_AUTH_SECRET,
  };
  process.env.APP_ENVIRONMENT = "development";
  process.env.DEMO_AUTH_EMAIL = "admin@sariarta.local";
  process.env.DEMO_AUTH_PASSWORD = "SariArtaDemo2026!";
  process.env.DEMO_AUTH_SECRET =
    "unit-test-demo-session-secret-with-at-least-32-characters";
  try {
    expect(
      await verifyDemoCredentials("admin@sariarta.local", "SariArtaDemo2026!"),
    ).toBe(true);
    expect(
      await verifyDemoCredentials("admin@sariarta.local", "wrong-password"),
    ).toBe(false);
    const token = await createDemoSessionToken();
    expect(await verifyDemoSessionToken(token)).toBe(true);
    expect(await verifyDemoSessionToken(`${token}tampered`)).toBe(false);
  } finally {
    restoreEnvironment("APP_ENVIRONMENT", previous.environment);
    restoreEnvironment("DEMO_AUTH_EMAIL", previous.email);
    restoreEnvironment("DEMO_AUTH_PASSWORD", previous.password);
    restoreEnvironment("DEMO_AUTH_SECRET", previous.secret);
  }
});

function restoreEnvironment(name: string, value: string | undefined) {
  if (value === undefined) delete process.env[name];
  else process.env[name] = value;
}
