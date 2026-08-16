"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import {
  ApiRequestError,
  apiFetch,
  type ContentGovernanceCommand,
  type MarketingAcceptanceDashboard,
  type MarketingContentAsset,
  type MarketingGenerationRun,
  type MarketingGenerationStart,
} from "@/lib/api";
import type { ContentActionState } from "@/app/(workspace)/marketing-content/content-action-state";


export async function createAndGenerateContent(
  _previous: ContentActionState,
  formData: FormData,
): Promise<ContentActionState> {
  let runId: string;
  try {
    const request = await apiFetch<{ id: string }>("/api/v1/content/requests", {
      method: "POST",
      headers: { "Idempotency-Key": value(formData, "request_idempotency_key") },
      body: JSON.stringify({
        domain_key: "commercial_kitchen",
        content_type: value(formData, "content_type"),
        audience: value(formData, "audience"),
        language: value(formData, "language"),
        channel: value(formData, "channel"),
        business_objective: value(formData, "business_objective"),
        topic: value(formData, "topic"),
        call_to_action: value(formData, "call_to_action"),
        campaign_name: optional(formData, "campaign_name"),
        constraints: { source: "marketing_ai_workspace" },
      }),
    });
    const run = await apiFetch<MarketingGenerationStart>(
      `/api/v1/content/requests/${request.id}/generate`,
      {
        method: "POST",
        headers: { "Idempotency-Key": value(formData, "generation_idempotency_key") },
      },
    );
    runId = run.run_id;
  } catch (error) {
    return actionError(error);
  }
  redirect(`/marketing-content/generation/${runId}`);
}

export async function prepareMarketingAcceptanceSet(
  _previous: ContentActionState,
): Promise<ContentActionState> {
  void _previous;
  try {
    const dashboard = await apiFetch<MarketingAcceptanceDashboard>(
      "/api/v1/content/acceptance",
    );
    if (!dashboard.mock_preparation_allowed) {
      return {
        status: "error",
        code: "validation",
        message:
          "Acceptance preparation is limited to Mock mode. Switch MARKETING_CONTENT_PROVIDER to mock before preparing the fixed set.",
      };
    }
    let queued = 0;
    for (const acceptanceCase of dashboard.cases) {
      let requestId = acceptanceCase.request_id;
      let requestStatus = acceptanceCase.request_status;
      const retryable =
        requestStatus === "failed" || requestStatus === "insufficient_evidence";
      const attempt = Math.max(
        1,
        acceptanceCase.attempt_count + (retryable ? 1 : 0),
      );
      if (!requestId || retryable) {
        const request = await apiFetch<{ id: string; status: string }>(
          "/api/v1/content/requests",
          {
            method: "POST",
            headers: {
              "Idempotency-Key": `acceptance-request-${acceptanceCase.case_id}-${attempt}`,
            },
            body: JSON.stringify({
              domain_key: "commercial_kitchen",
              content_type: acceptanceCase.content_type,
              audience: acceptanceCase.audience,
              language: acceptanceCase.language,
              channel: acceptanceCase.channel,
              business_objective: acceptanceCase.business_objective,
              topic: acceptanceCase.topic,
              call_to_action: acceptanceCase.call_to_action,
              campaign_name: "Phase 3.2 Business Acceptance",
              constraints: {
                source: "phase_3_2_business_acceptance",
                acceptance_dataset: dashboard.dataset_version,
                acceptance_case_id: acceptanceCase.case_id,
                acceptance_attempt: attempt,
                required_provider: "mock",
              },
            }),
          },
        );
        requestId = request.id;
        requestStatus = request.status;
      }
      if (requestStatus === "draft") {
        await apiFetch(`/api/v1/content/requests/${requestId}/generate`, {
          method: "POST",
          headers: {
            "Idempotency-Key": `acceptance-generate-${acceptanceCase.case_id}-${attempt}`,
          },
        });
        queued += 1;
      }
    }
    revalidatePath("/marketing-content/acceptance");
    revalidatePath("/marketing-content");
    return {
      status: "success",
      message:
        queued > 0
          ? `${queued} fixed Mock acceptance drafts were queued. Refresh shortly to review results.`
          : "The fixed acceptance set is already prepared or processing.",
    };
  } catch (error) {
    return actionError(error);
  }
}

export async function getMarketingGenerationRun(
  runId: string,
): Promise<MarketingGenerationRun> {
  return apiFetch<MarketingGenerationRun>(
    `/api/v1/content/generation-runs/${runId}`,
  );
}

export async function createManualContent(
  _previous: ContentActionState,
  formData: FormData,
): Promise<ContentActionState> {
  const contentType = value(formData, "content_type");
  const audience = value(formData, "audience");
  const language = value(formData, "language") as "en" | "zh-CN";
  const channel = value(formData, "channel");
  const objective = value(formData, "business_objective");
  const topic = value(formData, "topic");
  const callToAction = value(formData, "call_to_action");
  const title = value(formData, "title");
  const body = value(formData, "body");
  let assetId: string;
  try {
    const request = await apiFetch<{ id: string }>("/api/v1/content/requests", {
      method: "POST",
      headers: {
        "Idempotency-Key": value(formData, "request_idempotency_key"),
      },
      body: JSON.stringify({
        domain_key: "commercial_kitchen",
        content_type: contentType,
        audience,
        language,
        channel,
        business_objective: objective,
        topic,
        call_to_action: callToAction,
        campaign_name: optional(formData, "campaign_name"),
        constraints: { source: "manual_marketing_workspace" },
      }),
    });
    const asset = await apiFetch<MarketingContentAsset>(
      "/api/v1/content/assets",
      {
        method: "POST",
        headers: {
          "Idempotency-Key": value(formData, "asset_idempotency_key"),
        },
        body: JSON.stringify({
          domain_key: "commercial_kitchen",
          request_id: request.id,
          title,
          content_type: contentType,
          audience,
          language,
          channel,
          content_body: { body },
          plain_text: body,
          claims: [],
          citations: [],
        }),
      },
    );
    assetId = asset.id;
  } catch (error) {
    return actionError(error);
  }
  revalidatePath("/marketing-content");
  redirect(`/marketing-content/${assetId}`);
}

export async function createContentSuccessor(
  assetId: string,
  recordVersion: number,
  idempotencyKey: string,
  _previous: ContentActionState,
  formData: FormData,
): Promise<ContentActionState> {
  try {
    await apiFetch<MarketingContentAsset>(
      `/api/v1/content/assets/${assetId}/versions`,
      {
        method: "POST",
        headers: mutationHeaders(recordVersion, idempotencyKey),
        body: JSON.stringify({
          content_body: { body: value(formData, "body") },
          plain_text: value(formData, "body"),
          claims: [],
          citations: [],
        }),
      },
    );
    return refresh(assetId, "A new immutable draft version was created.");
  } catch (error) {
    return actionError(error);
  }
}

export async function submitContentReview(
  assetId: string,
  recordVersion: number,
  versionId: string,
  checksum: string,
  idempotencyKey: string,
  _previous: ContentActionState,
  formData: FormData,
): Promise<ContentActionState> {
  try {
    await apiFetch<ContentGovernanceCommand>(
      `/api/v1/content/assets/${assetId}/submit-review`,
      {
        method: "POST",
        headers: mutationHeaders(recordVersion, idempotencyKey),
        body: JSON.stringify({
          content_version_id: versionId,
          content_sha256: checksum,
          comment: optional(formData, "comment"),
        }),
      },
    );
    return refresh(
      assetId,
      "The exact current version was submitted for review.",
    );
  } catch (error) {
    return actionError(error);
  }
}

export async function decideContentReview(
  assetId: string,
  recordVersion: number,
  versionId: string,
  checksum: string,
  decision: "approved" | "rejected" | "changes_requested",
  idempotencyKey: string,
  _previous: ContentActionState,
  formData: FormData,
): Promise<ContentActionState> {
  try {
    await apiFetch<ContentGovernanceCommand>(
      `/api/v1/content/assets/${assetId}/decisions`,
      {
        method: "POST",
        headers: mutationHeaders(recordVersion, idempotencyKey),
        body: JSON.stringify({
          content_version_id: versionId,
          content_sha256: checksum,
          decision,
          comment: optional(formData, "comment"),
        }),
      },
    );
    return refresh(
      assetId,
      decision === "approved"
        ? "The exact reviewed version was approved."
        : "The review decision was recorded and the content returned to draft.",
    );
  } catch (error) {
    return actionError(error);
  }
}

export async function submitContentFeedback(
  assetId: string,
  versionId: string,
  checksum: string,
  idempotencyKey: string,
  _previous: ContentActionState,
  formData: FormData,
): Promise<ContentActionState> {
  try {
    await apiFetch(`/api/v1/content/assets/${assetId}/feedback`, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({
        content_version_id: versionId,
        content_sha256: checksum,
        categories: formData.getAll("categories").map(String),
        note: optional(formData, "note"),
      }),
    });
    return refresh(assetId, "Structured human feedback was recorded.");
  } catch (error) {
    return actionError(error);
  }
}

export async function archiveContent(
  assetId: string,
  recordVersion: number,
  idempotencyKey: string,
  _previous: ContentActionState,
  formData: FormData,
): Promise<ContentActionState> {
  return archiveCommand(
    assetId,
    recordVersion,
    idempotencyKey,
    "archive",
    value(formData, "reason"),
  );
}

export async function restoreContent(
  assetId: string,
  recordVersion: number,
  idempotencyKey: string,
  _previous: ContentActionState,
  formData: FormData,
): Promise<ContentActionState> {
  return archiveCommand(
    assetId,
    recordVersion,
    idempotencyKey,
    "restore",
    value(formData, "reason"),
  );
}

export async function rollbackContentVersion(
  assetId: string,
  sourceVersionId: string,
  recordVersion: number,
  idempotencyKey: string,
  _previous: ContentActionState,
): Promise<ContentActionState> {
  void _previous;
  try {
    await apiFetch<MarketingContentAsset>(
      `/api/v1/content/assets/${assetId}/rollback`,
      {
        method: "POST",
        headers: mutationHeaders(recordVersion, idempotencyKey),
        body: JSON.stringify({ source_version_id: sourceVersionId }),
      },
    );
    return refresh(
      assetId,
      "Rollback created a new draft successor; history was not overwritten.",
    );
  } catch (error) {
    return actionError(error);
  }
}

async function archiveCommand(
  assetId: string,
  recordVersion: number,
  idempotencyKey: string,
  command: "archive" | "restore",
  reason: string,
): Promise<ContentActionState> {
  try {
    await apiFetch<MarketingContentAsset>(
      `/api/v1/content/assets/${assetId}/${command}`,
      {
        method: "POST",
        headers: mutationHeaders(recordVersion, idempotencyKey),
        body: JSON.stringify({ reason }),
      },
    );
    return refresh(
      assetId,
      command === "archive"
        ? "Content archived."
        : "Content restored as a draft.",
    );
  } catch (error) {
    return actionError(error);
  }
}

function mutationHeaders(recordVersion: number, idempotencyKey: string) {
  return {
    "If-Match": `"${recordVersion}"`,
    "Idempotency-Key": idempotencyKey,
  };
}

function refresh(assetId: string, message: string): ContentActionState {
  revalidatePath("/marketing-content");
  revalidatePath(`/marketing-content/${assetId}`);
  return { status: "success", message };
}

function actionError(error: unknown): ContentActionState {
  if (!(error instanceof ApiRequestError)) {
    return {
      status: "error",
      message: "The operation could not be completed.",
    };
  }
  if (error.status === 412) {
    return {
      status: "error",
      code: "stale",
      message:
        "Content has changed since you opened it. Refresh before saving.",
    };
  }
  const code =
    error.status === 403
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
