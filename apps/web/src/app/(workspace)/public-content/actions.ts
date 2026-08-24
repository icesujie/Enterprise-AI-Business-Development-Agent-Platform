"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import type { PublicContentActionState } from "./action-state";
import {
  ApiRequestError,
  apiFetch,
  type PublicContentGovernanceCommand,
  type PublicContentItem,
} from "@/lib/api";

export async function createPublicContent(
  _previous: PublicContentActionState,
  formData: FormData,
): Promise<PublicContentActionState> {
  let itemId: string;
  try {
    const item = await apiFetch<PublicContentItem>(
      "/api/v1/public-content/items",
      {
        method: "POST",
        headers: { "Idempotency-Key": value(formData, "idempotency_key") },
        body: JSON.stringify({
          page_type: value(formData, "page_type"),
          slug: value(formData, "slug"),
          locale: value(formData, "locale"),
          title: value(formData, "title"),
          summary: value(formData, "summary"),
          seo_title: value(formData, "seo_title"),
          seo_description: value(formData, "seo_description"),
          structured_content: structured(formData),
          media_references: [],
          source_type: "manual",
          is_synthetic: formData.get("is_synthetic") === "on",
        }),
      },
    );
    itemId = item.id;
  } catch (error) {
    return actionError(error);
  }
  revalidatePath("/public-content");
  redirect(`/public-content/${itemId}`);
}

export async function createPublicContentSuccessor(
  itemId: string,
  recordVersion: number,
  _previous: PublicContentActionState,
  formData: FormData,
): Promise<PublicContentActionState> {
  try {
    await apiFetch<PublicContentItem>(
      `/api/v1/public-content/items/${itemId}/versions`,
      {
        method: "POST",
        headers: mutationHeaders(
          recordVersion,
          value(formData, "idempotency_key"),
        ),
        body: JSON.stringify({
          title: value(formData, "title"),
          summary: value(formData, "summary"),
          seo_title: value(formData, "seo_title"),
          seo_description: value(formData, "seo_description"),
          structured_content: structured(formData),
          media_references: [],
          source_type: "manual",
        }),
      },
    );
    return refresh(itemId, "A new immutable draft version was created.");
  } catch (error) {
    return actionError(error);
  }
}

export async function submitPublicContentReview(
  itemId: string,
  recordVersion: number,
  versionId: string,
  checksum: string,
  _previous: PublicContentActionState,
  formData: FormData,
): Promise<PublicContentActionState> {
  return exactVersionCommand(
    itemId,
    recordVersion,
    "submit-review",
    versionId,
    checksum,
    value(formData, "idempotency_key"),
    optional(formData, "comment"),
  );
}

export async function decidePublicContentReview(
  itemId: string,
  recordVersion: number,
  versionId: string,
  checksum: string,
  decision: "approved" | "rejected" | "changes_requested",
  _previous: PublicContentActionState,
  formData: FormData,
): Promise<PublicContentActionState> {
  return exactVersionCommand(
    itemId,
    recordVersion,
    "decisions",
    versionId,
    checksum,
    value(formData, "idempotency_key"),
    optional(formData, "comment"),
    decision,
  );
}

export async function publishPublicContent(
  itemId: string,
  recordVersion: number,
  versionId: string,
  checksum: string,
  _previous: PublicContentActionState,
  formData: FormData,
): Promise<PublicContentActionState> {
  return exactVersionCommand(
    itemId,
    recordVersion,
    "publish",
    versionId,
    checksum,
    value(formData, "idempotency_key"),
    optional(formData, "comment"),
  );
}

export async function archivePublicContent(
  itemId: string,
  recordVersion: number,
  restore: boolean,
  _previous: PublicContentActionState,
  formData: FormData,
): Promise<PublicContentActionState> {
  try {
    await apiFetch<PublicContentItem>(
      `/api/v1/public-content/items/${itemId}/${restore ? "restore" : "archive"}`,
      {
        method: "POST",
        headers: mutationHeaders(
          recordVersion,
          value(formData, "idempotency_key"),
        ),
        body: JSON.stringify({ reason: value(formData, "reason") }),
      },
    );
    return refresh(itemId, restore ? "Content restored." : "Content archived.");
  } catch (error) {
    return actionError(error);
  }
}

async function exactVersionCommand(
  itemId: string,
  recordVersion: number,
  command: "submit-review" | "decisions" | "publish",
  versionId: string,
  checksum: string,
  idempotencyKey: string,
  comment: string | null,
  decision?: "approved" | "rejected" | "changes_requested",
): Promise<PublicContentActionState> {
  try {
    await apiFetch<PublicContentGovernanceCommand>(
      `/api/v1/public-content/items/${itemId}/${command}`,
      {
        method: "POST",
        headers: mutationHeaders(recordVersion, idempotencyKey),
        body: JSON.stringify({
          public_content_version_id: versionId,
          content_sha256: checksum,
          comment,
          ...(decision ? { decision } : {}),
        }),
      },
    );
    return refresh(itemId, "Governance action recorded for the exact version.");
  } catch (error) {
    return actionError(error);
  }
}

function structured(formData: FormData): Record<string, unknown> {
  const raw = value(formData, "structured_content");
  const parsed: unknown = JSON.parse(raw);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("Structured content must be a JSON object.");
  }
  return parsed as Record<string, unknown>;
}

function mutationHeaders(recordVersion: number, idempotencyKey: string) {
  return {
    "If-Match": `"${recordVersion}"`,
    "Idempotency-Key": idempotencyKey,
  };
}

function refresh(itemId: string, message: string): PublicContentActionState {
  revalidatePath("/public-content");
  revalidatePath(`/public-content/${itemId}`);
  return { status: "success", message };
}

function actionError(error: unknown): PublicContentActionState {
  if (error instanceof SyntaxError) {
    return {
      status: "error",
      code: "validation",
      message: "Structured content is not valid JSON.",
    };
  }
  if (!(error instanceof ApiRequestError)) {
    return {
      status: "error",
      message: "The operation could not be completed.",
    };
  }
  const code =
    error.status === 412
      ? "stale"
      : error.status === 403
        ? "permission"
        : error.status === 404
          ? "not_found"
          : error.status === 409
            ? "conflict"
            : "validation";
  return { status: "error", code, message: error.message };
}

function value(formData: FormData, name: string): string {
  return String(formData.get(name) ?? "").trim();
}

function optional(formData: FormData, name: string): string | null {
  return value(formData, name) || null;
}
