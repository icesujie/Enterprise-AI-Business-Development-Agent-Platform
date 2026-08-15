"use server";

import {
  ApiRequestError,
  apiFetch,
  type KnowledgeSearchResponse,
} from "@/lib/api";

export type KnowledgeSearchActionResult =
  | { ok: true; data: KnowledgeSearchResponse }
  | { ok: false; kind: "denied" | "error"; message: string };

export async function searchKnowledge(input: {
  agent_id: string;
  query: string;
  language: "en" | "zh-CN" | "id";
  top_k: number;
}): Promise<KnowledgeSearchActionResult> {
  const tenantId =
    process.env.PUBLIC_TENANT_ID ?? "10000000-0000-4000-8000-000000000001";
  try {
    const data = await apiFetch<KnowledgeSearchResponse>(
      "/api/v1/knowledge/search",
      {
        method: "POST",
        body: JSON.stringify({
          ...input,
          tenant_id: tenantId,
          include_diagnostics: true,
        }),
      },
    );
    return { ok: true, data };
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 403) {
      return { ok: false, kind: "denied", message: error.message };
    }
    return {
      ok: false,
      kind: "error",
      message: error instanceof Error ? error.message : "Search failed.",
    };
  }
}
