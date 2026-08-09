import { StatusBadge } from "@/components/ui/status";
import { leadStatusLabels } from "@/lib/workspace-format";

export function LeadStatus({ status }: { status: string }) {
  const tone =
    status === "qualified" || status === "converted"
      ? "success"
      : status === "disqualified"
        ? "danger"
        : status === "qualifying"
          ? "info"
          : status === "nurture"
            ? "warning"
            : "neutral";
  return (
    <StatusBadge tone={tone}>
      {leadStatusLabels[status] ?? status.replaceAll("_", " ")}
    </StatusBadge>
  );
}

export function PriorityStatus({ priority }: { priority: string }) {
  const tone =
    priority === "urgent"
      ? "danger"
      : priority === "high"
        ? "warning"
        : "neutral";
  return <StatusBadge tone={tone}>{capitalize(priority)}</StatusBadge>;
}

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
