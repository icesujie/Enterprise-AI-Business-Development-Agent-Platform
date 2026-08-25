"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { apiFetch, type MediaAsset } from "@/lib/api";

export async function uploadMedia(formData: FormData) {
  const payload = new FormData();
  for (const field of ["file", "title", "alt_text", "caption"])
    if (formData.has(field)) payload.set(field, formData.get(field)!);
  payload.set("source_type", "manual_upload");
  const asset = await apiFetch<MediaAsset>("/api/v1/media/assets", {
    method: "POST",
    body: payload,
  });
  revalidatePath("/media");
  redirect(`/media/${asset.id}`);
}

export async function updateMediaMetadata(
  assetId: string,
  recordVersion: number,
  formData: FormData,
) {
  await apiFetch<MediaAsset>(`/api/v1/media/assets/${assetId}`, {
    method: "PATCH",
    headers: { "If-Match": `"${recordVersion}"` },
    body: JSON.stringify({
      title: value(formData, "title"),
      alt_text: value(formData, "alt_text"),
      caption: optional(formData, "caption"),
    }),
  });
  refresh(assetId);
}

export async function governMedia(
  assetId: string,
  recordVersion: number,
  action: "submit-review" | "approve" | "revoke" | "archive",
) {
  await apiFetch<MediaAsset>(`/api/v1/media/assets/${assetId}/${action}`, {
    method: "POST",
    headers: { "If-Match": `"${recordVersion}"` },
  });
  refresh(assetId);
}

function refresh(assetId: string) {
  revalidatePath("/media");
  revalidatePath(`/media/${assetId}`);
}

function value(data: FormData, key: string) {
  const result = data.get(key);
  if (typeof result !== "string" || !result.trim())
    throw new Error(`${key} is required.`);
  return result.trim();
}

function optional(data: FormData, key: string) {
  const result = data.get(key);
  return typeof result === "string" && result.trim() ? result.trim() : null;
}
