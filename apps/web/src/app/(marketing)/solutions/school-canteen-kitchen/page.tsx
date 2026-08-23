import type { Metadata } from "next";

import { SolutionPage } from "@/components/marketing/solution-page";
import { StructuredData } from "@/components/seo/structured-data";
import { schoolCanteenSolution } from "@/content/solution-pages";
import { getLocale } from "@/i18n/server";
import { buildPublicRouteMetadata } from "@/lib/seo";
import {
  buildBreadcrumbStructuredData,
  buildFutureServiceStructuredData,
} from "@/lib/structured-data";

export async function generateMetadata(): Promise<Metadata> {
  const locale = await getLocale();
  const content = schoolCanteenSolution[locale];
  return buildPublicRouteMetadata(
    {
      title: content.metadataTitle,
      description: content.metadataDescription,
      path: content.path,
    },
    locale,
  );
}

export default async function SchoolCanteenKitchenPage() {
  const locale = await getLocale();
  const content = schoolCanteenSolution[locale];

  return (
    <>
      <StructuredData
        data={buildBreadcrumbStructuredData([
          { name: locale === "zh-CN" ? "首页" : "Home", path: "/" },
          {
            name: locale === "zh-CN" ? "解决方案" : "Solutions",
            path: "/solutions",
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
      <SolutionPage content={content} />
    </>
  );
}
