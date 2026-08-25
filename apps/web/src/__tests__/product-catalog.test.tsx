import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import ProductDetailPage, {
  generateMetadata,
} from "@/app/(marketing)/products/[slug]/page";
import ProductsPage from "@/app/(marketing)/products/page";
import { productPriceLabel, type ProductContent } from "@/content/products";
import type { PublishedCmsPage } from "@/lib/public-content";
import { publicConsultationOpenEvent } from "@/lib/public-consultation-ui";
import { buildProductStructuredData } from "@/lib/structured-data";

const { getPublishedCmsPageMock, getPublishedProductsMock } = vi.hoisted(
  () => ({
    getPublishedCmsPageMock: vi.fn(),
    getPublishedProductsMock: vi.fn(),
  }),
);

vi.mock("@/i18n/server", () => ({ getLocale: vi.fn(async () => "en") }));
vi.mock("@/lib/public-content", () => ({
  getPublishedCmsPage: getPublishedCmsPageMock,
  getPublishedProducts: getPublishedProductsMock,
  isGovernedUnavailable: (value: unknown) =>
    typeof value === "object" &&
    value !== null &&
    "state" in value &&
    value.state === "governed_unavailable",
}));
vi.mock("next/navigation", () => ({
  notFound: vi.fn(() => {
    throw new Error("NEXT_NOT_FOUND");
  }),
}));

beforeEach(() => {
  getPublishedCmsPageMock.mockResolvedValue(productFixture());
  getPublishedProductsMock.mockResolvedValue([productFixture()]);
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

test("renders only catalog records supplied by the published Product boundary", async () => {
  render(
    await ProductsPage({
      params: Promise.resolve({}),
      searchParams: Promise.resolve({}),
    }),
  );
  expect(
    screen.getByRole("heading", { name: "Commercial Kitchen Product Catalog" }),
  ).toBeDefined();
  expect(
    screen.getByRole("heading", { name: "Stainless Preparation Table" }),
  ).toBeDefined();
  expect(screen.getByText("USD 180.00")).toBeDefined();
  expect(getPublishedProductsMock).toHaveBeenCalledWith("en");
});

test("renders Product metadata, structured data and safe consultation context", async () => {
  const metadata = await generateMetadata({
    params: Promise.resolve({ slug: "stainless-preparation-table" }),
    searchParams: Promise.resolve({}),
  });
  expect(metadata.alternates).toEqual({
    canonical: expect.stringMatching(
      /\/products\/stainless-preparation-table$/,
    ),
  });

  let detail: unknown;
  window.addEventListener(
    publicConsultationOpenEvent,
    (event) => {
      detail = (event as CustomEvent<unknown>).detail;
    },
    { once: true },
  );
  render(
    await ProductDetailPage({
      params: Promise.resolve({ slug: "stainless-preparation-table" }),
      searchParams: Promise.resolve({}),
    }),
  );
  expect(
    screen.getByRole("heading", {
      level: 1,
      name: "Stainless Preparation Table",
    }),
  ).toBeDefined();
  fireEvent.click(
    screen.getAllByRole("button", { name: "Request a Quote" })[0],
  );
  expect(detail).toEqual({
    source: "product_page",
    productLocale: "en",
    productName: "Stainless Preparation Table",
    productSlug: "stainless-preparation-table",
    skuModel: "PT-180",
    priceMode: "fixed",
    displayedPrice: "USD 180.00",
  });

  const structured = buildProductStructuredData({
    name: "Stainless Preparation Table",
    description: "Approved public description.",
    path: "/products/stainless-preparation-table",
    skuModel: "PT-180",
    category: "Preparation Equipment",
    brand: null,
    material: "Stainless steel",
    images: [],
    specifications: [{ label: "Material", value: "Stainless steel" }],
    priceMode: "fixed",
    currency: "USD",
    priceMin: "180.00",
    priceMax: null,
  });
  expect(structured).toEqual(
    expect.objectContaining({
      "@type": "Product",
      sku: "PT-180",
      offers: expect.objectContaining({
        price: "180.00",
        priceCurrency: "USD",
      }),
    }),
  );
  expect(structured).not.toHaveProperty("aggregateRating");
  expect(structured).not.toHaveProperty("review");
});

test("renders every governed indicative pricing mode without calculating prices", () => {
  const product = (
    priceMode: ProductContent["priceMode"],
    priceMin: string | null,
    priceMax: string | null = null,
  ) =>
    ({
      locale: "en",
      priceMode,
      currency: priceMin ? "USD" : null,
      priceMin,
      priceMax,
    }) as ProductContent;

  expect(productPriceLabel(product("fixed", "180.00"))).toBe("USD 180.00");
  expect(productPriceLabel(product("starting_from", "280.00"))).toBe(
    "From USD 280.00",
  );
  expect(productPriceLabel(product("range", "280.00", "350.00"))).toBe(
    "USD 280.00\u2013350.00",
  );
  expect(productPriceLabel(product("request_quote", null))).toBe(
    "Contact us for pricing",
  );

  const requestQuoteStructured = buildProductStructuredData({
    name: "Request-quote fixture",
    description: "Visible approved description.",
    path: "/products/request-quote-fixture",
    skuModel: "RQ-01",
    category: "Fixture",
    brand: null,
    material: null,
    images: [],
    specifications: [],
    priceMode: "request_quote",
    currency: null,
    priceMin: null,
    priceMax: null,
  });
  expect(requestQuoteStructured).not.toHaveProperty("offers");
});

function productFixture(): PublishedCmsPage {
  return {
    page_type: "product",
    slug: "stainless-preparation-table",
    locale: "en",
    title: "Stainless Preparation Table",
    summary: "Approved public product summary.",
    seo_title: "Stainless Preparation Table",
    seo_description: "Approved public Product metadata.",
    canonical_path: "/products/stainless-preparation-table",
    structured_content: {
      product_name: "Stainless Preparation Table",
      sku_model: "PT-180",
      category: "Preparation Equipment",
      brand: null,
      short_description: "Approved public product description.",
      detailed_description: ["Approved factual product details."],
      features: ["Approved public feature"],
      applications: ["Commercial kitchen preparation areas"],
      material: "Stainless steel",
      dimensions: null,
      configuration: null,
      specifications: [{ label: "Material", value: "Stainless steel" }],
      price_mode: "fixed",
      currency: "USD",
      price_min: "180.00",
      price_max: null,
      price_note: "Final quotation depends on quantity and configuration.",
      moq: null,
      availability_note: null,
      hero_media_asset_id: null,
      gallery_media_asset_ids: [],
      drawing_media_asset_ids: [],
      related_products: [],
      related_solution: null,
      related_industry: null,
      related_guide: null,
      related_project: null,
      inquiry_cta: {
        label: "Ask About This Product",
        description: "Discuss the product with the Sari Arta team.",
        destination: "public_consultation_agent",
      },
      quote_cta: {
        label: "Request a Quote",
        description: "Share quantity and configuration for human follow-up.",
        destination: "public_consultation_agent",
      },
    },
    media_references: [],
    published_at: "2026-08-24T10:00:00Z",
    version_created_at: "2026-08-24T09:00:00Z",
  };
}
