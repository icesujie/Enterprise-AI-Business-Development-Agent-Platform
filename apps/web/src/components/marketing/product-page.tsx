import Image from "next/image";
import Link from "next/link";

import { SectionContainer } from "@/components/layout/section-container";
import { PublicConsultationCta } from "@/components/marketing/public-consultation-cta";
import {
  productPriceLabel,
  type ProductContent,
  type ProductRelationship,
} from "@/content/products";

export function ProductPage({ product }: { product: ProductContent }) {
  const zh = product.locale === "zh-CN";
  const displayedPrice = productPriceLabel(product);
  const consultationContext = {
    source: "product_page" as const,
    productLocale: product.locale,
    productName: product.title,
    productSlug: product.slug,
    skuModel: product.skuModel,
    priceMode: product.priceMode,
    displayedPrice,
  };
  const related = [
    ...product.relatedProducts,
    product.relatedSolution,
    product.relatedIndustry,
    product.relatedGuide,
    product.relatedProject,
  ].filter((entry): entry is ProductRelationship => entry !== null);
  return (
    <>
      <header className="border-b border-[var(--color-line)] bg-[var(--color-surface-subtle)] py-14 sm:py-20">
        <SectionContainer>
          <div className="grid gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
            <div>
              <p className="eyebrow">{product.category}</p>
              <h1 className="section-title mt-5 max-w-3xl">{product.title}</h1>
              <p className="mt-3 text-sm font-semibold text-[var(--color-muted)]">
                {zh ? "型号" : "Model"}: {product.skuModel}
                {product.brand ? ` · ${product.brand}` : ""}
              </p>
              <p className="mt-6 max-w-2xl text-base leading-8 text-[var(--color-muted)]">
                {product.shortDescription}
              </p>
              <p className="mt-6 text-2xl font-semibold text-[var(--color-brand)]">
                {displayedPrice}
              </p>
              {product.priceNote ? (
                <p className="mt-2 max-w-2xl text-xs leading-5 text-[var(--color-muted)]">
                  {product.priceNote}
                </p>
              ) : null}
              <div className="mt-8 flex flex-wrap gap-3">
                <PublicConsultationCta
                  context={consultationContext}
                  label={product.inquiryCta.label}
                />
                <PublicConsultationCta
                  context={consultationContext}
                  label={product.quoteCta.label}
                />
              </div>
            </div>
            <ProductImage product={product} />
          </div>
        </SectionContainer>
      </header>

      <main>
        <section className="bg-white py-16 sm:py-20">
          <SectionContainer>
            <div className="grid gap-12 lg:grid-cols-[1fr_0.9fr]">
              <div>
                <p className="eyebrow">
                  {zh ? "产品概览" : "Product overview"}
                </p>
                <div className="mt-5 space-y-4 text-base leading-8 text-[var(--color-muted)]">
                  {product.detailedDescription.map((paragraph) => (
                    <p key={paragraph}>{paragraph}</p>
                  ))}
                </div>
                <h2 className="mt-10 text-xl font-semibold">
                  {zh ? "主要特点" : "Features"}
                </h2>
                <ul className="mt-5 grid gap-3 sm:grid-cols-2">
                  {product.features.map((feature) => (
                    <li
                      className="rounded-xl bg-[var(--color-surface-subtle)] p-4 text-sm leading-6"
                      key={feature}
                    >
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="card p-6 sm:p-8">
                <h2 className="text-xl font-semibold">
                  {zh ? "产品信息" : "Product information"}
                </h2>
                <dl className="mt-6 divide-y divide-[var(--color-line)] text-sm">
                  <Fact
                    label={zh ? "型号" : "SKU / model"}
                    value={product.skuModel}
                  />
                  <Fact
                    label={zh ? "类别" : "Category"}
                    value={product.category}
                  />
                  <Fact
                    label={zh ? "材质" : "Material"}
                    value={product.material}
                  />
                  <Fact
                    label={zh ? "尺寸" : "Dimensions"}
                    value={product.dimensions}
                  />
                  <Fact
                    label={zh ? "配置" : "Configuration"}
                    value={product.configuration}
                  />
                  <Fact label="MOQ" value={product.moq} />
                  <Fact
                    label={zh ? "供应说明" : "Availability"}
                    value={product.availabilityNote}
                  />
                  {product.specifications.map((specification) => (
                    <Fact
                      key={specification.label}
                      label={specification.label}
                      value={specification.value}
                    />
                  ))}
                </dl>
              </div>
            </div>
          </SectionContainer>
        </section>

        <section className="bg-[var(--color-canvas)] py-16 sm:py-20">
          <SectionContainer>
            <h2 className="section-title">
              {zh ? "适用场景" : "Suitable applications"}
            </h2>
            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {product.applications.map((application) => (
                <article className="card p-6" key={application}>
                  <p className="text-sm leading-7">{application}</p>
                </article>
              ))}
            </div>
          </SectionContainer>
        </section>

        {product.gallery.length || product.drawings.length ? (
          <section className="bg-white py-16 sm:py-20">
            <SectionContainer>
              <h2 className="section-title">
                {zh ? "产品媒体" : "Product media"}
              </h2>
              <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {[...product.gallery, ...product.drawings].map((image) => (
                  <figure
                    className="overflow-hidden rounded-2xl border border-[var(--color-line)] bg-white"
                    key={image.media_asset_id}
                  >
                    <Image
                      alt={image.alt_text}
                      className="h-64 w-full object-cover"
                      height={image.height}
                      src={`/public-media/${image.media_asset_id}`}
                      width={image.width}
                    />
                    {image.caption ? (
                      <figcaption className="p-4 text-xs text-[var(--color-muted)]">
                        {image.caption}
                      </figcaption>
                    ) : null}
                  </figure>
                ))}
              </div>
            </SectionContainer>
          </section>
        ) : null}

        {related.length ? (
          <section className="bg-[var(--color-brand)] py-16 text-white sm:py-20">
            <SectionContainer>
              <h2 className="section-title">
                {zh ? "相关内容" : "Related project information"}
              </h2>
              <div className="mt-8 flex flex-wrap gap-3">
                {related.map((entry) => (
                  <Link
                    className="button-secondary"
                    href={entry.path}
                    key={entry.path}
                  >
                    {entry.label}
                  </Link>
                ))}
              </div>
            </SectionContainer>
          </section>
        ) : null}

        <section className="bg-[var(--color-surface-subtle)] py-16 sm:py-20">
          <SectionContainer>
            <div className="card flex flex-col gap-7 p-7 sm:p-10 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="eyebrow">{zh ? "产品咨询" : "Product inquiry"}</p>
                <h2 className="section-title mt-4">{product.quoteCta.label}</h2>
                <p className="mt-4 max-w-2xl text-sm leading-7 text-[var(--color-muted)]">
                  {product.quoteCta.description}
                </p>
              </div>
              <PublicConsultationCta
                className="shrink-0"
                context={consultationContext}
                label={product.quoteCta.label}
              />
            </div>
          </SectionContainer>
        </section>
      </main>
    </>
  );
}

function ProductImage({ product }: { product: ProductContent }) {
  if (!product.hero)
    return (
      <div className="grid aspect-[4/3] place-items-center rounded-3xl border border-[var(--color-line)] bg-white p-10 text-center text-sm text-[var(--color-muted)]">
        Approved product media will appear here.
      </div>
    );
  return (
    <Image
      alt={product.hero.alt_text}
      className="aspect-[4/3] w-full rounded-3xl border border-[var(--color-line)] object-cover"
      height={product.hero.height}
      priority
      src={`/public-media/${product.hero.media_asset_id}`}
      width={product.hero.width}
    />
  );
}

function Fact({ label, value }: { label: string; value: string | null }) {
  if (!value) return null;
  return (
    <div className="grid gap-2 py-4 sm:grid-cols-[0.42fr_0.58fr]">
      <dt className="font-semibold">{label}</dt>
      <dd className="text-[var(--color-muted)]">{value}</dd>
    </div>
  );
}
