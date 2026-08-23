import type { Metadata } from "next";

import { IndustryPage } from "@/components/marketing/industry-page";
import { StructuredData } from "@/components/seo/structured-data";
import { schoolsIndustry } from "@/content/industry-pages";
import { getLocale } from "@/i18n/server";
import { buildPublicRouteMetadata } from "@/lib/seo";
import {
  buildBreadcrumbStructuredData,
  buildFutureServiceStructuredData,
} from "@/lib/structured-data";

export async function generateMetadata(): Promise<Metadata> {
  const locale = await getLocale();
  const content = schoolsIndustry[locale];
  return buildPublicRouteMetadata(
    {
      title: content.metadataTitle,
      description: content.metadataDescription,
      path: content.path,
    },
    locale,
  );
}

export default async function SchoolsIndustryPage() {
  const locale = await getLocale();
  const content = schoolsIndustry[locale];

  return (
    <>
      <StructuredData
        data={buildBreadcrumbStructuredData([
          { name: locale === "zh-CN" ? "首页" : "Home", path: "/" },
          {
            name: locale === "zh-CN" ? "行业" : "Industries",
            path: "/industries",
          },
          { name: content.breadcrumbLabel, path: content.path },
        ])}
      />
      <StructuredData
        data={buildFutureServiceStructuredData({
          name: content.metadataTitle,
          description: content.metadataDescription,
          path: content.path,
          language: locale,
        })}
      />
      <IndustryPage content={content} />
    </>
  );
}
