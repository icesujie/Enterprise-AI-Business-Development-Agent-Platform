import { KnowledgeAssistant } from "@/components/knowledge/knowledge-assistant";
import { PageHeader } from "@/components/workspace/page-header";
import { getLocale } from "@/i18n/server";

export default async function KnowledgeAssistantPage() {
  const zh = (await getLocale()) === "zh-CN";
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Phase 2.6.3 · Read-only grounded answers"
        title={zh ? "企业知识助手" : "Enterprise Knowledge Assistant"}
        description={
          zh
            ? "只根据当前智能体已批准、已发布并已启用的知识回答。不会修改 CRM，也不会执行外部动作。"
            : "Answers only from approved, published, active knowledge available to the selected agent. It cannot modify CRM or perform external actions."
        }
      />
      <KnowledgeAssistant initialLanguage={zh ? "zh-CN" : "en"} />
    </div>
  );
}
