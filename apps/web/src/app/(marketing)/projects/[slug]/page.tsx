import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { CaseStudyPage } from "@/components/marketing/case-study-page";
import { StructuredData } from "@/components/seo/structured-data";
import {
  getPublishedCaseStudy,
  getPublishedCaseStudySlugs,
} from "@/content/case-studies";
import { getLocale } from "@/i18n/server";
import { buildPublicRouteMetadata } from "@/lib/seo";
import {
  buildBreadcrumbStructuredData,
  buildFutureCaseStudyStructuredData,
} from "@/lib/structured-data";

type CaseStudyRouteProps = {
  params: Promise<{ slug: string }>;
};

export const dynamicParams = false;

export function generateStaticParams() {
  return getPublishedCaseStudySlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({
  params,
}: CaseStudyRouteProps): Promise<Metadata> {
  const [{ slug }, locale] = await Promise.all([params, getLocale()]);
  const caseStudy = getPublishedCaseStudy(slug, locale);
  if (!caseStudy) notFound();

  const firstImage = caseStudy.content.images[0];
  return buildPublicRouteMetadata(
    {
      title: caseStudy.content.metadataTitle,
      description: caseStudy.content.metadataDescription,
      path: `/projects/${caseStudy.record.slug}`,
      image: firstImage
        ? {
            url: firstImage.src,
            width: firstImage.width,
            height: firstImage.height,
            alt: firstImage.alt,
          }
        : undefined,
    },
    locale,
  );
}

export default async function PublicCaseStudyPage({
  params,
}: CaseStudyRouteProps) {
  const [{ slug }, locale] = await Promise.all([params, getLocale()]);
  const caseStudy = getPublishedCaseStudy(slug, locale);
  if (!caseStudy || !caseStudy.record.publishedAt) notFound();

  const path = `/projects/${caseStudy.record.slug}`;
  return (
    <>
      <StructuredData
        data={buildBreadcrumbStructuredData([
          { name: locale === "zh-CN" ? "首页" : "Home", path: "/" },
          {
            name: locale === "zh-CN" ? "项目案例" : "Projects",
            path: "/projects",
          },
          { name: caseStudy.content.breadcrumbLabel, path },
        ])}
      />
      <StructuredData
        data={buildFutureCaseStudyStructuredData({
          headline: caseStudy.content.metadataTitle,
          description: caseStudy.content.metadataDescription,
          path,
          datePublished: caseStudy.record.publishedAt,
          dateModified:
            caseStudy.record.updatedAt ?? caseStudy.record.publishedAt,
          language: locale,
          industry: caseStudy.content.industry,
          images: caseStudy.content.images.map((image) => image.src),
        })}
      />
      <CaseStudyPage content={caseStudy.content} locale={locale} />
    </>
  );
}
