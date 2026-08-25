"use server";

import { randomUUID } from "node:crypto";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import type { PublicContentActionState } from "./action-state";
import {
  ApiRequestError,
  apiFetch,
  type PublicContentGovernanceCommand,
  type PublicContentItem,
} from "@/lib/api";
import {
  runPublicationAutomation,
  type PublicationAutomationOutcome,
} from "@/lib/publication-automation";

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
          media_references: mediaReferences(formData),
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
          media_references: mediaReferences(formData),
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
  try {
    const result = await apiFetch<PublicContentGovernanceCommand>(
      `/api/v1/public-content/items/${itemId}/publish`,
      {
        method: "POST",
        headers: mutationHeaders(
          recordVersion,
          value(formData, "idempotency_key"),
        ),
        body: JSON.stringify({
          public_content_version_id: versionId,
          content_sha256: checksum,
          comment: optional(formData, "comment"),
        }),
      },
    );
    if (!result.publication) {
      return refresh(
        itemId,
        "Published, but no publication event was returned.",
      );
    }
    const automation = await runPublicationAutomation(
      result.item,
      "publish",
      result.publication.event_id,
    );
    return refresh(itemId, automationMessage("Content published.", automation));
  } catch (error) {
    return actionError(error);
  }
}

export async function archivePublicContent(
  itemId: string,
  recordVersion: number,
  restore: boolean,
  _previous: PublicContentActionState,
  formData: FormData,
): Promise<PublicContentActionState> {
  try {
    const idempotencyKey = value(formData, "idempotency_key");
    const item = await apiFetch<PublicContentItem>(
      `/api/v1/public-content/items/${itemId}/${restore ? "restore" : "archive"}`,
      {
        method: "POST",
        headers: mutationHeaders(recordVersion, idempotencyKey),
        body: JSON.stringify({ reason: value(formData, "reason") }),
      },
    );
    if (!item.published_version_id) {
      return refresh(
        itemId,
        restore ? "Content restored." : "Content archived.",
      );
    }
    const eventType = restore ? "publish" : "remove";
    const automation = await runPublicationAutomation(
      item,
      eventType,
      `${eventType}-${idempotencyKey}`,
    );
    return refresh(
      itemId,
      automationMessage(
        restore ? "Content restored." : "Content archived.",
        automation,
      ),
    );
  } catch (error) {
    return actionError(error);
  }
}

export async function retryPublicContentAutomation(
  itemId: string,
  _previous: PublicContentActionState,
  _formData: FormData,
): Promise<PublicContentActionState> {
  void _previous;
  void _formData;
  try {
    const item = await apiFetch<PublicContentItem>(
      `/api/v1/public-content/items/${itemId}`,
    );
    if (!item.published_version_id) {
      return {
        status: "error",
        message: "This content has no published version.",
      };
    }
    const eventType = item.status === "archived" ? "remove" : "publish";
    const automation = await runPublicationAutomation(
      item,
      eventType,
      `retry-${randomUUID()}`,
    );
    return refresh(
      itemId,
      automationMessage("Discovery refresh retried.", automation),
    );
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
  if (value(formData, "page_type") === "product") {
    return productStructured(formData);
  }
  const raw = value(formData, "structured_content");
  const parsed: unknown = JSON.parse(raw);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("Structured content must be a JSON object.");
  }
  return parsed as Record<string, unknown>;
}

function productStructured(formData: FormData): Record<string, unknown> {
  return {
    product_name: value(formData, "product_name"),
    sku_model: value(formData, "sku_model"),
    category: value(formData, "category"),
    brand: optional(formData, "brand"),
    short_description: value(formData, "short_description"),
    detailed_description: lines(formData, "detailed_description"),
    features: lines(formData, "features"),
    applications: lines(formData, "applications"),
    material: optional(formData, "material"),
    dimensions: optional(formData, "dimensions"),
    configuration: optional(formData, "configuration"),
    specifications: jsonField(formData, "specifications", []),
    price_mode: value(formData, "price_mode"),
    currency: optional(formData, "currency")?.toUpperCase() ?? null,
    price_min: optional(formData, "price_min"),
    price_max: optional(formData, "price_max"),
    price_note: optional(formData, "price_note"),
    moq: optional(formData, "moq"),
    availability_note: optional(formData, "availability_note"),
    hero_media_asset_id: optional(formData, "hero_media_asset_id"),
    gallery_media_asset_ids: lines(formData, "gallery_media_asset_ids"),
    drawing_media_asset_ids: lines(formData, "drawing_media_asset_ids"),
    related_products: jsonField(formData, "related_products", []),
    related_solution: jsonField(formData, "related_solution", null),
    related_industry: jsonField(formData, "related_industry", null),
    related_guide: jsonField(formData, "related_guide", null),
    related_project: jsonField(formData, "related_project", null),
    inquiry_cta: {
      label: value(formData, "inquiry_cta_label"),
      description: value(formData, "inquiry_cta_description"),
      destination: "public_consultation_agent",
    },
    quote_cta: {
      label: value(formData, "quote_cta_label"),
      description: value(formData, "quote_cta_description"),
      destination: "public_consultation_agent",
    },
  };
}

function lines(formData: FormData, name: string): string[] {
  return value(formData, name)
    .split(/\r?\n/)
    .map((entry) => entry.trim())
    .filter(Boolean);
}

function jsonField<T>(formData: FormData, name: string, fallback: T): unknown {
  const raw = optional(formData, name);
  return raw ? (JSON.parse(raw) as unknown) : fallback;
}

function mediaReferences(formData: FormData): unknown[] {
  const parsed: unknown = JSON.parse(value(formData, "media_references"));
  if (!Array.isArray(parsed))
    throw new Error("Media references must be a JSON array.");
  return parsed;
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

function automationMessage(
  prefix: string,
  outcome: PublicationAutomationOutcome,
): string {
  if (outcome.retryRequired || !outcome.auditRecorded) {
    return `${prefix} Search/discovery refresh needs an authorized retry. Correlation ID: ${outcome.correlationId}`;
  }
  return `${prefix} Public page, listings, and sitemap were refreshed.`;
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
