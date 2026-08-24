import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { CaseStudyPage } from "@/components/marketing/case-study-page";
import { GuidePage } from "@/components/marketing/guide-page";
import { IndustryPage } from "@/components/marketing/industry-page";
import { SolutionPage } from "@/components/marketing/solution-page";
import { StructuredData } from "@/components/seo/structured-data";
import {
  resolvePublishedPublicPage,
  type ResolvedPublicPage,
} from "@/content/published-public-pages";
import type { Locale } from "@/i18n/config";
import { buildPublicRouteMetadata } from "@/lib/seo";
import type { PublicPageType } from "@/lib/public-content";
import {
  buildBreadcrumbStructuredData,
  buildFaqStructuredData,
  buildFutureArticleStructuredData,
  buildFutureCaseStudyStructuredData,
  buildFutureServiceStructuredData,
} from "@/lib/structured-data";

export async function buildPublishedPublicMetadata(
  pageType: PublicPageType,
  slug: string,
  locale: Locale,
): Promise<Metadata> {
  const page = await resolvePublishedPublicPage(pageType, slug, locale);
  if (!page) notFound();
  const firstImage =
    page.pageType === "case_study" ? page.content.images[0] : undefined;
  return buildPublicRouteMetadata(
    {
      title: page.content.metadataTitle,
      description: page.content.metadataDescription,
      path: page.path,
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

export async function PublishedPublicRoute({
  pageType,
  slug,
  locale,
}: {
  pageType: PublicPageType;
  slug: string;
  locale: Locale;
}) {
  const page = await resolvePublishedPublicPage(pageType, slug, locale);
  if (!page) notFound();

  return (
    <>
      <StructuredData data={breadcrumb(page, locale)} />
      <PageStructuredData page={page} locale={locale} />
      {page.pageType === "solution" ? (
        <SolutionPage content={page.content} />
      ) : null}
      {page.pageType === "industry" ? (
        <IndustryPage content={page.content} />
      ) : null}
      {page.pageType === "case_study" ? (
        <CaseStudyPage content={page.content} locale={locale} />
      ) : null}
      {page.pageType === "guide" ? (
        <GuidePage content={page.content} locale={locale} />
      ) : null}
    </>
  );
}

function PageStructuredData({
  page,
  locale,
}: {
  page: ResolvedPublicPage;
  locale: Locale;
}) {
  if (page.pageType === "solution" || page.pageType === "industry") {
    return (
      <StructuredData
        data={buildFutureServiceStructuredData({
          name: page.content.metadataTitle,
          description: page.content.metadataDescription,
          path: page.path,
          language: locale,
        })}
      />
    );
  }
  if (page.pageType === "case_study") {
    return (
      <StructuredData
        data={buildFutureCaseStudyStructuredData({
          headline: page.content.metadataTitle,
          description: page.content.metadataDescription,
          path: page.path,
          datePublished: page.publishedAt,
          dateModified: page.updatedAt,
          language: locale,
          industry: page.content.industry,
          images: page.content.images.map((image) => image.src),
        })}
      />
    );
  }
  return (
    <>
      <StructuredData
        data={buildFutureArticleStructuredData({
          headline: page.content.metadataTitle,
          description: page.content.metadataDescription,
          path: page.path,
          datePublished: page.publishedAt,
          dateModified: page.updatedAt,
          language: locale,
        })}
      />
      {page.content.faqItems.length > 0 ? (
        <StructuredData data={buildFaqStructuredData(page.content.faqItems)} />
      ) : null}
    </>
  );
}

function breadcrumb(page: ResolvedPublicPage, locale: Locale) {
  const section = {
    solution: { en: "Solutions", zh: "解决方案", path: "/solutions" },
    industry: { en: "Industries", zh: "行业", path: "/industries" },
    case_study: { en: "Projects", zh: "项目案例", path: "/projects" },
    guide: null,
  }[page.pageType];
  const items = [{ name: locale === "zh-CN" ? "首页" : "Home", path: "/" }];
  if (section) {
    items.push({
      name: locale === "zh-CN" ? section.zh : section.en,
      path: section.path,
    });
  }
  items.push({ name: page.content.breadcrumbLabel, path: page.path });
  return buildBreadcrumbStructuredData(items);
}
