import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import MediaDetailPage from "@/app/(workspace)/media/[id]/page";
import MediaPage from "@/app/(workspace)/media/page";
import type { CurrentIdentity, MediaAsset } from "@/lib/api";

const { apiFetchMock } = vi.hoisted(() => ({ apiFetchMock: vi.fn() }));

vi.mock("@/i18n/server", () => ({ getLocale: vi.fn(async () => "en") }));
vi.mock("@/lib/api", () => ({ apiFetch: apiFetchMock }));
vi.mock("@/app/(workspace)/media/actions", () => ({
  uploadMedia: vi.fn(),
  updateMediaMetadata: vi.fn(),
  governMedia: vi.fn(),
}));

beforeEach(() =>
  apiFetchMock.mockImplementation(async (path: string) => fixture(path)),
);
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

test("renders private-by-default upload controls and governed media list", async () => {
  render(
    await MediaPage({
      params: Promise.resolve({}),
      searchParams: Promise.resolve({}),
    }),
  );
  expect(screen.getByRole("heading", { name: "Media Library" })).toBeDefined();
  expect(screen.getByText("Upload as private")).toBeDefined();
  expect(screen.getByText("Synthetic school kitchen image")).toBeDefined();
  expect(screen.getAllByText("approved").length).toBeGreaterThan(0);
  expect(screen.getByLabelText(/upload/i).getAttribute("accept")).toBe(
    "image/jpeg,image/png,image/webp",
  );
});

test("shows stable asset ID, metadata governance, public preview, and audit", async () => {
  render(
    await MediaDetailPage({
      params: Promise.resolve({ id: "media-1" }),
      searchParams: Promise.resolve({}),
    }),
  );
  expect(
    screen.getByRole("heading", { name: "Synthetic school kitchen image" }),
  ).toBeDefined();
  expect(screen.getByText("media-1")).toBeDefined();
  expect(
    screen.getByAltText("Synthetic approved kitchen image."),
  ).toBeDefined();
  expect(
    screen.getByRole("button", { name: "Revoke public use" }),
  ).toBeDefined();
  expect(screen.getByText("media.approve")).toBeDefined();
});

function fixture(path: string): unknown {
  if (typeof path !== "string") return undefined;
  if (path === "/api/v1/me") return identity();
  if (path.includes("/audit"))
    return [
      {
        id: "audit-1",
        media_asset_id: "media-1",
        actor_membership_id: "admin-1",
        action: "media.approve",
        before_metadata: {},
        after_metadata: {},
        details: {},
        correlation_id: null,
        created_at: "2026-08-24T10:00:00Z",
      },
    ];
  if (path === "/api/v1/media/assets/media-1") return asset();
  if (path.startsWith("/api/v1/media/assets?")) return [asset()];
  throw new Error(`Unexpected media API path: ${path}`);
}

function asset(): MediaAsset {
  return {
    id: "media-1",
    tenant_id: "tenant-1",
    media_type: "image",
    original_filename: "synthetic-school-kitchen.webp",
    mime_type: "image/webp",
    file_size: 1024,
    checksum: "a".repeat(64),
    storage_provider: "local",
    width: 1200,
    height: 800,
    title: "Synthetic school kitchen image",
    alt_text: "Synthetic approved kitchen image.",
    caption: "Synthetic fixture.",
    visibility: "public",
    public_use_status: "approved",
    source_type: "manual_upload",
    source_reference_id: null,
    uploaded_by: "sales-1",
    approved_by: "admin-1",
    record_version: 4,
    created_at: "2026-08-24T09:00:00Z",
    updated_at: "2026-08-24T10:00:00Z",
    approved_at: "2026-08-24T10:00:00Z",
    revoked_at: null,
    archived_at: null,
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
      "media:read",
      "media:edit",
      "media:submit_review",
      "media:approve",
      "media:revoke",
      "media:archive",
      "media:audit_read",
    ],
  };
}
