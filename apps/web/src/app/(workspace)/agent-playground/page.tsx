import { AgentPlayground } from "@/components/playground/agent-playground";
import { PageHeader } from "@/components/workspace/page-header";

export default function AgentPlaygroundPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Phase 2.3 · Multi-domain demonstration"
        title="Agent Playground"
        description="Compare two business-development agents using structured synthetic project briefs. Playground runs are isolated from CRM records and cannot contact customers or perform external actions."
      />
      <AgentPlayground />
    </div>
  );
}
