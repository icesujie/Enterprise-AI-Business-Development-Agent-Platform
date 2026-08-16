import type { Locale } from "@/i18n/config";
import { absolutePublicUrl, siteIdentity } from "@/lib/search-foundation";

export type StructuredDataNode = Record<string, unknown>;

export type BreadcrumbItem = {
  name: string;
  path: string;
};

export type FutureArticleStructuredData = {
  headline: string;
  description: string;
  path: string;
  datePublished: string;
  dateModified?: string;
  language: Locale;
};

export type FutureCaseStudyStructuredData = FutureArticleStructuredData & {
  industry?: string;
};

export type FutureServiceStructuredData = {
  name: string;
  description: string;
  path: string;
  language: Locale;
};

export function buildSiteStructuredData(locale: Locale): StructuredDataNode {
  const siteUrl = absolutePublicUrl("/");
  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Organization",
        "@id": `${siteUrl}#organization`,
        name: siteIdentity.name,
        url: siteUrl,
        description: siteIdentity.description,
        areaServed: { "@type": "Country", name: "Indonesia" },
        knowsAbout: [
          "Commercial kitchen engineering",
          "School kitchens",
          "Hospital and institutional kitchens",
          "Factory cafeterias",
          "Central kitchens",
        ],
      },
      {
        "@type": "WebSite",
        "@id": `${siteUrl}#website`,
        url: siteUrl,
        name: siteIdentity.name,
        publisher: { "@id": `${siteUrl}#organization` },
        inLanguage: locale,
      },
    ],
  };
}

export function buildBreadcrumbStructuredData(
  items: readonly BreadcrumbItem[],
): StructuredDataNode {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: absolutePublicUrl(item.path),
    })),
  };
}

export function buildFutureArticleStructuredData(
  article: FutureArticleStructuredData,
): StructuredDataNode {
  return {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: article.headline,
    description: article.description,
    url: absolutePublicUrl(article.path),
    datePublished: article.datePublished,
    dateModified: article.dateModified ?? article.datePublished,
    inLanguage: article.language,
    author: { "@id": `${absolutePublicUrl("/")}#organization` },
    publisher: { "@id": `${absolutePublicUrl("/")}#organization` },
  };
}

export function buildFutureCaseStudyStructuredData(
  caseStudy: FutureCaseStudyStructuredData,
): StructuredDataNode {
  return {
    ...buildFutureArticleStructuredData(caseStudy),
    articleSection: caseStudy.industry
      ? ["Case Study", caseStudy.industry]
      : "Case Study",
  };
}

export function buildFutureServiceStructuredData(
  service: FutureServiceStructuredData,
): StructuredDataNode {
  return {
    "@context": "https://schema.org",
    "@type": "Service",
    name: service.name,
    description: service.description,
    url: absolutePublicUrl(service.path),
    inLanguage: service.language,
    provider: { "@id": `${absolutePublicUrl("/")}#organization` },
    areaServed: { "@type": "Country", name: "Indonesia" },
  };
}
