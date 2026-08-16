"use client";

import { useActionState } from "react";

import { prepareMarketingAcceptanceSet } from "@/app/(workspace)/marketing-content/actions";
import { initialContentActionState } from "@/app/(workspace)/marketing-content/content-action-state";

export function MarketingAcceptanceControls({
  allowed,
  mockMode,
  zh,
}: {
  allowed: boolean;
  mockMode: boolean;
  zh: boolean;
}) {
  const [state, action, pending] = useActionState(
    prepareMarketingAcceptanceSet,
    initialContentActionState,
  );
  if (!allowed) return null;
  return (
    <form action={action} className="card p-6">
      <h2 className="text-lg font-semibold">
        {zh ? "准备固定验收集" : "Prepare fixed acceptance set"}
      </h2>
      <p className="mt-2 text-sm leading-6 text-[var(--color-muted)]">
        {zh
          ? "创建 10 个固定的中英文 Mock 草稿。可重复执行且不会调用付费模型。"
          : "Create ten fixed English and Chinese Mock drafts. The action is repeatable and never invokes a paid model."}
      </p>
      {!mockMode ? (
        <p className="mt-4 rounded-lg bg-[var(--color-warning-soft)] p-4 text-sm text-[var(--color-warning)]">
          {zh
            ? "当前不是 Mock 模式。为防止意外付费，本操作已禁用。"
            : "The current provider is not Mock. Preparation is disabled to prevent accidental paid calls."}
        </p>
      ) : null}
      {state.status !== "idle" ? (
        <p
          role={state.status === "error" ? "alert" : "status"}
          className={`mt-4 rounded-lg p-3 text-sm ${state.status === "error" ? "bg-[var(--color-danger-soft)] text-[var(--color-danger)]" : "bg-[var(--color-success-soft)] text-[var(--color-success)]"}`}
        >
          {state.message}
        </p>
      ) : null}
      <button
        className="button-primary mt-4"
        disabled={pending || !mockMode}
        type="submit"
      >
        {pending
          ? zh
            ? "正在准备…"
            : "Preparing…"
          : zh
            ? "准备 10 项验收草稿"
            : "Prepare 10 acceptance drafts"}
      </button>
    </form>
  );
}
