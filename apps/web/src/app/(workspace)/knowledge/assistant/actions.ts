"use server";

import {
  apiFetch,
  type KnowledgeAssistantRun,
  type KnowledgeAssistantRunStart,
} from "@/lib/api";

export async function startKnowledgeAssistantRun(input: {
  agent_id: string;
  language: "en" | "zh-CN";
  question: string;
}): Promise<KnowledgeAssistantRunStart> {
  return apiFetch<KnowledgeAssistantRunStart>(
    "/api/v1/knowledge/assistant/runs",
    {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify(input),
    },
  );
}

export async function getKnowledgeAssistantRun(
  runId: string,
): Promise<KnowledgeAssistantRun> {
  return apiFetch<KnowledgeAssistantRun>(
    `/api/v1/knowledge/assistant/runs/${runId}`,
  );
}
