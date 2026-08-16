import Link from "next/link";

import {
  AiContentRequestForm,
  ManualContentForm,
} from "@/components/marketing/marketing-content-forms";
import { PageHeader } from "@/components/workspace/page-header";
import { getLocale } from "@/i18n/server";

export default async function NewMarketingContentPage() {
  const zh = (await getLocale()) === "zh-CN";
  return (
    <div className="mx-auto max-w-4xl space-y-7">
      <Link
        className="text-sm font-semibold text-[var(--color-brand)]"
        href="/marketing-content"
      >
        ← {zh ? "返回营销内容" : "Back to Marketing Content"}
      </Link>
      <PageHeader
        eyebrow={zh ? "营销内容创建" : "Marketing content creation"}
        title={zh ? "创建受治理的营销草稿" : "Create a governed marketing draft"}
        description={
          zh
            ? "可以使用已批准公开知识生成 AI 草稿，也可以人工创建。所有版本不可变，后续修改会创建后继版本。"
            : "Generate from approved public knowledge or create manually. Every version is immutable and later edits create successors."
        }
      />
      <AiContentRequestForm
        zh={zh}
        requestKey={`ai-request-${crypto.randomUUID()}`}
        generationKey={`ai-generation-${crypto.randomUUID()}`}
      />
      <div className="flex items-center gap-4 text-xs font-semibold uppercase tracking-widest text-[var(--color-muted)]">
        <span className="h-px flex-1 bg-[var(--color-line)]" />
        {zh ? "或人工创建" : "or create manually"}
        <span className="h-px flex-1 bg-[var(--color-line)]" />
      </div>
      <ManualContentForm
        zh={zh}
        requestKey={`request-${crypto.randomUUID()}`}
        assetKey={`asset-${crypto.randomUUID()}`}
      />
    </div>
  );
}
