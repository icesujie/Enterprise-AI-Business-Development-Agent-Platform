"use client";

import { useActionState, useEffect, useRef } from "react";

import { FieldGroup, Select, TextArea, TextField } from "@/components/ui/form";
import {
  captureAcquisitionAttribution,
} from "@/lib/acquisition-attribution";

import { submitConsultation } from "./actions";

const countries = [
  ["ID", "Indonesia"],
  ["SG", "Singapore"],
  ["MY", "Malaysia"],
  ["PH", "Philippines"],
  ["TH", "Thailand"],
  ["VN", "Vietnam"],
  ["KH", "Cambodia"],
  ["TL", "Timor-Leste"],
  ["CN", "China"],
  ["IN", "India"],
  ["AU", "Australia"],
  ["AE", "United Arab Emirates"],
  ["SA", "Saudi Arabia"],
  ["XX", "Other / not listed"],
] as const;

export function ConsultationForm() {
  const [state, formAction, pending] = useActionState(submitConsultation, {
    error: null,
  });
  const acquisitionSourceRef = useRef<HTMLInputElement>(null);
  const landingPathRef = useRef<HTMLInputElement>(null);
  const referrerDomainRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const attribution = captureAcquisitionAttribution();
    if (acquisitionSourceRef.current) {
      acquisitionSourceRef.current.value = attribution.acquisition_source;
    }
    if (landingPathRef.current) {
      landingPathRef.current.value = attribution.landing_path;
    }
    if (referrerDomainRef.current) {
      referrerDomainRef.current.value = attribution.referrer_domain ?? "";
    }
  }, []);

  return (
    <form action={formAction} className="card p-6 sm:p-9">
      <input
        type="hidden"
        name="acquisition_source"
        defaultValue="direct"
        ref={acquisitionSourceRef}
      />
      <input
        type="hidden"
        name="landing_path"
        defaultValue="/contact"
        ref={landingPathRef}
      />
      <input
        type="hidden"
        name="referrer_domain"
        defaultValue=""
        ref={referrerDomainRef}
      />
      <div className="border-b border-[var(--color-line)] pb-6">
        <p className="eyebrow">Request kitchen consultation</p>
        <h2 className="mt-4 text-3xl font-semibold tracking-tight">
          Tell us about the operation you are planning.
        </h2>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--color-muted)]">
          Required fields help the team understand project fit before the first
          discussion. Estimates are acceptable.
        </p>
      </div>

      {state.error ? (
        <div
          className="mt-6 rounded-xl border border-[var(--color-danger)]/25 bg-[var(--color-danger-soft)] p-4 text-sm text-[var(--color-danger)]"
          role="alert"
        >
          {state.error}
        </div>
      ) : null}

      <fieldset className="mt-7">
        <legend className="text-sm font-bold">Contact and organization</legend>
        <div className="grid gap-x-5 sm:grid-cols-2">
          <FieldGroup label="Name">
            <TextField
              name="full_name"
              autoComplete="name"
              required
              maxLength={240}
            />
          </FieldGroup>
          <FieldGroup label="Work email" hint="Needed for a reply">
            <TextField
              name="email"
              type="email"
              autoComplete="email"
              required
              maxLength={320}
            />
          </FieldGroup>
          <FieldGroup label="Company / organization">
            <TextField
              name="company"
              autoComplete="organization"
              required
              maxLength={250}
            />
          </FieldGroup>
          <FieldGroup label="Phone / WhatsApp" hint="Optional">
            <TextField
              name="phone_e164"
              type="tel"
              autoComplete="tel"
              placeholder="+62…"
              pattern="\+[1-9][0-9]{6,14}"
              title="Use international format, for example +628123456789"
            />
          </FieldGroup>
          <FieldGroup label="Company website" hint="Optional">
            <TextField
              name="website_url"
              type="url"
              autoComplete="url"
              placeholder="https://"
            />
          </FieldGroup>
        </div>
      </fieldset>

      <fieldset className="mt-9 border-t border-[var(--color-line)] pt-7">
        <legend className="pr-3 text-sm font-bold">Project information</legend>
        <div className="grid gap-x-5 sm:grid-cols-2">
          <FieldGroup label="Country">
            <Select name="country" required defaultValue="">
              <option value="" disabled>
                Select project country
              </option>
              {countries.map(([code, name]) => (
                <option key={code} value={`${code}|${name}`}>
                  {name}
                </option>
              ))}
            </Select>
          </FieldGroup>
          <FieldGroup label="Project city" hint="Optional">
            <TextField name="project_city" maxLength={120} />
          </FieldGroup>
          <FieldGroup label="Project type">
            <Select name="project_type" required defaultValue="">
              <option value="" disabled>
                Select facility type
              </option>
              <option value="school_kitchen">School kitchen</option>
              <option value="hospital_kitchen">Hospital kitchen</option>
              <option value="factory_cafeteria">
                Factory / corporate cafeteria
              </option>
              <option value="central_kitchen">Central kitchen</option>
              <option value="hospitality_kitchen">
                Hotel / hospitality kitchen
              </option>
              <option value="other_commercial_kitchen">
                Other commercial kitchen
              </option>
            </Select>
          </FieldGroup>
          <FieldGroup label="Estimated kitchen size / operating capacity">
            <TextField
              name="estimated_kitchen_size"
              required
              maxLength={120}
              placeholder="e.g. 300 m² or 1,500 meals/day"
            />
          </FieldGroup>
          <FieldGroup label="Expected timeline">
            <TextField
              name="expected_timeline"
              required
              maxLength={100}
              placeholder="e.g. Target opening Q2 2027"
            />
          </FieldGroup>
        </div>
        <FieldGroup label="Project requirements">
          <TextArea
            name="message"
            className="min-h-36 resize-y"
            required
            minLength={10}
            maxLength={9500}
            placeholder="Describe the menu or operation, meal volume, current project stage, available drawings, known equipment needs, and the support you are looking for."
          />
        </FieldGroup>
      </fieldset>

      <div className="mt-7 border-t border-[var(--color-line)] pt-6">
        <label className="flex items-start gap-3 text-sm leading-6">
          <input
            className="mt-1.5 h-4 w-4 accent-[var(--color-brand)]"
            type="checkbox"
            name="contact_consent"
            required
          />
          <span>
            I agree that Sari Arta may use this information to review and
            contact me about this project inquiry.
          </span>
        </label>
        <label className="mt-3 flex items-start gap-3 text-sm leading-6 text-[var(--color-muted)]">
          <input
            className="mt-1.5 h-4 w-4 accent-[var(--color-brand)]"
            type="checkbox"
            name="marketing_consent"
          />
          <span>I would also like to receive relevant business updates.</span>
        </label>
      </div>

      <button
        className="button-primary mt-7 w-full sm:w-auto"
        type="submit"
        disabled={pending}
      >
        {pending ? "Submitting project brief…" : "Submit project brief"}
      </button>
      <p className="mt-4 max-w-2xl text-xs leading-5 text-[var(--color-muted)]">
        Submission creates an inquiry for human review. It does not create a
        quotation, technical approval, price, delivery date, or contractual
        commitment.
      </p>
    </form>
  );
}
