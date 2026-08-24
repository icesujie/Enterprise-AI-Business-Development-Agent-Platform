import Link from "next/link";

import { CreatePublicContentForm } from "@/components/public-content/public-content-forms";
import { PageHeader } from "@/components/workspace/page-header";
import { getLocale } from "@/i18n/server";

export default async function NewPublicContentPage() {
  const zh = (await getLocale()) === "zh-CN";
  return (
    <div className="mx-auto max-w-5xl space-y-7">
      <Link
        className="text-sm font-semibold text-[var(--color-brand)]"
        href="/public-content"
      >
        ← {zh ? "返回公开内容" : "Back to Public Content"}
      </Link>
      <PageHeader
        eyebrow={zh ? "结构化页面" : "Structured public page"}
        title={zh ? "创建页面草稿" : "Create page draft"}
        description={
          zh
            ? "只接受受控结构化字段，不接受任意 HTML。草稿默认不公开。"
            : "Uses schema-controlled content rather than arbitrary HTML. Drafts are private by default."
        }
      />
      <CreatePublicContentForm zh={zh} />
    </div>
  );
}
