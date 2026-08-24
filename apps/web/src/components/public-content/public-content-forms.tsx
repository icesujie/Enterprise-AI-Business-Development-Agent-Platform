"use client";

import { useActionState, useId, useState } from "react";

import {
  archivePublicContent,
  createPublicContent,
  createPublicContentSuccessor,
  decidePublicContentReview,
  publishPublicContent,
  submitPublicContentReview,
} from "@/app/(workspace)/public-content/actions";
import {
  initialPublicContentActionState,
  type PublicContentActionState,
} from "@/app/(workspace)/public-content/action-state";
import type { CurrentIdentity, PublicContentItem } from "@/lib/api";

type PageType = "solution" | "industry" | "case_study" | "guide";

export function CreatePublicContentForm({ zh }: { zh: boolean }) {
  const [pageType, setPageType] = useState<PageType>("solution");
  const [state, action, pending] = useActionState(
    createPublicContent,
    initialPublicContentActionState,
  );
  return (
    <form action={action} className="card space-y-6 p-6">
      <IdempotencyInput />
      <div className="grid gap-5 sm:grid-cols-3">
        <Field label={zh ? "页面类型" : "Page type"}>
          <select
            className="input"
            name="page_type"
            value={pageType}
            onChange={(event) => setPageType(event.target.value as PageType)}
          >
            <option value="solution">Solution</option>
            <option value="industry">Industry</option>
            <option value="case_study">Case study</option>
            <option value="guide">Guide</option>
          </select>
        </Field>
        <Field label={zh ? "语言" : "Locale"}>
          <select className="input" name="locale" defaultValue="en">
            <option value="en">English</option>
            <option value="zh-CN">中文</option>
          </select>
        </Field>
        <Field label={zh ? "网址标识" : "URL slug"}>
          <input
            className="input"
            name="slug"
            required
            pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
          />
        </Field>
      </div>
      <MetadataFields />
      <StructuredEditor key={pageType} pageType={pageType} />
      <label className="flex items-center gap-3 text-sm text-[var(--color-muted)]">
        <input type="checkbox" name="is_synthetic" />
        {zh
          ? "标记为合成/演示内容（禁止发布）"
          : "Synthetic/demo content (publishing is blocked)"}
      </label>
      <ActionState state={state} />
      <button className="button-primary" disabled={pending} type="submit">
        {pending
          ? zh
            ? "创建中…"
            : "Creating…"
          : zh
            ? "创建草稿"
            : "Create draft"}
      </button>
    </form>
  );
}

export function PublicContentDetailActions({
  item,
  identity,
  zh,
}: {
  item: PublicContentItem;
  identity: CurrentIdentity;
  zh: boolean;
}) {
  const current = item.current_version;
  const can = (permission: string) => identity.permissions.includes(permission);
  const [editState, editAction, editPending] = useActionState(
    createPublicContentSuccessor.bind(null, item.id, item.record_version),
    initialPublicContentActionState,
  );
  if (!current) return null;
  return (
    <div className="space-y-6">
      {can("public_content:edit") && item.status !== "archived" ? (
        <form action={editAction} className="card space-y-5 p-6">
          <h2 className="text-lg font-semibold">
            {zh ? "创建后继版本" : "Create successor version"}
          </h2>
          <IdempotencyInput />
          <MetadataFields version={current} />
          <StructuredEditor
            pageType={item.page_type}
            value={current.structured_content}
          />
          <ActionState state={editState} />
          <button
            className="button-secondary"
            disabled={editPending}
            type="submit"
          >
            {editPending
              ? zh
                ? "保存中…"
                : "Saving…"
              : zh
                ? "保存为新版本"
                : "Save as new version"}
          </button>
        </form>
      ) : null}

      <section className="card space-y-4 p-6">
        <h2 className="text-lg font-semibold">
          {zh ? "治理操作" : "Governance actions"}
        </h2>
        <p className="text-sm text-[var(--color-muted)]">
          {zh
            ? "审批和发布始终绑定当前版本及校验值。"
            : "Review and publishing always target the exact current version and checksum."}
        </p>
        {can("public_content:submit_review") && item.status === "draft" ? (
          <GovernanceForm
            item={item}
            command="submit"
            label={zh ? "提交审核" : "Submit review"}
          />
        ) : null}
        {can("public_content:review") && item.status === "review" ? (
          <GovernanceForm
            item={item}
            command="changes_requested"
            label={zh ? "要求修改" : "Request changes"}
          />
        ) : null}
        {can("public_content:approve") && item.status === "review" ? (
          <>
            <GovernanceForm
              item={item}
              command="approved"
              label={zh ? "批准版本" : "Approve version"}
            />
            <GovernanceForm
              item={item}
              command="rejected"
              label={zh ? "拒绝版本" : "Reject version"}
            />
          </>
        ) : null}
        {can("public_content:publish") && item.status === "approved" ? (
          <GovernanceForm
            item={item}
            command="publish"
            label={zh ? "发布批准版本" : "Publish approved version"}
          />
        ) : null}
        {can("public_content:archive") && item.status !== "archived" ? (
          <LifecycleForm
            item={item}
            restore={false}
            label={zh ? "归档" : "Archive"}
          />
        ) : null}
        {can("public_content:publish") && item.status === "archived" ? (
          <LifecycleForm item={item} restore label={zh ? "恢复" : "Restore"} />
        ) : null}
      </section>
    </div>
  );
}

function GovernanceForm({
  item,
  command,
  label,
}: {
  item: PublicContentItem;
  command: "submit" | "changes_requested" | "approved" | "rejected" | "publish";
  label: string;
}) {
  const current = item.current_version!;
  const serverAction =
    command === "submit"
      ? submitPublicContentReview.bind(
          null,
          item.id,
          item.record_version,
          current.id,
          current.content_sha256,
        )
      : command === "publish"
        ? publishPublicContent.bind(
            null,
            item.id,
            item.record_version,
            current.id,
            current.content_sha256,
          )
        : decidePublicContentReview.bind(
            null,
            item.id,
            item.record_version,
            current.id,
            current.content_sha256,
            command,
          );
  const [state, action, pending] = useActionState(
    serverAction,
    initialPublicContentActionState,
  );
  return (
    <form
      action={action}
      className="rounded-xl border border-[var(--color-line)] p-4"
    >
      <IdempotencyInput />
      <textarea
        className="input min-h-20"
        name="comment"
        placeholder="Review note"
      />
      <ActionState state={state} />
      <button className="button-tertiary mt-3" disabled={pending} type="submit">
        {pending ? "Working…" : label}
      </button>
    </form>
  );
}

function LifecycleForm({
  item,
  restore,
  label,
}: {
  item: PublicContentItem;
  restore: boolean;
  label: string;
}) {
  const [state, action, pending] = useActionState(
    archivePublicContent.bind(null, item.id, item.record_version, restore),
    initialPublicContentActionState,
  );
  return (
    <form
      action={action}
      className="rounded-xl border border-[var(--color-line)] p-4"
    >
      <IdempotencyInput />
      <input
        className="input"
        name="reason"
        minLength={3}
        required
        placeholder="Reason"
      />
      <ActionState state={state} />
      <button className="button-tertiary mt-3" disabled={pending} type="submit">
        {pending ? "Working…" : label}
      </button>
    </form>
  );
}

function MetadataFields({
  version,
}: {
  version?: PublicContentItem["current_version"];
}) {
  return (
    <div className="grid gap-5 sm:grid-cols-2">
      <Field label="Title">
        <input
          className="input"
          name="title"
          defaultValue={version?.title}
          required
        />
      </Field>
      <Field label="SEO title">
        <input
          className="input"
          name="seo_title"
          defaultValue={version?.seo_title}
          required
        />
      </Field>
      <Field label="Summary">
        <textarea
          className="input min-h-28"
          name="summary"
          defaultValue={version?.summary}
          required
        />
      </Field>
      <Field label="SEO description">
        <textarea
          className="input min-h-28"
          name="seo_description"
          defaultValue={version?.seo_description}
          required
        />
      </Field>
    </div>
  );
}

function StructuredEditor({
  pageType,
  value,
}: {
  pageType: PageType;
  value?: Record<string, unknown>;
}) {
  return (
    <Field label="Structured page content (JSON)">
      <p className="mb-2 text-xs leading-5 text-[var(--color-muted)]">
        Schema-controlled fields only. HTML is not accepted. Media references
        use stable IDs in a later phase.
      </p>
      <textarea
        className="input min-h-[28rem] font-mono text-xs leading-5"
        name="structured_content"
        defaultValue={JSON.stringify(value ?? template(pageType), null, 2)}
        spellCheck={false}
        required
      />
    </Field>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block text-sm font-semibold">
      <span className="mb-2 block">{label}</span>
      {children}
    </label>
  );
}

function ActionState({ state }: { state: PublicContentActionState }) {
  if (state.status === "idle") return null;
  return (
    <p
      role="status"
      className={`mt-3 text-sm ${state.status === "error" ? "text-[var(--color-danger)]" : "text-[var(--color-success)]"}`}
    >
      {state.message}
    </p>
  );
}

function IdempotencyInput() {
  const id = useId();
  return (
    <input
      type="hidden"
      name="idempotency_key"
      value={`public-content-${id}`}
    />
  );
}

function template(pageType: PageType): Record<string, unknown> {
  const cta = {
    label: "Start project consultation",
    description: "Share project requirements for human review.",
    destination: "public_consultation_agent",
  };
  if (pageType === "solution")
    return {
      overview: [""],
      customer_needs: [""],
      service_scope: [{ title: "", description: "" }],
      workflow_areas: [{ title: "", description: "" }],
      related_industries: [],
      related_projects: [],
      cta,
    };
  if (pageType === "industry")
    return {
      overview: [""],
      business_needs: [""],
      relevant_solutions: [],
      project_considerations: [{ title: "", description: "" }],
      related_projects: [],
      cta,
    };
  if (pageType === "case_study")
    return {
      project_overview: [""],
      location: "",
      industry: "",
      project_type: "",
      project_requirements: [""],
      scope_of_work: [{ title: "", description: "" }],
      functional_areas: [{ title: "", description: "" }],
      delivery_approach: [{ title: "", description: "" }],
      approved_project_facts: [{ label: "", value: "", source_note: "" }],
      gallery_references: [],
      related_solution: { label: "", path: "/solutions/" },
      related_industry: { label: "", path: "/industries/" },
      cta,
    };
  return {
    introduction: [""],
    sections: [{ title: "", description: "" }],
    faq_items: [],
    related_solutions: [],
    related_industries: [],
    related_projects: [],
    cta,
  };
}
