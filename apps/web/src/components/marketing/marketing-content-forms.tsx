"use client";

import { useActionState } from "react";

import {
  archiveContent,
  createContentSuccessor,
  createAndGenerateContent,
  createManualContent,
  decideContentReview,
  restoreContent,
  rollbackContentVersion,
  submitContentFeedback,
  submitContentReview,
} from "@/app/(workspace)/marketing-content/actions";
import {
  initialContentActionState,
  type ContentActionState,
} from "@/app/(workspace)/marketing-content/content-action-state";
import type {
  CurrentIdentity,
  MarketingContentAsset,
  MarketingContentVersion,
} from "@/lib/api";

export function ManualContentForm({
  zh,
  requestKey,
  assetKey,
}: {
  zh: boolean;
  requestKey: string;
  assetKey: string;
}) {
  const [state, action, pending] = useActionState(
    createManualContent,
    initialContentActionState,
  );
  return (
    <form action={action} className="card space-y-5 p-6">
      <input type="hidden" name="request_idempotency_key" value={requestKey} />
      <input type="hidden" name="asset_idempotency_key" value={assetKey} />
      <div className="grid gap-5 md:grid-cols-2">
        <Field
          label={zh ? "内容标题" : "Content title"}
          name="title"
          required
        />
        <Select
          label={zh ? "内容类型" : "Content type"}
          name="content_type"
          options={contentTypes(zh)}
        />
        <Select
          label={zh ? "目标受众" : "Target audience"}
          name="audience"
          options={audiences(zh)}
        />
        <Select
          label={zh ? "语言" : "Language"}
          name="language"
          options={[
            ["en", "English"],
            ["zh-CN", "中文"],
          ]}
        />
        <Select
          label={zh ? "渠道" : "Channel"}
          name="channel"
          options={[
            ["website", zh ? "网站" : "Website"],
            ["tiktok", "TikTok"],
            ["instagram", "Instagram"],
            ["facebook", "Facebook"],
            ["email", zh ? "邮件草稿" : "Email draft"],
          ]}
        />
        <Field
          label={zh ? "活动名称（可选）" : "Campaign (optional)"}
          name="campaign_name"
        />
      </div>
      <Field
        label={zh ? "业务目标" : "Business objective"}
        name="business_objective"
        required
      />
      <Field
        label={zh ? "主题 / 简报" : "Topic / brief"}
        name="topic"
        required
      />
      <Field
        label={zh ? "行动号召" : "Call to action"}
        name="call_to_action"
        required
      />
      <label className="label">
        {zh ? "正文" : "Content body"}
        <textarea className="field mt-2 min-h-64" name="body" required />
      </label>
      <ActionState state={state} zh={zh} />
      <button className="button-primary" type="submit" disabled={pending}>
        {pending
          ? zh
            ? "正在创建…"
            : "Creating…"
          : zh
            ? "创建人工草稿"
            : "Create manual draft"}
      </button>
      <p className="text-xs leading-5 text-[var(--color-muted)]">
        {zh
          ? "提交后会同时创建内容请求和不可变 v1 草稿，不会调用 AI。"
          : "This creates a governed request and immutable v1 draft together. No AI is called."}
      </p>
    </form>
  );
}

export function ContentFeedbackForm({
  asset,
  identity,
  zh,
  idempotencyKey,
}: {
  asset: MarketingContentAsset;
  identity: CurrentIdentity;
  zh: boolean;
  idempotencyKey: string;
}) {
  const current = asset.current_version;
  const [state, action, pending] = useActionState(
    submitContentFeedback.bind(
      null,
      asset.id,
      current?.id ?? "",
      current?.content_sha256 ?? "",
      idempotencyKey,
    ),
    initialContentActionState,
  );
  if (!current || !has(identity, "content:review") || asset.status === "archived") {
    return null;
  }
  const options: Array<[string, string, string]> = [
    ["useful", "Useful", "有用"],
    ["too_generic", "Too generic", "过于笼统"],
    ["brand_tone_issue", "Brand tone issue", "品牌语气问题"],
    ["weak_cta", "Weak CTA", "行动号召较弱"],
    ["insufficient_evidence", "Insufficient evidence", "证据不足"],
    ["too_long", "Too long", "内容过长"],
    ["channel_mismatch", "Channel mismatch", "渠道不匹配"],
  ];
  return (
    <form action={action} className="card p-6">
      <h2 className="text-lg font-semibold">
        {zh ? "人工质量反馈" : "Human quality feedback"}
      </h2>
      <p className="mt-2 text-sm text-[var(--color-muted)]">
        {zh
          ? `反馈绑定准确的 v${current.version_number} 和校验和，提交后不可修改或删除。`
          : `Feedback is bound to exact v${current.version_number} and checksum and cannot be edited or deleted.`}
      </p>
      <fieldset className="mt-5 grid gap-3">
        <legend className="sr-only">{zh ? "反馈类别" : "Feedback categories"}</legend>
        {options.map(([value, en, cn]) => (
          <label className="flex items-center gap-3 text-sm" key={value}>
            <input name="categories" type="checkbox" value={value} />
            {zh ? cn : en}
          </label>
        ))}
      </fieldset>
      <label className="label mt-5">
        {zh ? "补充说明（可选）" : "Reviewer note (optional)"}
        <textarea className="field mt-2 min-h-24" name="note" />
      </label>
      <ActionState state={state} zh={zh} />
      <button className="button-primary mt-4" disabled={pending} type="submit">
        {pending ? (zh ? "正在记录…" : "Recording…") : zh ? "记录反馈" : "Record feedback"}
      </button>
    </form>
  );
}

export function AiContentRequestForm({
  zh,
  requestKey,
  generationKey,
}: {
  zh: boolean;
  requestKey: string;
  generationKey: string;
}) {
  const [state, action, pending] = useActionState(
    createAndGenerateContent,
    initialContentActionState,
  );
  return (
    <form action={action} className="card space-y-5 border-[var(--color-brand)] p-6">
      <input type="hidden" name="request_idempotency_key" value={requestKey} />
      <input type="hidden" name="generation_idempotency_key" value={generationKey} />
      <div>
        <p className="eyebrow">{zh ? "受治理的 AI 生成" : "Governed AI generation"}</p>
        <h2 className="mt-2 text-xl font-semibold">
          {zh ? "根据已批准公开知识生成草稿" : "Generate from approved public knowledge"}
        </h2>
        <p className="mt-2 text-sm text-[var(--color-muted)]">
          {zh
            ? "AI 只能创建 Generated 版本，不能批准或发布。证据不足时系统不会猜测。"
            : "AI can create only a Generated version; it cannot approve or publish. Weak evidence returns an explicit no-draft outcome."}
        </p>
      </div>
      <div className="grid gap-5 md:grid-cols-2">
        <Select label={zh ? "内容类型" : "Content type"} name="content_type" options={contentTypes(zh)} />
        <Select label={zh ? "目标受众" : "Target audience"} name="audience" options={audiences(zh)} />
        <Select label={zh ? "语言" : "Language"} name="language" options={[["en", "English"], ["zh-CN", "中文"]]} />
        <Select label={zh ? "渠道" : "Channel"} name="channel" options={[["website", zh ? "网站" : "Website"], ["tiktok", "TikTok"], ["instagram", "Instagram"], ["facebook", "Facebook"], ["email", zh ? "邮件草稿" : "Email draft"]]} />
        <Field label={zh ? "活动名称（可选）" : "Campaign (optional)"} name="campaign_name" />
      </div>
      <Field label={zh ? "业务目标" : "Business objective"} name="business_objective" required />
      <Field label={zh ? "主题 / 简报" : "Topic / brief"} name="topic" required />
      <Field label={zh ? "行动号召" : "Call to action"} name="call_to_action" required />
      <ActionState state={state} zh={zh} />
      <button className="button-primary" type="submit" disabled={pending}>
        {pending ? (zh ? "正在排队…" : "Queuing…") : zh ? "生成 AI 草稿" : "Generate AI draft"}
      </button>
    </form>
  );
}

export function ContentDetailActions({
  asset,
  identity,
  zh,
  keys,
}: {
  asset: MarketingContentAsset;
  identity: CurrentIdentity;
  zh: boolean;
  keys: Record<string, string>;
}) {
  const current = asset.current_version;
  const canEdit = has(identity, "content:edit") && asset.status !== "archived";
  const canSubmit =
    has(identity, "content:submit_review") &&
    ["draft", "generated"].includes(asset.status);
  const canApprove =
    has(identity, "content:approve") &&
    asset.status === "review" &&
    asset.creator_membership_id !== identity.membership_id;
  const canArchive = has(identity, "content:archive");
  const [editState, editAction, editPending] = useActionState(
    createContentSuccessor.bind(
      null,
      asset.id,
      asset.record_version,
      keys.edit,
    ),
    initialContentActionState,
  );
  const [submitState, submitAction, submitPending] = useActionState(
    submitContentReview.bind(
      null,
      asset.id,
      asset.record_version,
      current?.id ?? "",
      current?.content_sha256 ?? "",
      keys.submit,
    ),
    initialContentActionState,
  );
  const [approveState, approveAction, approvePending] = useActionState(
    decideContentReview.bind(
      null,
      asset.id,
      asset.record_version,
      current?.id ?? "",
      current?.content_sha256 ?? "",
      "approved",
      keys.approve,
    ),
    initialContentActionState,
  );
  const [rejectState, rejectAction, rejectPending] = useActionState(
    decideContentReview.bind(
      null,
      asset.id,
      asset.record_version,
      current?.id ?? "",
      current?.content_sha256 ?? "",
      "rejected",
      keys.reject,
    ),
    initialContentActionState,
  );
  const lifecycleAction =
    asset.status === "archived" ? restoreContent : archiveContent;
  const [archiveState, archiveAction, archivePending] = useActionState(
    lifecycleAction.bind(null, asset.id, asset.record_version, keys.archive),
    initialContentActionState,
  );

  return (
    <div className="space-y-6">
      {canEdit && current ? (
        <form action={editAction} className="card p-6">
          <h2 className="text-lg font-semibold">
            {zh ? "创建后继版本" : "Create successor version"}
          </h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            {zh
              ? `编辑不会覆盖 v${current.version_number}，而是创建新的草稿版本。`
              : `Editing never overwrites v${current.version_number}; it creates a new draft.`}
          </p>
          <label className="label mt-5">
            {zh ? "正文" : "Content body"}
            <textarea
              className="field mt-2 min-h-56"
              name="body"
              defaultValue={current.plain_text}
              required
            />
          </label>
          <ActionState state={editState} zh={zh} />
          <button
            className="button-primary mt-4"
            disabled={editPending}
            type="submit"
          >
            {editPending
              ? zh
                ? "正在保存…"
                : "Saving…"
              : zh
                ? "保存为新版本"
                : "Save as new version"}
          </button>
        </form>
      ) : null}

      {canSubmit && current ? (
        <form action={submitAction} className="card p-6">
          <h2 className="text-lg font-semibold">
            {zh ? "提交审核" : "Submit review"}
          </h2>
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            {zh
              ? `提交精确的 v${current.version_number} 和校验和，后续编辑会使本次审核失效。`
              : `Submit exact v${current.version_number} and its checksum. Any later edit invalidates this review.`}
          </p>
          <input
            className="field mt-4"
            name="comment"
            placeholder={zh ? "审核备注（可选）" : "Review note (optional)"}
          />
          <ActionState state={submitState} zh={zh} />
          <button
            className="button-primary mt-4"
            disabled={submitPending}
            type="submit"
          >
            {zh ? "提交审核" : "Submit for review"}
          </button>
        </form>
      ) : null}

      {canApprove && current ? (
        <div className="grid gap-5 lg:grid-cols-2">
          <form action={approveAction} className="card p-6">
            <h2 className="text-lg font-semibold">
              {zh ? "批准版本" : "Approve version"}
            </h2>
            <input
              className="field mt-4"
              name="comment"
              placeholder={zh ? "批准意见（可选）" : "Approval note (optional)"}
            />
            <ActionState state={approveState} zh={zh} />
            <button
              className="button-primary mt-4"
              disabled={approvePending}
              type="submit"
            >
              {zh
                ? `批准 v${current.version_number}`
                : `Approve v${current.version_number}`}
            </button>
          </form>
          <form action={rejectAction} className="card p-6">
            <h2 className="text-lg font-semibold">
              {zh ? "拒绝版本" : "Reject version"}
            </h2>
            <input
              className="field mt-4"
              name="comment"
              minLength={3}
              placeholder={zh ? "拒绝原因" : "Rejection reason"}
              required
            />
            <ActionState state={rejectState} zh={zh} />
            <button
              className="button-tertiary mt-4"
              disabled={rejectPending}
              type="submit"
            >
              {zh ? "拒绝并退回草稿" : "Reject and return to draft"}
            </button>
          </form>
        </div>
      ) : null}

      {has(identity, "content:approve") &&
      asset.status === "review" &&
      asset.creator_membership_id === identity.membership_id ? (
        <p className="rounded-lg bg-[var(--color-warning-soft)] p-4 text-sm text-[var(--color-warning)]">
          {zh
            ? "职责分离：您创建了此内容，因此不能批准自己的版本。"
            : "Separation of duties: you created this content and cannot approve your own version."}
        </p>
      ) : null}

      {canArchive ? (
        <form action={archiveAction} className="card p-6">
          <h2 className="text-lg font-semibold">
            {asset.status === "archived"
              ? zh
                ? "恢复内容"
                : "Restore content"
              : zh
                ? "归档内容"
                : "Archive content"}
          </h2>
          <input
            className="field mt-4"
            name="reason"
            minLength={3}
            placeholder={zh ? "操作原因" : "Reason"}
            required
          />
          <ActionState state={archiveState} zh={zh} />
          <button
            className="button-tertiary mt-4"
            disabled={archivePending}
            type="submit"
          >
            {asset.status === "archived"
              ? zh
                ? "恢复为草稿"
                : "Restore as draft"
              : zh
                ? "归档"
                : "Archive"}
          </button>
        </form>
      ) : null}
    </div>
  );
}

export function RollbackVersionButton({
  asset,
  version,
  zh,
  idempotencyKey,
}: {
  asset: MarketingContentAsset;
  version: MarketingContentVersion;
  zh: boolean;
  idempotencyKey: string;
}) {
  const [state, action, pending] = useActionState(
    rollbackContentVersion.bind(
      null,
      asset.id,
      version.id,
      asset.record_version,
      idempotencyKey,
    ),
    initialContentActionState,
  );
  return (
    <form action={action}>
      <button className="button-tertiary" type="submit" disabled={pending}>
        {zh ? `恢复为新版本` : "Restore as new version"}
      </button>
      <ActionState state={state} zh={zh} compact />
    </form>
  );
}

function ActionState({
  state,
  zh,
  compact = false,
}: {
  state: ContentActionState;
  zh: boolean;
  compact?: boolean;
}) {
  if (state.status === "idle") return null;
  const text =
    state.code === "stale" && zh
      ? "内容自您打开后已发生变化，请刷新页面后再保存。"
      : state.message;
  return (
    <p
      role={state.status === "error" ? "alert" : "status"}
      className={`${compact ? "mt-2 text-xs" : "mt-4 rounded-lg p-3 text-sm"} ${state.status === "error" ? "bg-[var(--color-danger-soft)] text-[var(--color-danger)]" : "bg-[var(--color-success-soft)] text-[var(--color-success)]"}`}
    >
      {text}
    </p>
  );
}

function Field({
  label,
  name,
  required = false,
}: {
  label: string;
  name: string;
  required?: boolean;
}) {
  return (
    <label className="label">
      {label}
      <input className="field mt-2" name={name} required={required} />
    </label>
  );
}

function Select({
  label,
  name,
  options,
}: {
  label: string;
  name: string;
  options: string[][];
}) {
  return (
    <label className="label">
      {label}
      <select className="field mt-2" name={name}>
        {options.map(([value, title]) => (
          <option value={value} key={value}>
            {title}
          </option>
        ))}
      </select>
    </label>
  );
}

function contentTypes(zh: boolean): string[][] {
  return [
    ["website_article", zh ? "网站文章" : "Website article"],
    ["tiktok_script", "TikTok script"],
    ["instagram_reel_script", "Instagram Reel script"],
    ["facebook_post", "Facebook post"],
    ["email_draft", zh ? "邮件草稿" : "Email draft"],
  ];
}

function audiences(zh: boolean): string[][] {
  return [
    ["schools", zh ? "学校" : "Schools"],
    ["hospitals", zh ? "医院" : "Hospitals"],
    ["factories", zh ? "工厂" : "Factories"],
    ["central_kitchens", zh ? "中央厨房" : "Central kitchens"],
    ["project_owners", zh ? "项目业主" : "Project owners"],
    ["facility_managers", zh ? "设施经理" : "Facility managers"],
  ];
}

function has(identity: CurrentIdentity, permission: string): boolean {
  return identity.permissions.includes(permission);
}
