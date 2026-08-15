import { KnowledgeSearchTester } from "@/components/knowledge/knowledge-search-tester";
import { PageHeader } from "@/components/workspace/page-header";
import { getLocale } from "@/i18n/server";

export default async function KnowledgeSearchPage() {
  const zh = (await getLocale()) === "zh-CN";
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Phase 2.6.2 · Retrieval evaluation"
        title={zh ? "知识检索测试" : "Knowledge retrieval test"}
        description={
          zh
            ? "检查已治理知识的排序、阈值、引用和权限结果。本页面不生成 AI 回答。"
            : "Inspect ranking, thresholds, citations, and access decisions for governed knowledge. This page does not generate AI answers."
        }
      />
      <KnowledgeSearchTester zh={zh} />
    </div>
  );
}
