"use server";

import { redirect } from "next/navigation";

export async function submitInquiry(formData: FormData) {
  if (formData.get("contact_consent") !== "on") {
    throw new Error("Contact consent is required to submit an inquiry.");
  }
  const apiBaseUrl = process.env.API_BASE_URL ?? "http://localhost:8000";
  const response = await fetch(`${apiBaseUrl}/api/v1/public/lead-submissions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": crypto.randomUUID(),
      "X-Site-Token": process.env.PUBLIC_SITE_TOKEN ?? "",
    },
    body: JSON.stringify({
      contact: {
        first_name: value(formData, "first_name"),
        last_name: value(formData, "last_name"),
        email: value(formData, "email"),
        phone_e164: optional(formData, "phone_e164"),
        preferred_language: "en",
      },
      organization: {
        name: value(formData, "organization_name"),
        website_url: optional(formData, "website_url"),
        country_code: optional(formData, "country_code"),
      },
      inquiry: {
        message: value(formData, "message"),
        project_country_code: optional(formData, "country_code"),
        project_city: optional(formData, "project_city"),
        project_type: optional(formData, "project_type"),
        expected_capacity: optional(formData, "expected_capacity"),
        target_timeline: optional(formData, "target_timeline"),
      },
      attribution: { source: "website", campaign: "m3-public-form" },
      consent: {
        privacy_policy_version: "mvp-2026-08",
        contact_consent: true,
        marketing_consent: formData.get("marketing_consent") === "on",
      },
    }),
    cache: "no-store",
  });
  if (!response.ok)
    throw new Error("We could not submit your inquiry. Please try again.");
  redirect("/inquiry?submitted=1");
}
const value = (data: FormData, name: string) =>
  String(data.get(name) ?? "").trim();
const optional = (data: FormData, name: string) => value(data, name) || null;
