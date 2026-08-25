import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import PublicContentDetailPage from "@/app/(workspace)/public-content/[id]/page";
import NewPublicContentPage from "@/app/(workspace)/public-content/new/page";
import PublicContentPage from "@/app/(workspace)/public-content/page";
import type {
  CurrentIdentity,
  PublicContentItem,
  PublicContentVersion,
} from "@/lib/api";

const { apiFetchMock } = vi.hoisted(() => ({ apiFetchMock: vi.fn() }));

vi.mock("@/i18n/server", () => ({ getLocale: vi.fn(async () => "en") }));
vi.mock("@/lib/api", () => ({ apiFetch: apiFetchMock }));
vi.mock("@/app/(workspace)/public-content/actions", () => ({
  createPublicContent: vi.fn(),
  createPublicContentSuccessor: vi.fn(),
  submitPublicContentReview: vi.fn(),
  decidePublicContentReview: vi.fn(),
  publishPublicContent: vi.fn(),
  archivePublicContent: vi.fn(),
  retryPublicContentAutomation: vi.fn(),
}));

beforeEach(() => {
  apiFetchMock.mockImplementation(async (path: string) => fixture(path));
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

test("renders governed public content filters and publication pointers", async () => {
  render(
    await PublicContentPage({
      params: Promise.resolve({}),
      searchParams: Promise.resolve({ status: "published" }),
    }),
  );
  expect(screen.getByRole("heading", { name: "Public Content" })).toBeDefined();
  expect(
    screen.getByRole("link", { name: "School kitchen planning" }),
  ).toBeDefined();
  expect(screen.getByText("/solutions/school-kitchen-planning")).toBeDefined();
  expect(screen.getAllByText("published").length).toBeGreaterThan(0);
  expect(
    screen.getByLabelText("Locale").querySelectorAll("option"),
  ).toHaveLength(3);
});

test("creates only schema-controlled page types and visibly gates synthetic content", async () => {
  render(await NewPublicContentPage());
  const pageType = screen.getByLabelText("Page type");
  expect(pageType.querySelectorAll("option")).toHaveLength(5);
  fireEvent.change(pageType, { target: { value: "product" } });
  expect(screen.getByLabelText("SKU / model")).toBeDefined();
  expect(screen.getByLabelText("Price mode")).toBeDefined();
  expect(
    screen.getByText(/approved factual product information/i),
  ).toBeDefined();
  expect(screen.getByText("Media references (JSON)")).toBeDefined();
  expect(screen.getByText(/publishing is blocked/i)).toBeDefined();
});

test("shows exact current, approved and published versions with governance history", async () => {
  render(
    await PublicContentDetailPage({
      params: Promise.resolve({ id: "public-item-1" }),
      searchParams: Promise.resolve({}),
    }),
  );
  expect(screen.getByText("Current structured content")).toBeDefined();
  expect(screen.getAllByText("v2").length).toBeGreaterThan(0);
  expect(screen.getByText("Version history")).toBeDefined();
  expect(screen.getByText("Review history")).toBeDefined();
  expect(screen.getByText("Audit timeline")).toBeDefined();
});

function fixture(path: string): unknown {
  if (path === "/api/v1/me") return identity();
  if (path.includes("/versions")) return versions();
  if (path.includes("/decisions"))
    return [
      {
        id: "decision-1",
        public_content_item_id: "public-item-1",
        public_content_version_id: "version-2",
        decision_type: "approved",
        decided_by: "admin-1",
        content_sha256: "b".repeat(64),
        comment: "Approved fixture.",
        created_at: "2026-08-23T10:00:00Z",
      },
    ];
  if (path.includes("/audit"))
    return [
      {
        id: "audit-1",
        actor_membership_id: "admin-1",
        action: "public_content.published",
        public_content_item_id: "public-item-1",
        public_content_version_id: "version-2",
        before_metadata: {},
        after_metadata: {},
        details: {},
        correlation_id: "correlation-1",
        created_at: "2026-08-23T10:01:00Z",
      },
    ];
  if (path === "/api/v1/public-content/items/public-item-1") return item();
  if (path.startsWith("/api/v1/public-content/items?")) return [item()];
  throw new Error(`Unexpected public content API path: ${path}`);
}

function version(number: number): PublicContentVersion {
  return {
    id: `version-${number}`,
    tenant_id: "tenant-1",
    public_content_item_id: "public-item-1",
    version_number: number,
    origin: "human",
    title: "School kitchen planning",
    summary: "Synthetic internal CMS fixture.",
    seo_title: "School kitchen planning",
    seo_description: "Synthetic internal CMS fixture.",
    structured_content: { overview: ["Synthetic internal fixture"] },
    media_references: [],
    source_type: "manual",
    source_reference_id: null,
    source_structuring_run_id: null,
    source_candidate_key: null,
    source_filename: null,
    source_checksum: null,
    content_sha256: (number === 1 ? "a" : "b").repeat(64),
    based_on_version_id: number === 1 ? null : "version-1",
    created_by: "sales-1",
    created_at: `2026-08-${20 + number}T10:00:00Z`,
  };
}

function versions() {
  return [version(2), version(1)];
}

function item(): PublicContentItem {
  const current = version(2);
  return {
    id: "public-item-1",
    tenant_id: "tenant-1",
    page_type: "solution",
    slug: "school-kitchen-planning",
    locale: "en",
    title: current.title,
    summary: current.summary,
    seo_title: current.seo_title,
    seo_description: current.seo_description,
    canonical_path: "/solutions/school-kitchen-planning",
    status: "published",
    is_synthetic: false,
    current_version_id: current.id,
    approved_version_id: current.id,
    published_version_id: current.id,
    created_by: "sales-1",
    approved_by: "admin-1",
    published_by: "admin-1",
    record_version: 4,
    created_at: "2026-08-20T10:00:00Z",
    updated_at: "2026-08-23T10:00:00Z",
    published_at: "2026-08-23T10:00:00Z",
    archived_at: null,
    archived_by: null,
    archive_reason: null,
    current_version: current,
    approved_version: current,
    published_version: current,
  };
}

function identity(): CurrentIdentity {
  return {
    user_id: "admin-user",
    email: "admin@example.invalid",
    display_name: "Synthetic Admin",
    workspace: { id: "tenant-1", slug: "synthetic", name: "Synthetic" },
    membership_id: "admin-1",
    role: "admin",
    permissions: [
      "public_content:read",
      "public_content:edit",
      "public_content:submit_review",
      "public_content:review",
      "public_content:approve",
      "public_content:publish",
      "public_content:archive",
      "public_content:audit_read",
    ],
  };
}
