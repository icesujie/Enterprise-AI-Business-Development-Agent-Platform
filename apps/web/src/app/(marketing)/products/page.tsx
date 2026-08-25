import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

import { SectionContainer } from "@/components/layout/section-container";
import { StructuredData } from "@/components/seo/structured-data";
import { listPublishedProducts, productPriceLabel } from "@/content/products";
import { getLocale } from "@/i18n/server";
import { buildPublicPageMetadata } from "@/lib/seo";
import { buildBreadcrumbStructuredData } from "@/lib/structured-data";

export async function generateMetadata(): Promise<Metadata> {
  return buildPublicPageMetadata("products", await getLocale());
}

export default async function ProductsPage({
  searchParams,
}: PageProps<"/products">) {
  const [locale, params] = await Promise.all([getLocale(), searchParams]);
  const products = await listPublishedProducts(locale);
  const selected = typeof params.category === "string" ? params.category : "";
  const categories = [
    ...new Set(products.map((product) => product.category)),
  ].sort();
  const visible = selected
    ? products.filter((product) => product.category === selected)
    : products;
  const zh = locale === "zh-CN";
  return (
    <>
      <StructuredData
        data={buildBreadcrumbStructuredData([
          { name: zh ? "首页" : "Home", path: "/" },
          { name: zh ? "产品目录" : "Products", path: "/products" },
        ])}
      />
      <header className="border-b border-[var(--color-line)] bg-[var(--color-surface-subtle)] py-16 sm:py-20">
        <SectionContainer>
          <p className="eyebrow">
            {zh ? "公开产品信息" : "Public product information"}
          </p>
          <h1 className="section-title mt-5">
            {zh ? "商用厨房产品目录" : "Commercial Kitchen Product Catalog"}
          </h1>
          <p className="mt-5 max-w-3xl text-base leading-8 text-[var(--color-muted)]">
            {zh
              ? "查看经过人工审核并发布的产品信息和指示性价格。最终报价由销售人员根据数量、配置及交付地点确认。"
              : "Explore human-reviewed public product information and indicative pricing. Final quotations are confirmed by sales based on quantity, configuration, and delivery location."}
          </p>
        </SectionContainer>
      </header>
      <main className="bg-[var(--color-canvas)] py-14 sm:py-20">
        <SectionContainer>
          {categories.length ? (
            <nav
              className="mb-10 flex flex-wrap gap-3"
              aria-label={zh ? "产品类别" : "Product categories"}
            >
              <Link
                className={!selected ? "button-primary" : "button-tertiary"}
                href="/products"
              >
                {zh ? "全部产品" : "All products"}
              </Link>
              {categories.map((category) => (
                <Link
                  className={
                    selected === category ? "button-primary" : "button-tertiary"
                  }
                  href={`/products?category=${encodeURIComponent(category)}`}
                  key={category}
                >
                  {category}
                </Link>
              ))}
            </nav>
          ) : null}
          {visible.length ? (
            <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
              {visible.map((product) => (
                <article className="card overflow-hidden" key={product.path}>
                  {product.hero ? (
                    <Image
                      alt={product.hero.alt_text}
                      className="aspect-[4/3] w-full object-cover"
                      height={product.hero.height}
                      src={`/public-media/${product.hero.media_asset_id}`}
                      width={product.hero.width}
                    />
                  ) : (
                    <div className="grid aspect-[4/3] place-items-center bg-[var(--color-surface-subtle)] p-8 text-center text-xs text-[var(--color-muted)]">
                      {zh ? "暂无已批准公开图片" : "No approved public image"}
                    </div>
                  )}
                  <div className="p-6">
                    <p className="text-xs font-bold uppercase tracking-wider text-[var(--color-accent)]">
                      {product.category}
                    </p>
                    <h2 className="mt-3 text-xl font-semibold">
                      {product.title}
                    </h2>
                    <p className="mt-2 text-xs text-[var(--color-muted)]">
                      {product.skuModel}
                    </p>
                    <p className="mt-4 line-clamp-3 text-sm leading-7 text-[var(--color-muted)]">
                      {product.shortDescription}
                    </p>
                    <p className="mt-5 font-semibold text-[var(--color-brand)]">
                      {productPriceLabel(product)}
                    </p>
                    <Link className="button-tertiary mt-6" href={product.path}>
                      {zh ? "查看产品" : "View product"}
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="card p-10 text-center text-sm text-[var(--color-muted)]">
              {zh
                ? "当前没有符合条件的已发布产品。"
                : "No published products match this category."}
            </div>
          )}
        </SectionContainer>
      </main>
    </>
  );
}
