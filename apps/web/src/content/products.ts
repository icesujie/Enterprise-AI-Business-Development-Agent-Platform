import type { Locale } from "@/i18n/config";
import {
  getPublishedCmsPage,
  isGovernedUnavailable,
  getPublishedProducts,
  type PublishedCmsPage,
  type PublishedMediaReference,
} from "@/lib/public-content";

export type ProductPriceMode =
  "fixed" | "starting_from" | "range" | "request_quote";

export type ProductRelationship = { label: string; path: string };
export type ProductSpecification = { label: string; value: string };
export type ProductCta = {
  label: string;
  description: string;
  destination: "public_consultation_agent" | "contact_form";
};

export type ProductContent = {
  slug: string;
  path: string;
  locale: Locale;
  title: string;
  summary: string;
  seoTitle: string;
  seoDescription: string;
  skuModel: string;
  category: string;
  brand: string | null;
  shortDescription: string;
  detailedDescription: string[];
  features: string[];
  applications: string[];
  material: string | null;
  dimensions: string | null;
  configuration: string | null;
  specifications: ProductSpecification[];
  priceMode: ProductPriceMode;
  currency: string | null;
  priceMin: string | null;
  priceMax: string | null;
  priceNote: string | null;
  moq: string | null;
  availabilityNote: string | null;
  hero: PublishedMediaReference | null;
  gallery: PublishedMediaReference[];
  drawings: PublishedMediaReference[];
  relatedProducts: ProductRelationship[];
  relatedSolution: ProductRelationship | null;
  relatedIndustry: ProductRelationship | null;
  relatedGuide: ProductRelationship | null;
  relatedProject: ProductRelationship | null;
  inquiryCta: ProductCta;
  quoteCta: ProductCta;
};

type CmsProduct = {
  product_name: string;
  sku_model: string;
  category: string;
  brand: string | null;
  short_description: string;
  detailed_description: string[];
  features: string[];
  applications: string[];
  material: string | null;
  dimensions: string | null;
  configuration: string | null;
  specifications: ProductSpecification[];
  price_mode: ProductPriceMode;
  currency: string | null;
  price_min: string | null;
  price_max: string | null;
  price_note: string | null;
  moq: string | null;
  availability_note: string | null;
  hero_media_asset_id: string | null;
  gallery_media_asset_ids: string[];
  drawing_media_asset_ids: string[];
  related_products: ProductRelationship[];
  related_solution: ProductRelationship | null;
  related_industry: ProductRelationship | null;
  related_guide: ProductRelationship | null;
  related_project: ProductRelationship | null;
  inquiry_cta: ProductCta;
  quote_cta: ProductCta;
};

export async function getPublishedProduct(
  slug: string,
  locale: Locale,
): Promise<ProductContent | null> {
  try {
    const page = await getPublishedCmsPage("product", slug, locale);
    if (isGovernedUnavailable(page)) return null;
    return page ? adaptProduct(page) : null;
  } catch (error) {
    throw error;
  }
}

export async function listPublishedProducts(
  locale: Locale,
): Promise<ProductContent[]> {
  return (await getPublishedProducts(locale)).map(adaptProduct);
}

function adaptProduct(page: PublishedCmsPage): ProductContent {
  const content = page.structured_content as CmsProduct;
  const media = new Map(
    page.media_references.map((reference) => [
      reference.media_asset_id,
      reference,
    ]),
  );
  return {
    slug: page.slug,
    path: page.canonical_path,
    locale: page.locale,
    title: page.title,
    summary: page.summary,
    seoTitle: page.seo_title,
    seoDescription: page.seo_description,
    skuModel: content.sku_model,
    category: content.category,
    brand: content.brand,
    shortDescription: content.short_description,
    detailedDescription: content.detailed_description,
    features: content.features,
    applications: content.applications,
    material: content.material,
    dimensions: content.dimensions,
    configuration: content.configuration,
    specifications: content.specifications,
    priceMode: content.price_mode,
    currency: content.currency,
    priceMin: content.price_min,
    priceMax: content.price_max,
    priceNote: content.price_note,
    moq: content.moq,
    availabilityNote: content.availability_note,
    hero: content.hero_media_asset_id
      ? (media.get(content.hero_media_asset_id) ?? null)
      : null,
    gallery: content.gallery_media_asset_ids.flatMap((id) =>
      media.has(id) ? [media.get(id)!] : [],
    ),
    drawings: content.drawing_media_asset_ids.flatMap((id) =>
      media.has(id) ? [media.get(id)!] : [],
    ),
    relatedProducts: content.related_products,
    relatedSolution: content.related_solution,
    relatedIndustry: content.related_industry,
    relatedGuide: content.related_guide,
    relatedProject: content.related_project,
    inquiryCta: content.inquiry_cta,
    quoteCta: content.quote_cta,
  };
}

export function productPriceLabel(product: ProductContent): string {
  if (product.priceMode === "request_quote")
    return product.locale === "zh-CN" ? "价格请咨询" : "Contact us for pricing";
  const currency = product.currency ?? "";
  const minimum = product.priceMin ?? "";
  if (product.priceMode === "fixed") return `${currency} ${minimum}`.trim();
  if (product.priceMode === "starting_from")
    return `${product.locale === "zh-CN" ? "起价" : "From"} ${currency} ${minimum}`.trim();
  return `${currency} ${minimum}\u2013${product.priceMax ?? ""}`.trim();
}
