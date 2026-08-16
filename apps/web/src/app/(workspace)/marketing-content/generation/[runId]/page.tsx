import Link from "next/link";

import { getMarketingGenerationRun } from "@/app/(workspace)/marketing-content/actions";
import { MarketingGenerationStatus } from "@/components/marketing/marketing-generation-status";
import { PageHeader } from "@/components/workspace/page-header";
import { getLocale } from "@/i18n/server";

export default async function MarketingGenerationPage({ params }: PageProps<"/marketing-content/generation/[runId]">) {
  const { runId } = await params;
  const zh = (await getLocale()) === "zh-CN";
  const run = await getMarketingGenerationRun(runId);
  return <div className="mx-auto max-w-5xl space-y-7">
    <Link className="text-sm font-semibold text-[var(--color-brand)]" href="/marketing-content">← {zh ? "返回营销内容" : "Back to Marketing Content"}</Link>
    <PageHeader eyebrow={zh ? "营销内容智能体" : "Marketing Content Agent"} title={zh ? "受治理的 AI 草稿生成" : "Governed AI draft generation"} description={zh ? "只使用已批准的公开营销知识；所有结果仍需人工审核。" : "Uses only approved public marketing knowledge; every result still requires human review."} />
    <MarketingGenerationStatus run={run} zh={zh} />
  </div>;
}
