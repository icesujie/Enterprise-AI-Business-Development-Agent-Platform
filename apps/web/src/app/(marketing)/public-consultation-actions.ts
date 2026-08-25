"use server";

import { submitPublicLead, type PublicLeadAccepted } from "@/lib/public-leads";
import type { AcquisitionAttribution } from "@/lib/acquisition-attribution";
import type { ProductConsultationContext } from "@/lib/public-consultation-ui";

export type ConsultationLanguage = "en" | "zh-CN";
export type ConsultationField =
  | "facility_type"
  | "project_type"
  | "location"
  | "capacity"
  | "timeline"
  | "budget_range"
  | "contact_name"
  | "company"
  | "email";

export type ConsultationTurnResponse = {
  accepted_value: string;
  assistant_message: string;
  next_field: ConsultationField | null;
  next_prompt: string | null;
  ready_for_consent: boolean;
  provider_type: string;
  correlation_id: string;
};

export async function processConsultationTurn(input: {
  language: ConsultationLanguage;
  field: ConsultationField;
  answer: string;
}): Promise<ConsultationTurnResponse> {
  const apiBaseUrl = process.env.API_BASE_URL ?? "http://localhost:8000";
  const response = await fetch(
    `${apiBaseUrl}/api/v1/public/consultation/turns`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Site-Token": process.env.PUBLIC_SITE_TOKEN ?? "",
      },
      body: JSON.stringify(input),
      cache: "no-store",
    },
  );
  if (!response.ok) {
    const problem = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(problem?.detail ?? "Consultation service is unavailable.");
  }
  return (await response.json()) as ConsultationTurnResponse;
}

export async function createConsultationLead(input: {
  language: ConsultationLanguage;
  values: Record<ConsultationField, string>;
  contactConsent: boolean;
  marketingConsent: boolean;
  attribution?: AcquisitionAttribution;
  productContext?: ProductConsultationContext | null;
}): Promise<PublicLeadAccepted> {
  if (input.contactConsent !== true) {
    throw new Error("Contact consent is required before creating an inquiry.");
  }
  const nameParts = input.values.contact_name.trim().split(/\s+/);
  const firstName = nameParts.shift() ?? input.values.contact_name;
  const lastName = nameParts.join(" ") || null;
  return submitPublicLead(
    {
      contact: {
        first_name: firstName,
        last_name: lastName,
        email: input.values.email,
        phone_e164: null,
        preferred_language: input.language,
      },
      organization: {
        name: input.values.company,
        website_url: null,
        country_code: null,
      },
      inquiry: {
        message: buildSummary(
          input.language,
          input.values,
          input.productContext,
        ),
        project_country_code: null,
        project_city: input.values.location,
        project_type: input.values.project_type,
        facility_type: input.values.facility_type,
        expected_capacity: input.values.capacity,
        target_timeline: input.values.timeline,
        budget_range: input.values.budget_range || null,
        product_context: input.productContext
          ? {
              source: input.productContext.source,
              product_locale: input.productContext.productLocale,
              product_name: input.productContext.productName,
              product_slug: input.productContext.productSlug,
              sku_model: input.productContext.skuModel,
              price_mode: input.productContext.priceMode,
              displayed_price: input.productContext.displayedPrice,
            }
          : null,
      },
      attribution: {
        source: "website_ai_assistant",
        campaign: "phase-3.1-public-consultation-agent",
        ...input.attribution,
      },
      consent: {
        privacy_policy_version: "public-agent-2026-08",
        contact_consent: input.contactConsent,
        marketing_consent: input.marketingConsent,
      },
    },
    crypto.randomUUID(),
  );
}

function buildSummary(
  language: ConsultationLanguage,
  values: Record<ConsultationField, string>,
  productContext?: ProductConsultationContext | null,
) {
  const labels =
    language === "zh-CN"
      ? ["设施", "项目类型", "地点", "规模", "时间", "预算"]
      : [
          "Facility",
          "Project type",
          "Location",
          "Capacity",
          "Timeline",
          "Budget",
        ];
  const data = [
    values.facility_type,
    values.project_type,
    values.location,
    values.capacity,
    values.timeline,
    values.budget_range || (language === "zh-CN" ? "暂未提供" : "Not provided"),
  ];
  const summary = labels
    .map((label, index) => `${label}: ${data[index]}`)
    .join("\n");
  if (!productContext) return summary;
  const product =
    language === "zh-CN"
      ? `产品咨询: ${productContext.productName} (${productContext.skuModel}) · ${productContext.displayedPrice}`
      : `Product inquiry: ${productContext.productName} (${productContext.skuModel}) · ${productContext.displayedPrice}`;
  return `${product}\n${summary}`;
}
