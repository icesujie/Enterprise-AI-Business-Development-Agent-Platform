"use server";

import { redirect } from "next/navigation";

import {
  PublicLeadServiceError,
  submitPublicLead,
  type PublicLeadPayload,
} from "@/lib/public-leads";
import { isAcquisitionAttribution } from "@/lib/acquisition-attribution";

export type ConsultationFormState = {
  error: string | null;
};

export async function submitConsultation(
  _previousState: ConsultationFormState,
  formData: FormData,
): Promise<ConsultationFormState> {
  const fullName = value(formData, "full_name");
  const company = value(formData, "company");
  const email = value(formData, "email");
  const projectType = value(formData, "project_type");
  const estimatedSize = value(formData, "estimated_kitchen_size");
  const timeline = value(formData, "expected_timeline");
  const message = value(formData, "message");
  const countryValue = value(formData, "country");

  if (
    !fullName ||
    !company ||
    !email ||
    !projectType ||
    !estimatedSize ||
    !timeline ||
    !message ||
    !countryValue
  ) {
    return { error: "Please complete every required field." };
  }
  if (!/^\S+@\S+\.\S+$/.test(email)) {
    return { error: "Enter a valid work email address." };
  }
  if (message.length < 10) {
    return { error: "Tell us a little more about the project requirements." };
  }
  if (formData.get("contact_consent") !== "on") {
    return {
      error: "Contact consent is required to submit the project brief.",
    };
  }

  const [countryCode, countryName] = splitCountry(countryValue);
  const [firstName, ...remainingName] = fullName.split(/\s+/);
  const attribution = {
    acquisition_source: value(formData, "acquisition_source"),
    landing_path: value(formData, "landing_path"),
    referrer_domain: optional(formData, "referrer_domain"),
  };
  const payload: PublicLeadPayload = {
    contact: {
      first_name: firstName,
      last_name: remainingName.join(" ") || null,
      email,
      phone_e164: optional(formData, "phone_e164"),
      preferred_language: "en",
    },
    organization: {
      name: company,
      website_url: optional(formData, "website_url"),
      country_code: countryCode === "XX" ? null : countryCode,
    },
    inquiry: {
      message: `Project country: ${countryName}\nKitchen size / operating capacity: ${estimatedSize}\n\n${message}`,
      project_country_code: countryCode === "XX" ? null : countryCode,
      project_city: optional(formData, "project_city"),
      project_type: projectType,
      expected_capacity: estimatedSize,
      target_timeline: timeline,
    },
    attribution: {
      source: "website",
      campaign: "m6-public-consultation",
      ...(isAcquisitionAttribution(attribution) ? attribution : {}),
    },
    consent: {
      privacy_policy_version: "mvp-2026-08",
      contact_consent: true,
      marketing_consent: formData.get("marketing_consent") === "on",
    },
  };

  try {
    await submitPublicLead(payload, crypto.randomUUID());
  } catch (error) {
    if (error instanceof PublicLeadServiceError) {
      if (error.status === 429) {
        return {
          error:
            "Too many submissions were received. Please wait a few minutes and try again.",
        };
      }
      if (error.status === 503) {
        return {
          error:
            "The inquiry service is temporarily unavailable. Your form remains on this page so you can try again.",
        };
      }
    }
    return {
      error:
        "We could not submit the project brief. Check the information and try again.",
    };
  }

  redirect("/contact?submitted=1");
}

function value(data: FormData, name: string) {
  return String(data.get(name) ?? "").trim();
}

function optional(data: FormData, name: string) {
  return value(data, name) || null;
}

function splitCountry(valueToSplit: string): [string, string] {
  const [code, ...name] = valueToSplit.split("|");
  return [code.toUpperCase(), name.join("|") || code.toUpperCase()];
}
