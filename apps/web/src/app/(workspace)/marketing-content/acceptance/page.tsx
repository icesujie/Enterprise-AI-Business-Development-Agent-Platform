import Link from "next/link";

import { MarketingAcceptanceControls } from "@/components/marketing/marketing-acceptance-controls";
import { StatusBadge } from "@/components/ui/status";
import { PageHeader } from "@/components/workspace/page-header";
import { getLocale } from "@/i18n/server";
import {
  apiFetch,
  type CurrentIdentity,
  type MarketingAcceptanceDashboard,
} from "@/lib/api";

export default async function MarketingAcceptancePage() {
  const [dashboard, identity, locale] = await Promise.all([
    apiFetch<MarketingAcceptanceDashboard>("/api/v1/content/acceptance"),
    apiFetch<CurrentIdentity>("/api/v1/me"),
    getLocale(),
  ]);
  const zh = locale === "zh-CN";
  const summary = dashboard.summary;
  return (
    <div className="space-y-7">
      <Link className="text-sm font-semibold text-[var(--color-brand)]" href="/marketing-content">
        ← {zh ? "返回营销内容" : "Back to Marketing Content"}
      </Link>
      <PageHeader
        eyebrow={zh ? "Phase 3.2 业务验收" : "Phase 3.2 business acceptance"}
        title={zh ? "营销内容智能体最终验收" : "Marketing Content Agent final acceptance"}
        description={
          zh
            ? "使用固定的 10 项中英文业务案例完成编辑、反馈、审核和批准。所有动作复用现有内容治理流程。"
            : "Review, edit, give feedback, and decide ten fixed bilingual business cases through the existing governed content lifecycle."
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <Summary label={zh ? "验收案例" : "Acceptance cases"} value={summary.total} />
        <Summary label={zh ? "已准备" : "Prepared"} value={summary.prepared} />
        <Summary label={zh ? "已审核" : "Reviewed"} value={summary.reviewed} />
        <Summary label={zh ? "已批准" : "Approved"} value={summary.approved} />
        <Summary label={zh ? "已拒绝" : "Rejected"} value={summary.rejected} />
      </section>

      <section className="grid gap-5 lg:grid-cols-3">
        <ReadinessCard
          title={zh ? "人工修改比例" : "Human Edit Distance"}
          status={summary.average_human_edit_distance == null ? "pending" : "ready"}
          detail={
            summary.average_human_edit_distance == null
              ? zh
                ? "尚无人工批准后继版本，不生成虚假指标。"
                : "No approved human successor exists; no metric is fabricated."
              : `${Math.round(summary.average_human_edit_distance * 100)}% ${zh ? "平均修改" : "average change"}`
          }
          zh={zh}
        />
        <ReadinessCard
          title={zh ? "品牌指南验证" : "Brand Guideline validation"}
          status="pending"
          detail={
            zh
              ? "尚无获业务方批准的真实 Sari Arta 品牌指南。"
              : summary.brand_guideline_note
          }
          zh={zh}
        />
        <ReadinessCard
          title={zh ? "OpenAI 对比" : "OpenAI comparison"}
          status="pending"
          detail={
            zh
              ? "受控的一个英文和一个中文案例尚未人工执行。"
              : summary.openai_comparison_note
          }
          zh={zh}
        />
      </section>

      <MarketingAcceptanceControls
        allowed={identity.permissions.includes("content:generate")}
        mockMode={dashboard.mock_preparation_allowed}
        zh={zh}
      />

      <section className="card overflow-hidden">
        <div className="border-b border-[var(--color-line)] p-5">
          <h2 className="text-lg font-semibold">{zh ? "固定验收案例" : "Fixed acceptance cases"}</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            {dashboard.dataset_version} · {zh ? "当前提供方" : "Configured provider"}: {dashboard.configured_provider}
          </p>
        </div>
        <div className="divide-y divide-[var(--color-line)]">
          {dashboard.cases.map((item, index) => (
            <article className="grid gap-4 p-5 lg:grid-cols-[50px_minmax(240px,2fr)_1fr_1fr_170px] lg:items-center" key={item.case_id}>
              <strong className="text-[var(--color-muted)]">{String(index + 1).padStart(2, "0")}</strong>
              <div>
                <p className="font-semibold">{item.scenario}</p>
                <p className="mt-1 text-sm text-[var(--color-muted)]">{typeLabel(item.content_type, zh)} · {item.language} · {item.channel}</p>
                <p className="mt-2 text-sm leading-6">{item.topic}</p>
              </div>
              <div className="space-y-2 text-sm">
                <StatusBadge tone={item.approved ? "success" : item.rejected ? "danger" : item.reviewed ? "info" : "neutral"}>
                  {item.approved ? (zh ? "已批准" : "Approved") : item.rejected ? (zh ? "已拒绝" : "Rejected") : item.reviewed ? (zh ? "已审核" : "Reviewed") : (zh ? "待审核" : "Pending review")}
                </StatusBadge>
                <p className="text-xs text-[var(--color-muted)]">{item.request_status ?? (zh ? "未准备" : "Not prepared")}</p>
              </div>
              <div className="text-sm">
                <p>{zh ? "AI 版本" : "AI version"}: {item.generated_version_number ? `v${item.generated_version_number}` : "—"}</p>
                <p className="mt-1">{zh ? "人工批准" : "Human approved"}: {item.approved_human_version_number ? `v${item.approved_human_version_number}` : "—"}</p>
                <p className="mt-1">{zh ? "修改比例" : "Changed"}: {item.human_edit_distance == null ? "—" : `${Math.round(item.human_edit_distance * 100)}%`}</p>
              </div>
              {item.asset_id ? (
                <Link className="button-tertiary text-center" href={`/marketing-content/${item.asset_id}`}>
                  {zh ? "打开审核" : "Open review"}
                </Link>
              ) : (
                <span className="text-sm text-[var(--color-muted)]">{zh ? "等待生成" : "Awaiting generation"}</span>
              )}
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <section className="card p-6">
          <h2 className="text-lg font-semibold">{zh ? "质量汇总" : "Quality summary"}</h2>
          <dl className="mt-4 grid gap-3 sm:grid-cols-2">
            {Object.entries(summary.quality_metric_summary).map(([key, value]) => (
              <div className="rounded-lg bg-[var(--color-surface-subtle)] p-3" key={key}>
                <dt className="text-xs text-[var(--color-muted)]">{key.replaceAll("_", " ")}</dt>
                <dd className="mt-1 font-semibold">{value}</dd>
              </div>
            ))}
            {!Object.keys(summary.quality_metric_summary).length ? <p className="text-sm text-[var(--color-muted)]">{zh ? "准备草稿后显示。" : "Available after drafts are prepared."}</p> : null}
          </dl>
        </section>
        <section className="card p-6">
          <h2 className="text-lg font-semibold">{zh ? "常见人工反馈" : "Common human feedback"}</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {Object.entries(summary.common_feedback_categories).map(([category, count]) => <span className="rounded-full bg-[var(--color-surface-subtle)] px-3 py-2 text-sm" key={category}>{category} · {count}</span>)}
            {!Object.keys(summary.common_feedback_categories).length ? <p className="text-sm text-[var(--color-muted)]">{zh ? "尚无人工反馈。" : "No human feedback yet."}</p> : null}
          </div>
        </section>
      </section>

      <section className="card p-6">
        <h2 className="text-lg font-semibold">{zh ? "最终 GO 标准" : "Final GO criteria"}</h2>
        <ul className="mt-4 grid gap-3 text-sm leading-6 lg:grid-cols-2">
          {criteria(zh).map((item) => <li className="rounded-lg bg-[var(--color-surface-subtle)] p-4" key={item}>□ {item}</li>)}
        </ul>
      </section>
    </div>
  );
}

function Summary({ label, value }: { label: string; value: number }) {
  return <div className="card p-5"><p className="text-xs font-bold uppercase tracking-wide text-[var(--color-muted)]">{label}</p><strong className="mt-2 block text-3xl">{value}</strong></div>;
}

function ReadinessCard({ title, status, detail, zh }: { title: string; status: "ready" | "pending"; detail: string; zh: boolean }) {
  return <section className="card p-5"><div className="flex items-center justify-between gap-3"><h2 className="font-semibold">{title}</h2><StatusBadge tone={status === "ready" ? "success" : "warning"}>{status === "ready" ? (zh ? "就绪" : "Ready") : (zh ? "待完成" : "Pending")}</StatusBadge></div><p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">{detail}</p></section>;
}

function typeLabel(value: string, zh: boolean) {
  const labels: Record<string, [string, string]> = {
    website_article: ["Website Article", "网站文章"],
    tiktok_script: ["TikTok Script", "TikTok 脚本"],
    instagram_reel_script: ["Instagram Reel Script", "Instagram Reel 脚本"],
    facebook_post: ["Facebook Post", "Facebook 帖子"],
    email_draft: ["Email Draft", "邮件草稿"],
  };
  return labels[value]?.[zh ? 1 : 0] ?? value;
}

function criteria(zh: boolean) {
  return zh
    ? ["10 项案例全部完成审核", "不包含不受支持的事实声明", "引用完整率保持 100%", "租户、权限和知识边界测试无失败", "五种内容类型均被人工认为可用", "记录真实人工修改比例", "英文和中文均获接受", "品牌指南已验证或作为已知前提被明确接受", "OpenAI 双案例已验证或明确记录延期原因"]
    : ["All ten cases reviewed", "No unsupported factual claims", "Citation completeness remains 100%", "No tenant, permission, or knowledge-boundary failures", "Human reviewers consider all five content types usable", "Real Human Edit Distance recorded", "English and Chinese both accepted", "Brand Guideline validated or explicitly accepted as a known prerequisite", "Two-case OpenAI comparison completed or deferred with a documented reason"];
}
