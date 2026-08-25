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
  datePublished?: string;
  dateModified?: string;
  language: Locale;
};

export type FutureCaseStudyStructuredData = FutureArticleStructuredData & {
  industry?: string;
  images?: readonly string[];
};

export type FutureServiceStructuredData = {
  name: string;
  description: string;
  path: string;
  language: Locale;
};

export type FaqStructuredDataItem = {
  question: string;
  answer: string;
};

export type ProductStructuredDataInput = {
  name: string;
  description: string;
  path: string;
  skuModel: string;
  category: string;
  brand: string | null;
  material: string | null;
  images: string[];
  specifications: Array<{ label: string; value: string }>;
  priceMode: "fixed" | "starting_from" | "range" | "request_quote";
  currency: string | null;
  priceMin: string | null;
  priceMax: string | null;
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
    ...(article.datePublished
      ? {
          datePublished: article.datePublished,
          dateModified: article.dateModified ?? article.datePublished,
        }
      : {}),
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
    image: caseStudy.images?.map(absolutePublicUrl),
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

export function buildFaqStructuredData(
  items: readonly FaqStructuredDataItem[],
): StructuredDataNode {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: item.answer,
      },
    })),
  };
}

export function buildProductStructuredData(
  product: ProductStructuredDataInput,
): StructuredDataNode {
  const offer = buildVisibleProductOffer(product);
  return {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.name,
    description: product.description,
    url: absolutePublicUrl(product.path),
    sku: product.skuModel,
    category: product.category,
    ...(product.brand
      ? { brand: { "@type": "Brand", name: product.brand } }
      : {}),
    ...(product.material ? { material: product.material } : {}),
    ...(product.images.length
      ? { image: product.images.map(absolutePublicUrl) }
      : {}),
    ...(product.specifications.length
      ? {
          additionalProperty: product.specifications.map((specification) => ({
            "@type": "PropertyValue",
            name: specification.label,
            value: specification.value,
          })),
        }
      : {}),
    ...(offer ? { offers: offer } : {}),
  };
}

function buildVisibleProductOffer(
  product: ProductStructuredDataInput,
): StructuredDataNode | null {
  if (
    product.priceMode === "request_quote" ||
    !product.currency ||
    !product.priceMin
  )
    return null;
  if (product.priceMode === "fixed") {
    return {
      "@type": "Offer",
      priceCurrency: product.currency,
      price: product.priceMin,
      url: absolutePublicUrl(product.path),
    };
  }
  return {
    "@type": "AggregateOffer",
    priceCurrency: product.currency,
    lowPrice: product.priceMin,
    ...(product.priceMode === "range" && product.priceMax
      ? { highPrice: product.priceMax }
      : {}),
    offerCount: 1,
    url: absolutePublicUrl(product.path),
  };
}
