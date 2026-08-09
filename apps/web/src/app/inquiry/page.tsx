import Link from "next/link";

import { submitInquiry } from "./actions";

export default async function InquiryPage({
  searchParams,
}: PageProps<"/inquiry">) {
  const submitted = (await searchParams).submitted === "1";
  return (
    <main className="min-h-screen bg-[var(--panel)] px-6 py-12 text-white">
      <div className="mx-auto max-w-3xl">
        <Link href="/leads" className="text-sm font-semibold text-white/65">
          Sari Arta · Business Development
        </Link>
        {submitted ? (
          <section className="mt-20 rounded-3xl bg-white p-10 text-[var(--ink)]">
            <p className="eyebrow">Inquiry received</p>
            <h1 className="mt-3 text-4xl font-semibold">
              Thank you. We&apos;ll follow up soon.
            </h1>
            <p className="mt-4 leading-7 text-[var(--muted)]">
              Your commercial-kitchen project inquiry has been recorded for the
              sales team.
            </p>
          </section>
        ) : (
          <>
            <header className="mt-12">
              <p className="text-sm font-bold uppercase tracking-[0.2em] text-white/55">
                Commercial kitchen engineering
              </p>
              <h1 className="mt-4 text-5xl font-semibold tracking-tight">
                Tell us about your project.
              </h1>
              <p className="mt-5 max-w-2xl text-lg leading-8 text-white/65">
                Share the essentials. Our team will review the requirements
                before making any technical or commercial commitment.
              </p>
            </header>
            <form
              action={submitInquiry}
              className="mt-10 rounded-3xl bg-white p-8 text-[var(--ink)] sm:p-10"
            >
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="First name" name="first_name" required />
                <Field label="Last name" name="last_name" />
                <Field
                  label="Business email"
                  name="email"
                  type="email"
                  required
                />
                <Field label="Phone" name="phone_e164" placeholder="+62…" />
                <Field label="Company" name="organization_name" required />
                <Field label="Website" name="website_url" type="url" />
                <Field label="Country code" name="country_code" maxLength={2} />
                <Field label="Project city" name="project_city" />
                <Field label="Project type" name="project_type" />
                <Field label="Expected capacity" name="expected_capacity" />
                <Field label="Target timeline" name="target_timeline" />
              </div>
              <label className="label">
                Project requirements
                <textarea
                  className="field mt-2 min-h-36 resize-y"
                  name="message"
                  required
                  minLength={10}
                />
              </label>
              <label className="mt-5 flex items-start gap-3 text-sm">
                <input
                  className="mt-1"
                  type="checkbox"
                  name="contact_consent"
                  required
                />
                I agree that Sari Arta may contact me about this inquiry.
              </label>
              <label className="mt-3 flex items-start gap-3 text-sm text-[var(--muted)]">
                <input
                  className="mt-1"
                  type="checkbox"
                  name="marketing_consent"
                />
                I would also like to receive relevant updates.
              </label>
              <button className="button-primary mt-7">Submit inquiry</button>
            </form>
          </>
        )}
      </div>
    </main>
  );
}
function Field({
  label,
  name,
  type = "text",
  ...props
}: {
  label: string;
  name: string;
  type?: string;
  required?: boolean;
  placeholder?: string;
  maxLength?: number;
}) {
  return (
    <label className="label">
      {label}
      <input className="field mt-2" name={name} type={type} {...props} />
    </label>
  );
}
