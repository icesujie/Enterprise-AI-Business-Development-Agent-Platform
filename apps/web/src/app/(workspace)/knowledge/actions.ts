"use server";

import { revalidatePath } from "next/cache";

import {
  apiFetch,
  type KnowledgeCollection,
  type ManagedKnowledgeDocument,
} from "@/lib/api";

export async function createKnowledgeCollection(formData: FormData) {
  const key = String(formData.get("collection_key") ?? "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, "-");
  await apiFetch<KnowledgeCollection>(
    "/api/v1/knowledge-management/collections",
    {
      method: "POST",
      body: JSON.stringify({
        domain_key: String(formData.get("domain_key") ?? ""),
        collection_key: key,
        name: String(formData.get("name") ?? ""),
        description: String(formData.get("description") ?? "").trim() || null,
        collection_metadata: { source: "workspace" },
      }),
    },
  );
  revalidatePath("/knowledge");
}

export async function uploadKnowledgeDocument(formData: FormData) {
  const collectionId = String(formData.get("collection_id") ?? "");
  const payload = new FormData();
  payload.set("title", String(formData.get("title") ?? ""));
  payload.set(
    "document_type",
    String(formData.get("document_type") ?? "reference"),
  );
  payload.set("language", String(formData.get("language") ?? "en"));
  payload.set("document_metadata_json", '{"source":"workspace_upload"}');
  const file = formData.get("file");
  if (file instanceof File) payload.set("file", file);
  await apiFetch<ManagedKnowledgeDocument>(
    `/api/v1/knowledge-management/collections/${collectionId}/documents`,
    { method: "POST", body: payload },
  );
  revalidatePath("/knowledge");
}

async function command(documentId: string, path: string, body?: unknown) {
  await apiFetch<ManagedKnowledgeDocument>(
    `/api/v1/knowledge-management/documents/${documentId}/${path}`,
    {
      method: "POST",
      body: body === undefined ? undefined : JSON.stringify(body),
    },
  );
  revalidatePath("/knowledge");
}

export async function submitKnowledgeReview(documentId: string) {
  await command(documentId, "submit-review");
}

export async function reviewKnowledgeDocument(
  documentId: string,
  decision: "approved" | "rejected",
) {
  await command(documentId, "approval", { decision });
}

export async function activateKnowledgeDocument(documentId: string) {
  await command(documentId, "activate");
}

export async function archiveKnowledgeDocument(documentId: string) {
  await command(documentId, "archive");
}

export async function processKnowledgeDocument(documentId: string) {
  await command(documentId, "processing-runs");
}

export async function bindKnowledgeDocument(
  documentId: string,
  formData: FormData,
) {
  await command(documentId, "bindings", {
    agent_key: String(formData.get("agent_key") ?? ""),
  });
}
