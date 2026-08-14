import "server-only";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { DEMO_SESSION_COOKIE, verifyDemoSessionToken } from "@/lib/demo-auth";
import { createClient } from "@/lib/supabase/server";

export type Organization = {
  id: string;
  legal_name: string;
  display_name: string;
  website_url: string | null;
  domain: string | null;
  industry: string | null;
  country_code: string | null;
  city: string | null;
  preferred_language: string | null;
  lifecycle_stage: string;
  owner_membership_id: string | null;
  created_at: string;
  updated_at: string;
  version: number;
  contact_count?: number;
};

export type Contact = {
  id: string;
  organization_id: string | null;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  phone_e164: string | null;
  whatsapp_e164: string | null;
  job_title: string | null;
  preferred_language: string | null;
  marketing_consent_status: string;
  do_not_contact: boolean;
  owner_membership_id: string | null;
  created_at: string;
  updated_at: string;
  version: number;
};

export type Lead = {
  id: string;
  organization_id: string | null;
  contact_id: string | null;
  source_channel: string;
  source_detail: string | null;
  inquiry_summary: string;
  status: string;
  priority: string;
  owner_membership_id: string | null;
  project_country_code: string | null;
  project_city: string | null;
  project_type: string | null;
  expected_capacity: string | null;
  requirements: Record<string, unknown>;
  target_timeline: string | null;
  estimated_value: string | null;
  currency: string | null;
  qualification_score: string | null;
  created_at: string;
  updated_at: string;
  version: number;
};

export type LeadList = { items: Lead[]; next_cursor: string | null };

export type Opportunity = {
  id: string;
  organization_id: string;
  primary_contact_id: string | null;
  source_lead_id: string | null;
  name: string;
  stage: string;
  status: string;
  probability: string;
  estimated_value: string;
  currency: string;
  expected_close_date: string | null;
  requirements: Record<string, unknown>;
  owner_membership_id: string;
  created_at: string;
  updated_at: string;
  version: number;
};

export type OpportunityList = {
  items: Opportunity[];
  next_cursor: string | null;
};

export type Task = {
  id: string;
  lead_id: string | null;
  opportunity_id?: string | null;
  organization_id?: string | null;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  assigned_to: string;
  due_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  version: number;
};

export type Activity = {
  id: string;
  lead_id: string | null;
  opportunity_id?: string | null;
  activity_type: string;
  occurred_at: string;
  subject: string;
  description: string | null;
  actor_membership_id: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type QualificationRun = {
  id: string;
  workflow_type: string;
  status: string;
  lead_id: string | null;
  result: Record<string, unknown> | null;
  provider_type: string | null;
  model_id: string | null;
  started_at: string | null;
  completed_at: string | null;
  error_code: string | null;
  error_message: string | null;
  correlation_id: string | null;
  attempt_count: number;
  max_attempts: number;
  next_retry_at: string | null;
  last_heartbeat_at: string | null;
  created_at: string;
};

export type LeadAssessment = {
  id: string;
  lead_id: string;
  assessment_version: number;
  agent_run_id: string | null;
  score: string;
  qualification_level: "A" | "B" | "C";
  tier: string;
  need_summary: string | null;
  business_summary: string | null;
  qualification: Record<string, unknown>;
  key_qualification_factors: Array<{
    key: string;
    label: string;
    status: string;
  }>;
  recommended_action: string;
  missing_information: string[];
  confidence: string;
  review_status: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
};

export type KnowledgeCollection = {
  id: string;
  domain_key: string;
  collection_key: string;
  name: string;
  description: string | null;
  status: string;
  collection_metadata: Record<string, unknown>;
  document_count: number;
  created_at: string;
  updated_at: string;
};

export type ManagedKnowledgeDocument = {
  id: string;
  tenant_id: string;
  domain_key: string;
  agent_id: string | null;
  collection_id: string;
  collection_name: string;
  title: string;
  document_type: string;
  language: string;
  lifecycle_status: string;
  approval_status: string;
  processing_status: string;
  current_version_number: number;
  document_metadata: Record<string, unknown>;
  approved_by: string | null;
  approved_at: string | null;
  review_note: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

const apiBaseUrl = process.env.API_BASE_URL ?? "http://localhost:8000";

async function authenticationHeaders(): Promise<Record<string, string>> {
  const developmentSubject = process.env.DEVELOPMENT_AUTH_SUBJECT;
  if (developmentSubject) {
    const cookieStore = await cookies();
    const session = cookieStore.get(DEMO_SESSION_COOKIE)?.value;
    if (!(await verifyDemoSessionToken(session))) redirect("/login");
    return { "X-Development-Subject": developmentSubject };
  }

  const supabase = await createClient();
  if (!supabase) redirect("/login");
  const { error: claimsError } = await supabase.auth.getClaims();
  if (claimsError) redirect("/login");
  const { data } = await supabase.auth.getSession();
  if (!data.session?.access_token) redirect("/login");
  return { Authorization: `Bearer ${data.session.access_token}` };
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  const authHeaders = await authenticationHeaders();
  Object.entries(authHeaders).forEach(([name, value]) =>
    headers.set(name, value),
  );
  if (
    init.body &&
    !(init.body instanceof FormData) &&
    !headers.has("Content-Type")
  )
    headers.set("Content-Type", "application/json");
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
  if (!response.ok) {
    const problem = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(
      problem?.detail ?? `API request failed (${response.status})`,
    );
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
