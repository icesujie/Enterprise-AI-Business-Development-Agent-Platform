import "server-only";

import { randomUUID } from "node:crypto";
import { revalidatePath, updateTag } from "next/cache";

import { apiFetch, type PublicContentItem } from "@/lib/api";
import { notifyIndexNow, type IndexNowResult } from "@/lib/indexnow";

export type PublicationAutomationOutcome = {
  revalidation: "succeeded" | "failed";
  indexNow: IndexNowResult["status"] | "failed";
  retryRequired: boolean;
  auditRecorded: boolean;
  correlationId: string;
};

export function publicationRevalidationPaths(
  item: Pick<PublicContentItem, "canonical_path" | "page_type">,
): string[] {
  const listing = {
    solution: "/solutions",
    industry: "/industries",
    case_study: "/projects",
    guide: "/guides",
    product: "/products",
  }[item.page_type];
  return [...new Set([item.canonical_path, listing, "/sitemap.xml"])];
}

export async function runPublicationAutomation(
  item: PublicContentItem,
  eventType: "publish" | "remove",
  attemptKey: string,
): Promise<PublicationAutomationOutcome> {
  if (!item.published_version_id) {
    throw new Error(
      "Publication automation requires an exact published version.",
    );
  }
  const started = performance.now();
  const correlationId = randomUUID();
  let revalidation: PublicationAutomationOutcome["revalidation"] = "succeeded";
  try {
    updateTag("public-content");
    for (const path of publicationRevalidationPaths(item)) revalidatePath(path);
  } catch {
    revalidation = "failed";
  }

  let indexNow: PublicationAutomationOutcome["indexNow"];
  try {
    const result = await notifyIndexNow(
      [
        {
          path: item.canonical_path,
          status: eventType === "publish" ? "published" : "archived",
          isPublic: true,
          wasPublished: true,
        },
      ],
      { action: eventType },
    );
    indexNow = result.status;
  } catch {
    indexNow = "failed";
  }

  const retryRequired = revalidation === "failed" || indexNow === "failed";
  let auditRecorded = true;
  try {
    await apiFetch(
      `/api/v1/public-content/items/${item.id}/publication-automation`,
      {
        method: "POST",
        headers: {
          "Idempotency-Key": automationIdempotencyKey(attemptKey),
          "X-Correlation-ID": correlationId,
        },
        body: JSON.stringify({
          event_type: eventType,
          public_content_version_id: item.published_version_id,
          revalidation_outcome: revalidation,
          indexnow_outcome: indexNow,
          duration_ms: Math.max(0, Math.round(performance.now() - started)),
          retry_state: retryRequired ? "retry_required" : "complete",
          failure_code: failureCode(revalidation, indexNow),
        }),
      },
    );
  } catch {
    auditRecorded = false;
  }
  return {
    revalidation,
    indexNow,
    retryRequired,
    auditRecorded,
    correlationId,
  };
}

function automationIdempotencyKey(value: string): string {
  return `publication-auto-${value}`.slice(0, 200);
}

function failureCode(
  revalidation: PublicationAutomationOutcome["revalidation"],
  indexNow: PublicationAutomationOutcome["indexNow"],
): string | null {
  if (revalidation === "failed" && indexNow === "failed")
    return "revalidation_and_indexnow_failed";
  if (revalidation === "failed") return "revalidation_failed";
  if (indexNow === "failed") return "indexnow_failed";
  return null;
}
