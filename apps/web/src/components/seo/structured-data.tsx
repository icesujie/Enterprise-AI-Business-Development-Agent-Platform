import type { StructuredDataNode } from "@/lib/structured-data";

export function StructuredData({ data }: { data: StructuredDataNode }) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: serializeStructuredData(data) }}
    />
  );
}

export function serializeStructuredData(data: StructuredDataNode): string {
  return JSON.stringify(data).replace(/</g, "\\u003c");
}
