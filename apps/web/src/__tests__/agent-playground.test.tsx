import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { AgentPlayground } from "@/components/playground/agent-playground";

const { startMock, getMock } = vi.hoisted(() => ({
  startMock: vi.fn(async () => ({
    run_id: "playground-run-1",
    workflow_type: "agent_playground_qualification",
    status: "queued",
    status_url: "/api/v1/agent-runs/playground-run-1",
    created_at: "2026-08-09T09:00:00Z",
  })),
  getMock: vi.fn(async () => ({
    id: "playground-run-1",
    workflow_type: "agent_playground_qualification",
    status: "succeeded",
    provider_type: "mock",
    error_message: null,
    attempt_count: 1,
    max_attempts: 3,
    result: {
      schema_version: "agent_playground_output_v1",
      domain: "laboratory_animal_facility",
      response_locale: "id",
      qualification_score: 85,
      qualification_level: "A",
      business_summary:
        "Synthetic University sedang mengevaluasi proyek fasilitas IVC.",
      missing_information: ["Jalur pengadaan"],
      risks: ["Tinjauan ahli wajib."],
      recommended_next_actions: ["Tugaskan kepada spesialis fasilitas IVC."],
      demo_only: true,
      human_review_required: true,
    },
  })),
}));

vi.mock("@/app/(workspace)/agent-playground/actions", () => ({
  startPlaygroundRun: startMock,
  getPlaygroundRun: getMock,
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

test("switches agents and localizes the Playground in Bahasa Indonesia", () => {
  render(<AgentPlayground />);

  fireEvent.click(
    screen.getByRole("button", {
      name: /IVC Facility Business Development Agent/,
    }),
  );
  expect(screen.getByLabelText("Organization")).toBeDefined();
  expect(screen.queryByLabelText("Project type")).toBeNull();

  fireEvent.change(screen.getByLabelText("Response language"), {
    target: { value: "id" },
  });
  expect(screen.getByText("Ringkasan proyek terstruktur")).toBeDefined();
  expect(
    screen.getByRole("button", { name: "Jalankan kualifikasi" }),
  ).toBeDefined();
});

test("runs the selected agent and displays the unified structured result", async () => {
  render(<AgentPlayground />);
  fireEvent.click(
    screen.getByRole("button", {
      name: /IVC Facility Business Development Agent/,
    }),
  );
  fireEvent.change(screen.getByLabelText("Response language"), {
    target: { value: "id" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Jalankan kualifikasi" }));

  await waitFor(() => expect(startMock).toHaveBeenCalledOnce());
  await waitFor(
    () => expect(getMock).toHaveBeenCalledWith("playground-run-1"),
    {
      timeout: 1500,
    },
  );
  expect(await screen.findByText("85", {}, { timeout: 1500 })).toBeDefined();
  expect(screen.getByText("Level A")).toBeDefined();
  expect(screen.getByText(/sedang mengevaluasi/)).toBeDefined();
  expect(screen.getByText("Jalur pengadaan")).toBeDefined();
  expect(screen.getByText("Tinjauan ahli wajib.")).toBeDefined();
  expect(
    screen.getByText("Tugaskan kepada spesialis fasilitas IVC."),
  ).toBeDefined();
  expect(screen.queryByText(/chain-of-thought/i)).toBeNull();
});
