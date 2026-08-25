export const publicConsultationOpenEvent = "sari-arta:open-public-consultation";

export type ProductConsultationContext = {
  source: "product_page";
  productLocale: "en" | "zh-CN";
  productName: string;
  productSlug: string;
  skuModel: string;
  priceMode: "fixed" | "starting_from" | "range" | "request_quote";
  displayedPrice: string;
};
