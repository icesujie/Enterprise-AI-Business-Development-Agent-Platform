import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import MarketingContentDetailPage from "@/app/(workspace)/marketing-content/[id]/page";
import MarketingAcceptancePage from "@/app/(workspace)/marketing-content/acceptance/page";
import NewMarketingContentPage from "@/app/(workspace)/marketing-content/new/page";
import MarketingContentPage from "@/app/(workspace)/marketing-content/page";
import { MarketingChannelPreview } from "@/components/marketing/marketing-channel-preview";
import type {
  CurrentIdentity,
  MarketingAcceptanceDashboard,
  MarketingContentAsset,
  MarketingContentEvaluation,
  MarketingContentVersion,
} from "@/lib/api";

const { apiFetchMock, createSuccessorMock, identityState, assetState } =
  vi.hoisted(() => ({
    apiFetchMock: vi.fn(),
    createSuccessorMock: vi.fn(),
    identityState: { value: "sales" as "sales" | "admin" },
    assetState: {
      value: "draft" as "draft" | "review" | "approved" | "archived",
    },
  }));

vi.mock("@/i18n/server", () => ({
  getLocale: vi.fn(async () => "en"),
}));

vi.mock("@/lib/api", () => ({ apiFetch: apiFetchMock }));

vi.mock("@/app/(workspace)/marketing-content/actions", () => ({
  createManualContent: vi.fn(async () => ({
    status: "success",
    message: "Created",
  })),
  createAndGenerateContent: vi.fn(async () => ({
    status: "success",
    message: "Queued",
  })),
  prepareMarketingAcceptanceSet: vi.fn(async () => ({
    status: "success",
    message: "Prepared",
  })),
  createContentSuccessor: createSuccessorMock,
  submitContentReview: vi.fn(async () => ({
    status: "success",
    message: "Submitted",
  })),
  decideContentReview: vi.fn(async () => ({
    status: "success",
    message: "Decided",
  })),
  archiveContent: vi.fn(async () => ({
    status: "success",
    message: "Archived",
  })),
  restoreContent: vi.fn(async () => ({
    status: "success",
    message: "Restored",
  })),
  rollbackContentVersion: vi.fn(async () => ({
    status: "success",
    message: "Rolled back",
  })),
  submitContentFeedback: vi.fn(async () => ({
    status: "success",
    message: "Feedback recorded",
  })),
}));

beforeEach(() => {
  identityState.value = "sales";
  assetState.value = "draft";
  createSuccessorMock.mockReset();
  createSuccessorMock.mockResolvedValue({
    status: "error",
    code: "stale",
    message: "Content has changed since you opened it. Refresh before saving.",
  });
  apiFetchMock.mockImplementation(async (path: string) => fixture(path));
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

test("renders the governed content list and current/approved pointers", async () => {
  render(
    await MarketingContentPage({
      params: Promise.resolve({}),
      searchParams: Promise.resolve({ view: "draft" }),
    }),
  );
  expect(
    screen.getByRole("heading", { name: "Marketing Content" }),
  ).toBeDefined();
  expect(
    screen.getByRole("link", { name: "Synthetic School Article" }),
  ).toBeDefined();
  expect(screen.getByText("v3 · Draft")).toBeDefined();
  expect(screen.getAllByText("v2 · Approved").length).toBeGreaterThan(0);
  expect(
    screen.getByText(/No publishing or external sending is available/i),
  ).toBeDefined();
});

test("renders five governed AI content types and preserves manual fallback", async () => {
  render(await NewMarketingContentPage());
  expect(
    screen.getByRole("heading", { name: "Create a governed marketing draft" }),
  ).toBeDefined();
  const contentTypes = screen.getAllByLabelText("Content type");
  expect(contentTypes[0].querySelectorAll("option")).toHaveLength(5);
  expect(
    screen.getByRole("button", { name: "Generate AI draft" }),
  ).toBeDefined();
  expect(
    screen.getByRole("button", { name: "Create manual draft" }),
  ).toBeDefined();
  expect(screen.getByText(/No AI is called/i)).toBeDefined();
});

test("renders the fixed bilingual business acceptance dashboard", async () => {
  identityState.value = "admin";
  render(await MarketingAcceptancePage());
  expect(
    screen.getByRole("heading", {
      name: "Marketing Content Agent final acceptance",
    }),
  ).toBeDefined();
  expect(screen.getAllByText("10", { selector: "strong" }).length).toBeGreaterThan(0);
  expect(screen.getAllByText("Pending").length).toBeGreaterThan(0);
  expect(
    screen.getByText("Indonesia school central kitchen project"),
  ).toBeDefined();
  expect(screen.getByText("印度尼西亚学校中央厨房项目")).toBeDefined();
  expect(
    screen.getByRole("button", { name: "Prepare 10 acceptance drafts" }),
  ).toBeDefined();
});

test("shows Sales edit and submit controls but hides approval actions", async () => {
  render(await detailPage());
  expect(
    screen.getByRole("heading", { name: "Version history" }),
  ).toBeDefined();
  expect(
    screen.getByRole("button", { name: "Save as new version" }),
  ).toBeDefined();
  expect(
    screen.getByRole("button", { name: "Submit for review" }),
  ).toBeDefined();
  expect(screen.queryByRole("button", { name: /Approve v/ })).toBeNull();
  expect(
    screen.queryByRole("heading", { name: "Governance audit" }),
  ).toBeNull();
});

test("shows Admin approve and reject controls for independently created review content", async () => {
  identityState.value = "admin";
  assetState.value = "review";
  render(await detailPage());
  expect(screen.getByRole("button", { name: "Approve v3" })).toBeDefined();
  expect(
    screen.getByRole("button", { name: "Reject and return to draft" }),
  ).toBeDefined();
  expect(
    screen.getByRole("heading", { name: "Approval history" }),
  ).toBeDefined();
  expect(
    screen.getByRole("heading", { name: "Governance audit" }),
  ).toBeDefined();
  expect(
    screen.getByRole("heading", { name: "Human quality feedback" }),
  ).toBeDefined();
  expect(screen.getByText("91/100")).toBeDefined();
});

test.each([
  ["website_article", "Website article"],
  ["tiktok_script", "Short-form video script"],
  ["instagram_reel_script", "Short-form video script"],
  ["facebook_post", "Facebook"],
  ["email_draft", "Subject"],
])("renders a channel-specific %s preview", (contentType, marker) => {
  render(
    <MarketingChannelPreview
      contentType={contentType}
      version={previewVersion(contentType)}
      zh={false}
    />,
  );
  expect(screen.getByText(marker)).toBeDefined();
});

test("shows restore for archived content and no edit form", async () => {
  identityState.value = "admin";
  assetState.value = "archived";
  render(await detailPage());
  expect(
    screen.getByRole("button", { name: "Restore as draft" }),
  ).toBeDefined();
  expect(
    screen.queryByRole("button", { name: "Save as new version" }),
  ).toBeNull();
});

test("shows a clear 412 stale edit message", async () => {
  render(await detailPage());
  fireEvent.submit(
    screen
      .getByRole("button", { name: "Save as new version" })
      .closest("form")!,
  );
  await waitFor(() =>
    expect(screen.getByRole("alert").textContent).toContain(
      "Content has changed since you opened it. Refresh before saving.",
    ),
  );
});

async function detailPage() {
  return MarketingContentDetailPage({
    params: Promise.resolve({ id: "asset-1" }),
    searchParams: Promise.resolve({}),
  });
}

function fixture(path: string): unknown {
  if (path === "/api/v1/me") return identity();
  if (path === "/api/v1/content/acceptance") return acceptanceDashboard();
  if (path.includes("/versions")) return versions();
  if (path.includes("/decisions")) return [];
  if (path.includes("/audit")) return [];
  if (path.includes("/evaluation")) return evaluation();
  if (path === "/api/v1/content/assets/asset-1") return asset();
  if (path.startsWith("/api/v1/content/assets?")) return [asset("draft")];
  if (path.startsWith("/api/v1/content/requests?")) return [];
  throw new Error(`Unexpected content API path: ${path}`);
}

function identity(): CurrentIdentity {
  const admin = identityState.value === "admin";
  return {
    user_id: admin ? "admin-user" : "sales-user",
    email: admin ? "admin@example.invalid" : "sales@example.invalid",
    display_name: admin ? "Synthetic Admin" : "Synthetic Sales",
    workspace: { id: "tenant-1", slug: "synthetic", name: "Synthetic" },
    membership_id: admin ? "admin-membership" : "sales-membership",
    role: admin ? "admin" : "sales",
    permissions: admin
      ? [
          "content:read",
          "content:generate",
          "content:edit",
          "content:submit_review",
          "content:approve",
          "content:archive",
          "content:audit_read",
          "content:review",
        ]
      : ["content:read", "content:edit", "content:submit_review"],
  };
}

function evaluation(): MarketingContentEvaluation {
  return {
    asset_id: "asset-1",
    evaluated_version_id: "version-3",
    generation_run_id: "generation-1",
    generation_outcome: "generated",
    evidence_status: "sufficient",
    provider: "mock",
    model: "grounded-marketing-v1",
    quality_evaluation: {
      brand_fit: 90,
      audience_fit: 90,
      channel_fit: 95,
      clarity: 80,
      cta_quality: 95,
      factual_grounding: 100,
      unsupported_claims: 0,
      repetition: 75,
      content_usefulness: 91,
      overall_score: 91,
      issues: [],
    },
    human_edit_distance: 0.18,
    generated_version_id: "version-1",
    generated_version_number: 1,
    approved_human_version_id: "version-3",
    approved_human_version_number: 3,
    citations: [],
    latency_ms: 40,
    token_usage: {},
    estimated_cost: null,
    correlation_id: "correlation-1",
    feedback: [],
  };
}

function acceptanceDashboard(): MarketingAcceptanceDashboard {
  const caseBase = {
    content_type: "website_article",
    audience: "schools",
    channel: "website",
    business_objective: "Synthetic objective",
    topic: "Synthetic topic",
    call_to_action: "Request consultation",
    request_id: null,
    request_status: null,
    attempt_count: 0,
    asset_id: null,
    asset_status: null,
    reviewed: false,
    approved: false,
    rejected: false,
    human_edit_distance: null,
    generated_version_number: null,
    approved_human_version_number: null,
    feedback_categories: [],
    quality_evaluation: null,
  };
  const cases = Array.from({ length: 10 }, (_, index) => ({
    ...caseBase,
    case_id: `case-${index}`,
    scenario:
      index === 0
        ? "Indonesia school central kitchen project"
        : index === 1
          ? "印度尼西亚学校中央厨房项目"
          : `Synthetic case ${index + 1}`,
    language: index % 2 === 0 ? ("en" as const) : ("zh-CN" as const),
  }));
  return {
    dataset_version: "phase_3_2_business_acceptance_v1",
    configured_provider: "mock",
    mock_preparation_allowed: true,
    cases,
    summary: {
      total: 10,
      prepared: 0,
      reviewed: 0,
      approved: 0,
      rejected: 0,
      average_human_edit_distance: null,
      common_feedback_categories: {},
      quality_metric_summary: {},
      brand_guideline_validation: "pending",
      brand_guideline_note: "No approved real guideline.",
      openai_comparison_state: "not_run",
      openai_comparison_note: "Not run.",
    },
  };
}

function previewVersion(contentType: string): MarketingContentVersion {
  const base = versions()[0];
  const references = [{ chunk_id: "chunk-1" }];
  const scene = {
    visual: "Show workflow",
    voiceover: "Synthetic evidence",
    on_screen_text: "Project workflow",
  };
  const bodies: Record<string, Record<string, unknown>> = {
    website_article: {
      content_type: "website_article",
      title: "School kitchen planning",
      summary: "Synthetic summary",
      sections: [{ heading: "Planning", body: "Synthetic body" }],
      call_to_action: "Request consultation",
      references,
    },
    tiktok_script: {
      content_type: "tiktok_script",
      title: "Kitchen workflow",
      hook: "Start with requirements",
      scenes: [scene],
      call_to_action: "Request consultation",
      references,
    },
    instagram_reel_script: {
      content_type: "instagram_reel_script",
      title: "Kitchen workflow",
      hook: "Start with requirements",
      scenes: [scene],
      caption: "Synthetic caption",
      call_to_action: "Request consultation",
      references,
    },
    facebook_post: {
      content_type: "facebook_post",
      headline: "Kitchen planning",
      body: "Synthetic post body",
      call_to_action: "Request consultation",
      hashtags: ["#CommercialKitchen"],
      references,
    },
    email_draft: {
      content_type: "email_draft",
      subject: "Kitchen planning",
      preview_text: "Synthetic preview",
      greeting: "Hello,",
      body_sections: ["Synthetic body"],
      call_to_action: "Request consultation",
      closing: "Sari Arta",
      references,
    },
  };
  return {
    ...base,
    content_body: bodies[contentType],
    citations: [
      {
        chunk_id: "chunk-1",
        document_name: "Synthetic source",
        document_version: 1,
      },
    ],
  };
}

function versions(): MarketingContentVersion[] {
  return [3, 2, 1].map((number) => ({
    id: `version-${number}`,
    tenant_id: "tenant-1",
    content_asset_id: "asset-1",
    version_number: number,
    origin: "human",
    content_body: { body: `Synthetic content v${number}` },
    plain_text: `Synthetic content v${number}`,
    claims: [],
    citations: [],
    generation_run_id: null,
    based_on_version_id: number > 1 ? `version-${number - 1}` : null,
    content_sha256: String(number).repeat(64),
    created_by: "sales-membership",
    created_at: `2026-08-1${number}T02:00:00Z`,
  }));
}

function asset(status = assetState.value): MarketingContentAsset {
  const allVersions = versions();
  const current = allVersions[0];
  const approved = allVersions[1];
  return {
    id: "asset-1",
    tenant_id: "tenant-1",
    domain_id: "domain-1",
    agent_id: null,
    request_id: "request-1",
    title: "Synthetic School Article",
    content_type: "website_article",
    audience: "schools",
    language: "en",
    channel: "website",
    status,
    owner_membership_id: "sales-membership",
    creator_membership_id: "sales-membership",
    current_version_id: current.id,
    approved_version_id: approved.id,
    record_version: 7,
    archived_at: status === "archived" ? "2026-08-16T03:00:00Z" : null,
    archived_by: status === "archived" ? "admin-membership" : null,
    archive_reason: status === "archived" ? "Synthetic archive" : null,
    created_at: "2026-08-10T02:00:00Z",
    updated_at: "2026-08-16T02:00:00Z",
    current_version: current,
    approved_version: approved,
  };
}
