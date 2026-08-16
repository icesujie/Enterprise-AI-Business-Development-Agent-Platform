import "server-only";

import type { AcquisitionAttribution } from "@/lib/acquisition-attribution";

export type PublicLeadPayload = {
  contact: {
    first_name: string;
    last_name: string | null;
    email: string;
    phone_e164: string | null;
    preferred_language: string;
  };
  organization: {
    name: string;
    website_url: string | null;
    country_code: string | null;
  };
  inquiry: {
    message: string;
    project_country_code: string | null;
    project_city: string | null;
    project_type: string;
    facility_type?: string | null;
    expected_capacity: string;
    target_timeline: string;
    budget_range?: string | null;
  };
  attribution: {
    source: "website" | "website_ai_assistant";
    campaign: string;
  } & Partial<AcquisitionAttribution>;
  consent: {
    privacy_policy_version: string;
    contact_consent: true;
    marketing_consent: boolean;
  };
};

export type PublicLeadAccepted = {
  submission_id: string;
  status: "accepted";
  message: string;
  duplicate?: boolean;
};

export class PublicLeadServiceError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

export async function submitPublicLead(
  payload: PublicLeadPayload,
  idempotencyKey: string,
): Promise<PublicLeadAccepted> {
  const apiBaseUrl = process.env.API_BASE_URL ?? "http://localhost:8000";
  const response = await fetch(`${apiBaseUrl}/api/v1/public/lead-submissions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey,
      "X-Site-Token": process.env.PUBLIC_SITE_TOKEN ?? "",
    },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new PublicLeadServiceError(
      response.status,
      `Public lead submission failed (${response.status})`,
    );
  }

  return (await response.json()) as PublicLeadAccepted;
}
