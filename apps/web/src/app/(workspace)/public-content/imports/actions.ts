"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import {
  apiFetch,
  type PublicContentImport,
  type PublicContentItem,
  type PublicContentStructuringRun,
} from "@/lib/api";

export async function importPublicContentDocument(formData: FormData) {
  const payload = new FormData();
  const file = formData.get("file");
  if (!(file instanceof File) || !file.size)
    throw new Error("Select a document to import.");
  payload.set("file", file);
  const record = await apiFetch<PublicContentImport>(
    "/api/v1/public-content/imports",
    { method: "POST", body: payload },
  );
  revalidatePath("/public-content/imports");
  redirect(`/public-content/imports/${record.id}`);
}

export async function structurePublicContentImport(
  importId: string,
  formData: FormData,
) {
  await apiFetch<PublicContentStructuringRun>(
    `/api/v1/public-content/imports/${importId}/structure`,
    {
      method: "POST",
      body: JSON.stringify({
        page_type: value(formData, "page_type"),
        locale: value(formData, "locale"),
      }),
    },
  );
  revalidatePath(`/public-content/imports/${importId}`);
}

export async function createPublicDraftFromImport(
  importId: string,
  runId: string,
  formData: FormData,
) {
  const item = await apiFetch<PublicContentItem>(
    `/api/v1/public-content/imports/${importId}/drafts`,
    {
      method: "POST",
      headers: { "Idempotency-Key": `import-draft-${crypto.randomUUID()}` },
      body: JSON.stringify({
        structuring_run_id: runId,
        product_candidate_key:
          optionalValue(formData, "product_candidate_key") ?? null,
        slug: value(formData, "slug"),
        title: value(formData, "title"),
        summary: value(formData, "summary"),
        seo_title: value(formData, "seo_title"),
        seo_description: value(formData, "seo_description"),
        structured_content: jsonValue(formData, "structured_content"),
        media_references: jsonValue(formData, "media_references"),
        is_synthetic: formData.get("is_synthetic") === "on",
      }),
    },
  );
  revalidatePath("/public-content");
  redirect(`/public-content/${item.id}`);
}

function value(data: FormData, key: string) {
  const result = data.get(key);
  if (typeof result !== "string" || !result.trim())
    throw new Error(`${key} is required.`);
  return result.trim();
}

function optionalValue(data: FormData, key: string) {
  const result = data.get(key);
  return typeof result === "string" && result.trim() ? result.trim() : null;
}

function jsonValue(data: FormData, key: string) {
  return JSON.parse(value(data, key)) as unknown;
}
