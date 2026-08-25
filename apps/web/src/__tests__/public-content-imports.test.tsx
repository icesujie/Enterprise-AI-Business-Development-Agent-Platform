import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import PublicContentImportDetailPage from "@/app/(workspace)/public-content/imports/[id]/page";
import PublicContentImportsPage from "@/app/(workspace)/public-content/imports/page";
import type {
  PublicContentImport,
  PublicContentStructuringRun,
} from "@/lib/api";

const { apiFetchMock } = vi.hoisted(() => ({ apiFetchMock: vi.fn() }));

vi.mock("@/i18n/server", () => ({ getLocale: vi.fn(async () => "en") }));
vi.mock("@/lib/api", () => ({ apiFetch: apiFetchMock }));
vi.mock("@/app/(workspace)/public-content/imports/actions", () => ({
  createPublicDraftFromImport: vi.fn(),
  importPublicContentDocument: vi.fn(),
  structurePublicContentImport: vi.fn(),
}));

beforeEach(() => {
  apiFetchMock.mockImplementation(async (path: string) => {
    if (path === "/api/v1/public-content/imports") return [fixture()];
    if (path === "/api/v1/public-content/imports/import-1") return fixture();
    if (path === "/api/v1/public-content/imports/import-1/structuring-runs")
      return [structuringRun()];
    throw new Error(`Unexpected path: ${path}`);
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

test("shows a bounded document upload and extraction history", async () => {
  render(await PublicContentImportsPage());
  expect(
    screen.getByRole("heading", { name: "Document Imports" }),
  ).toBeDefined();
  expect(
    screen.getByLabelText("Choose business document").getAttribute("accept"),
  ).toBe(".docx,.pdf,.html,.htm,.txt,.md");
  expect(screen.getByText("synthetic-brief.docx")).toBeDefined();
  expect(screen.getByText("3 blocks · 1 media")).toBeDefined();
});

test("shows structured preview and private media review link", async () => {
  render(
    await PublicContentImportDetailPage({
      params: Promise.resolve({ id: "import-1" }),
      searchParams: Promise.resolve({}),
    }),
  );
  expect(
    screen.getByRole("heading", { name: "Synthetic School Brief" }),
  ).toBeDefined();
  expect(screen.getByText("School canteen overview")).toBeDefined();
  expect(
    screen.getByText(/Every image requires separate Media Library review/),
  ).toBeDefined();
  expect(
    screen.getByRole("link", { name: "Review image 1" }).getAttribute("href"),
  ).toBe("/media/media-1");
  expect(
    screen.getByText(/does not generate or publish a webpage/),
  ).toBeDefined();
  expect(
    screen.getByRole("heading", { name: "Structure as Public Content" }),
  ).toBeDefined();
  expect(
    screen.getByRole("heading", { name: "Synthetic School Kitchen Solution" }),
  ).toBeDefined();
  expect(screen.getByText("requires_human_input")).toBeDefined();
  expect(
    screen.getByText(/Human input required:/).parentElement?.textContent,
  ).toContain("related_solution");
  expect(screen.getByText("case_study.source[0]")).toBeDefined();
  expect(
    screen.getByRole("button", { name: "Create private Draft" }),
  ).toBeDefined();
});

test("shows Product candidates, pricing review and separate human confirmation actions", async () => {
  apiFetchMock.mockImplementation(async (path: string) => {
    if (path === "/api/v1/public-content/imports/import-1") return fixture();
    if (path === "/api/v1/public-content/imports/import-1/structuring-runs")
      return [productStructuringRun()];
    throw new Error(`Unexpected path: ${path}`);
  });
  render(
    await PublicContentImportDetailPage({
      params: Promise.resolve({ id: "import-1" }),
      searchParams: Promise.resolve({}),
    }),
  );
  const pageType = screen.getByLabelText("Target page type");
  expect(pageType.querySelector('option[value="product"]')).not.toBeNull();
  expect(screen.getByText("Multiple products detected.")).toBeDefined();
  expect(screen.getAllByText("Synthetic Product A").length).toBeGreaterThan(1);
  expect(screen.getByText("Synthetic Product B")).toBeDefined();
  expect(screen.getAllByText("Pricing review").length).toBeGreaterThan(1);
  expect(
    screen.getAllByRole("button", { name: "Create private Draft" }),
  ).toHaveLength(2);
  expect(
    screen.getByText(/No batch Product pages will be created/),
  ).toBeDefined();
});

function structuringRun(): PublicContentStructuringRun {
  return {
    id: "run-1",
    tenant_id: "tenant-1",
    public_content_import_id: "import-1",
    requested_by: "sales-1",
    selected_page_type: "case_study",
    recommended_page_type: "industry",
    provider: "mock",
    model: "source-structuring-v1",
    locale: "en",
    status: "completed",
    outcome: "requires_human_input",
    result: {
      title: "Synthetic School Kitchen Solution",
      summary: "Plan preparation, cooking, washing and storage workflow.",
      seo_title: "Synthetic School Kitchen Solution",
      seo_description:
        "Plan preparation, cooking, washing and storage workflow.",
      cms_structured_content: {
        project_overview: [
          "Plan preparation, cooking, washing and storage workflow.",
        ],
        location: "",
        industry: "",
        project_type: "",
        project_requirements: [],
        scope_of_work: [],
        functional_areas: [],
        delivery_approach: [],
        approved_project_facts: [],
        related_solution: null,
        related_industry: null,
        gallery_references: [],
        cta: {
          label: "Request project consultation",
          description: "Share project requirements for human review.",
          destination: "public_consultation_agent",
        },
      },
      media_suggestions: [
        {
          media_asset_id: "media-1",
          role: "hero",
          order: 0,
          source_page: null,
          source_section: "School canteen overview",
        },
      ],
      evidence: [
        {
          field_path: "case_study.source[0]",
          import_id: "import-1",
          block_order: 0,
          source_section: "School canteen overview",
          source_page: null,
          media_asset_id: null,
        },
      ],
    },
    missing_fields: ["related_solution", "related_industry"],
    failure_reason: null,
    duration_ms: 12,
    correlation_id: "corr-1",
  };
}

function productStructuringRun(): PublicContentStructuringRun {
  const candidates: NonNullable<
    PublicContentStructuringRun["result"]["product_candidates"]
  > = ["A", "B"].map((suffix, index) => ({
    candidate_key: `product-${index + 1}`,
    slug_suggestion: `synthetic-product-${suffix.toLowerCase()}`,
    title: `Synthetic Product ${suffix}`,
    summary: `Synthetic source-backed Product ${suffix} summary.`,
    seo_title: `Synthetic Product ${suffix}`,
    seo_description: `Synthetic source-backed Product ${suffix} summary.`,
    content: {
      page_type: "product",
      product_name: `Synthetic Product ${suffix}`,
      sku_model: `TEST-${suffix}`,
      category: "Preparation Equipment",
      price_mode: index ? "request_quote" : "fixed",
      currency: index ? null : "USD",
      price_min: index ? null : "180.00",
      price_max: null,
    },
    cms_structured_content: {
      product_name: `Synthetic Product ${suffix}`,
      sku_model: `TEST-${suffix}`,
      category: "Preparation Equipment",
      short_description: `Synthetic source-backed Product ${suffix} summary.`,
      detailed_description: ["Synthetic source paragraph."],
      features: ["Synthetic feature"],
      applications: ["Synthetic application"],
      specifications: [],
      price_mode: index ? "request_quote" : "fixed",
      currency: index ? null : "USD",
      price_min: index ? null : "180.00",
      price_max: null,
      hero_media_asset_id: null,
      gallery_media_asset_ids: [],
      drawing_media_asset_ids: [],
      related_products: [],
      related_solution: null,
      related_industry: null,
      related_guide: null,
      related_project: null,
      inquiry_cta: {
        label: "Ask About This Product",
        description: "Human follow-up.",
        destination: "public_consultation_agent",
      },
      quote_cta: {
        label: "Request a Quote",
        description: "Human follow-up.",
        destination: "public_consultation_agent",
      },
    },
    missing_fields: index ? ["content.price_review"] : [],
    media_suggestions: [],
    evidence: [],
  }));
  return {
    id: "product-run-1",
    tenant_id: "tenant-1",
    public_content_import_id: "import-1",
    requested_by: "sales-1",
    selected_page_type: "product",
    recommended_page_type: "product",
    provider: "mock",
    model: "source-structuring-v1",
    locale: "en",
    status: "completed",
    outcome: "requires_human_input",
    result: {
      title: candidates[0].title,
      summary: candidates[0].summary,
      seo_title: candidates[0].seo_title,
      seo_description: candidates[0].seo_description,
      multiple_products_detected: true,
      product_candidates: candidates,
      evidence: [],
    },
    missing_fields: [],
    failure_reason: null,
    duration_ms: 18,
    correlation_id: "product-corr-1",
  };
}

function fixture(): PublicContentImport {
  return {
    id: "import-1",
    tenant_id: "tenant-1",
    source_type: "docx",
    original_filename: "synthetic-brief.docx",
    mime_type:
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    checksum: "a".repeat(64),
    file_size: 1024,
    requested_by: "sales-1",
    storage_provider: "local",
    processing_status: "completed",
    created_at: "2026-08-24T09:00:00Z",
    started_at: "2026-08-24T09:00:01Z",
    completed_at: "2026-08-24T09:00:02Z",
    failure_reason: null,
    extraction_metadata: { block_count: 3, extracted_media_count: 1 },
    extraction_result: {
      title: "Synthetic School Brief",
      blocks: [
        {
          kind: "heading",
          text: "School canteen overview",
          order: 0,
          level: 1,
          page_number: null,
          section_title: "School canteen overview",
        },
        {
          kind: "paragraph",
          text: "Plan preparation, cooking, washing and storage workflow.",
          order: 1,
          level: null,
          page_number: null,
          section_title: "School canteen overview",
        },
        {
          kind: "list",
          text: "Confirm site conditions",
          order: 2,
          level: null,
          page_number: null,
          section_title: "School canteen overview",
        },
      ],
      media: [
        {
          media_asset_id: "media-1",
          order: 0,
          page_number: null,
          section_title: "School canteen overview",
        },
      ],
    },
    extracted_media_ids: ["media-1"],
  };
}
