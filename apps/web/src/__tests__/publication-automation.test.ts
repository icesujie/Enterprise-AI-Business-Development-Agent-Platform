import { beforeEach, expect, test, vi } from "vitest";

import {
  publicationRevalidationPaths,
  runPublicationAutomation,
} from "@/lib/publication-automation";
import type { PublicContentItem } from "@/lib/api";

const { apiFetchMock, notifyIndexNowMock, revalidatePathMock, updateTagMock } =
  vi.hoisted(() => ({
    apiFetchMock: vi.fn(),
    notifyIndexNowMock: vi.fn(),
    revalidatePathMock: vi.fn(),
    updateTagMock: vi.fn(),
  }));

vi.mock("next/cache", () => ({
  revalidatePath: revalidatePathMock,
  updateTag: updateTagMock,
}));
vi.mock("@/lib/api", () => ({ apiFetch: apiFetchMock }));
vi.mock("@/lib/indexnow", () => ({ notifyIndexNow: notifyIndexNowMock }));

beforeEach(() => {
  vi.clearAllMocks();
  apiFetchMock.mockResolvedValue({ status: "recorded" });
  notifyIndexNowMock.mockResolvedValue({ status: "disabled", submitted: 0 });
});

test("refreshes the exact Product route, listing, sitemap and records a safe outcome", async () => {
  const item = fixture("published");
  expect(publicationRevalidationPaths(item)).toEqual([
    "/products/governed-product",
    "/products",
    "/sitemap.xml",
  ]);

  const outcome = await runPublicationAutomation(item, "publish", "event-1");

  expect(outcome).toEqual(
    expect.objectContaining({
      revalidation: "succeeded",
      indexNow: "disabled",
      retryRequired: false,
      auditRecorded: true,
    }),
  );
  expect(updateTagMock).toHaveBeenCalledWith("public-content");
  expect(revalidatePathMock.mock.calls.map(([path]) => path)).toEqual([
    "/products/governed-product",
    "/products",
    "/sitemap.xml",
  ]);
  expect(notifyIndexNowMock).toHaveBeenCalledWith(
    [
      expect.objectContaining({
        path: "/products/governed-product",
        status: "published",
        wasPublished: true,
      }),
    ],
    { action: "publish" },
  );
  expect(apiFetchMock).toHaveBeenCalledWith(
    "/api/v1/public-content/items/item-1/publication-automation",
    expect.objectContaining({
      method: "POST",
      body: expect.stringContaining('"public_content_version_id":"version-1"'),
    }),
  );
});

test("isolates IndexNow failure from publication and records retry-required", async () => {
  notifyIndexNowMock.mockRejectedValue(new Error("Temporary provider failure"));
  const outcome = await runPublicationAutomation(
    fixture("published"),
    "publish",
    "event-failure",
  );

  expect(outcome.indexNow).toBe("failed");
  expect(outcome.retryRequired).toBe(true);
  const request = apiFetchMock.mock.calls[0][1] as RequestInit;
  expect(request.body).toContain('"retry_state":"retry_required"');
  expect(request.body).toContain('"failure_code":"indexnow_failed"');
});

test("notifies the canonical formerly-published URL after archive", async () => {
  await runPublicationAutomation(fixture("archived"), "remove", "archive-1");
  expect(notifyIndexNowMock).toHaveBeenCalledWith(
    [
      expect.objectContaining({
        path: "/products/governed-product",
        status: "archived",
        wasPublished: true,
      }),
    ],
    { action: "remove" },
  );
});

function fixture(status: "published" | "archived"): PublicContentItem {
  return {
    id: "item-1",
    tenant_id: "tenant-1",
    page_type: "product",
    slug: "governed-product",
    locale: "en",
    title: "Governed Product",
    summary: "Approved public product.",
    seo_title: "Governed Product",
    seo_description: "Approved public product metadata.",
    canonical_path: "/products/governed-product",
    status,
    is_synthetic: false,
    current_version_id: "version-1",
    approved_version_id: "version-1",
    published_version_id: "version-1",
    created_by: "sales-1",
    approved_by: "admin-1",
    published_by: "admin-1",
    record_version: 4,
    created_at: "2026-08-25T08:00:00Z",
    updated_at: "2026-08-25T09:00:00Z",
    published_at: "2026-08-25T09:00:00Z",
    archived_at: status === "archived" ? "2026-08-25T10:00:00Z" : null,
    archived_by: status === "archived" ? "admin-1" : null,
    archive_reason: status === "archived" ? "Test archive" : null,
    current_version: null,
    approved_version: null,
    published_version: null,
  };
}
