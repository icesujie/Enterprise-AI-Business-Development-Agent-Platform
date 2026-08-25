import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { ProductPage } from "@/components/marketing/product-page";
import { StructuredData } from "@/components/seo/structured-data";
import { getPublishedProduct } from "@/content/products";
import { getLocale } from "@/i18n/server";
import { buildPublicRouteMetadata } from "@/lib/seo";
import {
  buildBreadcrumbStructuredData,
  buildProductStructuredData,
} from "@/lib/structured-data";

export async function generateMetadata({
  params,
}: PageProps<"/products/[slug]">): Promise<Metadata> {
  const [{ slug }, locale] = await Promise.all([params, getLocale()]);
  const product = await getPublishedProduct(slug, locale);
  if (!product) notFound();
  return buildPublicRouteMetadata(
    {
      title: product.seoTitle,
      description: product.seoDescription,
      path: product.path,
      image: product.hero
        ? {
            url: `/public-media/${product.hero.media_asset_id}`,
            width: product.hero.width,
            height: product.hero.height,
            alt: product.hero.alt_text,
          }
        : undefined,
    },
    locale,
  );
}

export default async function ProductDetailPage({
  params,
}: PageProps<"/products/[slug]">) {
  const [{ slug }, locale] = await Promise.all([params, getLocale()]);
  const product = await getPublishedProduct(slug, locale);
  if (!product) notFound();
  const zh = locale === "zh-CN";
  const images = [product.hero, ...product.gallery, ...product.drawings]
    .filter((image) => image !== null)
    .map((image) => `/public-media/${image.media_asset_id}`);
  return (
    <>
      <StructuredData
        data={buildBreadcrumbStructuredData([
          { name: zh ? "首页" : "Home", path: "/" },
          { name: zh ? "产品目录" : "Products", path: "/products" },
          { name: product.title, path: product.path },
        ])}
      />
      <StructuredData
        data={buildProductStructuredData({
          name: product.title,
          description: product.shortDescription,
          path: product.path,
          skuModel: product.skuModel,
          category: product.category,
          brand: product.brand,
          material: product.material,
          images,
          specifications: product.specifications,
          priceMode: product.priceMode,
          currency: product.currency,
          priceMin: product.priceMin,
          priceMax: product.priceMax,
        })}
      />
      <ProductPage product={product} />
    </>
  );
}
