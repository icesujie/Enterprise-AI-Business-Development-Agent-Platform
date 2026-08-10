"use server";

import { apiFetch } from "@/lib/api";
import type {
  PlaygroundRequest,
  PlaygroundRun,
  PlaygroundRunStart,
} from "@/lib/agent-playground";

export async function startPlaygroundRun(
  request: PlaygroundRequest,
): Promise<PlaygroundRunStart> {
  return apiFetch<PlaygroundRunStart>("/api/v1/agent-playground/runs", {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify(request),
  });
}

export async function getPlaygroundRun(runId: string): Promise<PlaygroundRun> {
  return apiFetch<PlaygroundRun>(`/api/v1/agent-runs/${runId}`);
}
