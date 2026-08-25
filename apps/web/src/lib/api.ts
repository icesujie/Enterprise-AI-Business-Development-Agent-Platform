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

export type KnowledgeDocumentVersion = {
  id: string;
  version_number: number;
  original_filename: string;
  media_type: string;
  content_sha256: string;
  byte_size: number;
  version_metadata: Record<string, unknown>;
  status: string;
  review_status: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_note: string | null;
  restored_from_version_id: string | null;
  created_from_action: string;
  created_by: string;
  created_at: string;
};

export type KnowledgeDocumentBinding = {
  id: string;
  agent_key: string;
  status: string;
  created_by: string;
  created_at: string;
  updated_by: string | null;
  updated_at: string;
};

export type KnowledgeAuditLog = {
  id: string;
  document_id: string;
  document_version_id: string | null;
  actor_user_id: string;
  actor_display_name: string;
  action: string;
  before_metadata: Record<string, unknown>;
  after_metadata: Record<string, unknown>;
  details: Record<string, unknown>;
  correlation_id: string | null;
  created_at: string;
};

export type CurrentIdentity = {
  user_id: string;
  email: string;
  display_name: string;
  workspace: { id: string; slug: string; name: string };
  membership_id: string;
  role: string;
  permissions: string[];
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
  record_version: number;
  current_version_number: number;
  current_version_id: string | null;
  published_version_id: string | null;
  active_version_id: string | null;
  document_metadata: Record<string, unknown>;
  approved_by: string | null;
  approved_at: string | null;
  review_note: string | null;
  created_by: string;
  updated_by: string | null;
  published_by: string | null;
  published_at: string | null;
  archived_by: string | null;
  archived_at: string | null;
  archive_reason: string | null;
  restore_reason: string | null;
  created_at: string;
  updated_at: string;
  current_version?: KnowledgeDocumentVersion | null;
  bindings?: KnowledgeDocumentBinding[];
};

export type KnowledgeSearchResult = {
  document_name: string;
  document_version: number;
  chunk_content: string;
  page_number: number | null;
  section: string | null;
  metadata: Record<string, unknown>;
  similarity_score: number;
  citation: {
    document_id: string;
    document_name: string;
    document_version_id: string;
    document_version: number;
    chunk_id: string;
    page_number: number | null;
    section: string | null;
    content_sha256: string;
  };
};

export type KnowledgeSearchResponse = {
  evidence_status: "sufficient_candidates" | "insufficient_evidence";
  tenant_id: string;
  agent_id: string;
  language: "en" | "zh-CN" | "id";
  correlation_id: string;
  duration_ms: number;
  similarity_threshold: number;
  minimum_evidence_count: number;
  decision_reason:
    | "meets_minimum_evidence"
    | "below_similarity_threshold"
    | "insufficient_result_count";
  results: KnowledgeSearchResult[];
  below_threshold_results: KnowledgeSearchResult[];
};

export type KnowledgeAssistantEvidence = {
  document_id: string;
  document_name: string;
  document_version_id: string;
  document_version: number;
  page_number: number | null;
  section: string | null;
  chunk_id: string;
  source_metadata: Record<string, unknown>;
  similarity_score: number;
  content: string;
  content_sha256: string;
};

export type KnowledgeAssistantResult = {
  evidence_status: "sufficient" | "insufficient" | "conflicting";
  answer: string;
  citations: Array<
    Omit<KnowledgeAssistantEvidence, "content" | "content_sha256">
  >;
  evidence: KnowledgeAssistantEvidence[];
  conflict_keys: string[];
  retrieved_result_count: number;
  model_provider: string;
  model_id: string;
};

export type KnowledgeAssistantRun = {
  run_id: string;
  workflow_type: "knowledge_assistant";
  status: string;
  correlation_id: string | null;
  provider_type: string | null;
  model_id: string | null;
  duration_ms: number | null;
  result: KnowledgeAssistantResult | null;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
};

export type KnowledgeAssistantRunStart = {
  run_id: string;
  workflow_type: "knowledge_assistant";
  status: string;
  status_url: string;
  correlation_id: string | null;
  created_at: string;
};

export type MarketingContentRequest = {
  id: string;
  tenant_id: string;
  domain_id: string;
  agent_id: string | null;
  requested_by: string;
  content_type: string;
  audience: string;
  language: "en" | "zh-CN";
  channel: string;
  business_objective: string;
  topic: string;
  call_to_action: string;
  campaign_name: string | null;
  constraints: Record<string, unknown>;
  knowledge_collection_ids: string[];
  status: string;
  result_asset_id: string | null;
  created_at: string;
  updated_at: string;
};

export type MarketingContentVersion = {
  id: string;
  tenant_id: string;
  content_asset_id: string;
  version_number: number;
  origin: "human" | "ai_generated" | "rollback";
  content_body: Record<string, unknown>;
  plain_text: string;
  claims: Array<Record<string, unknown>>;
  citations: Array<Record<string, unknown>>;
  generation_run_id: string | null;
  based_on_version_id: string | null;
  content_sha256: string;
  created_by: string;
  created_at: string;
};

export type MarketingContentAsset = {
  id: string;
  tenant_id: string;
  domain_id: string;
  agent_id: string | null;
  request_id: string | null;
  title: string;
  content_type: string;
  audience: string;
  language: "en" | "zh-CN";
  channel: string;
  status: "draft" | "generated" | "review" | "approved" | "archived";
  owner_membership_id: string;
  creator_membership_id: string;
  current_version_id: string | null;
  approved_version_id: string | null;
  record_version: number;
  archived_at: string | null;
  archived_by: string | null;
  archive_reason: string | null;
  created_at: string;
  updated_at: string;
  current_version: MarketingContentVersion | null;
  approved_version: MarketingContentVersion | null;
};

export type MarketingContentDecision = {
  id: string;
  content_asset_id: string;
  content_version_id: string;
  decision_type: "submitted" | "changes_requested" | "approved" | "rejected";
  decided_by: string;
  content_sha256: string;
  comment: string | null;
  created_at: string;
};

export type MarketingContentAuditLog = {
  id: string;
  actor_membership_id: string;
  action: string;
  target_type: string;
  target_id: string;
  content_asset_id: string | null;
  content_version_id: string | null;
  content_request_id: string | null;
  outcome: string;
  before_metadata: Record<string, unknown>;
  after_metadata: Record<string, unknown>;
  details: Record<string, unknown>;
  correlation_id: string | null;
  created_at: string;
};

export type ContentGovernanceCommand = {
  asset: MarketingContentAsset;
  decision: MarketingContentDecision | null;
};

export type MarketingGenerationStart = {
  run_id: string;
  request_id: string;
  workflow_type: "marketing_content_generation";
  status: string;
  status_url: string;
  correlation_id: string | null;
  created_at: string;
};

export type MarketingGenerationRun = {
  run_id: string;
  request_id: string;
  workflow_type: "marketing_content_generation";
  status: string;
  correlation_id: string | null;
  provider: string | null;
  model: string | null;
  evidence_status: "sufficient" | "insufficient" | "conflicting" | null;
  duration_ms: number | null;
  result: null | {
    outcome: "generated" | "insufficient_evidence";
    evidence_status: "sufficient" | "insufficient" | "conflicting";
    message: string;
    asset_id: string | null;
    version_id: string | null;
    content: Record<string, unknown> | null;
    citations: Array<Record<string, unknown>>;
  };
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
};

export type MarketingReviewFeedback = {
  id: string;
  content_asset_id: string;
  content_version_id: string;
  reviewer_membership_id: string;
  content_sha256: string;
  categories: string[];
  note: string | null;
  created_at: string;
};

export type MarketingQualityEvaluation = {
  brand_fit: number;
  audience_fit: number;
  channel_fit: number;
  clarity: number;
  cta_quality: number;
  factual_grounding: number;
  unsupported_claims: number;
  repetition: number;
  content_usefulness: number;
  overall_score: number;
  issues: string[];
};

export type MarketingContentEvaluation = {
  asset_id: string;
  evaluated_version_id: string;
  generation_run_id: string | null;
  generation_outcome: string | null;
  evidence_status: string | null;
  provider: string | null;
  model: string | null;
  quality_evaluation: MarketingQualityEvaluation | null;
  human_edit_distance: number | null;
  generated_version_id: string | null;
  generated_version_number: number | null;
  approved_human_version_id: string | null;
  approved_human_version_number: number | null;
  citations: Array<Record<string, unknown>>;
  latency_ms: number | null;
  token_usage: Record<string, unknown>;
  estimated_cost: string | null;
  correlation_id: string | null;
  feedback: MarketingReviewFeedback[];
};

export type MarketingAcceptanceCase = {
  case_id: string;
  scenario: string;
  content_type: string;
  audience: string;
  language: "en" | "zh-CN";
  channel: string;
  business_objective: string;
  topic: string;
  call_to_action: string;
  request_id: string | null;
  request_status: string | null;
  attempt_count: number;
  asset_id: string | null;
  asset_status: string | null;
  reviewed: boolean;
  approved: boolean;
  rejected: boolean;
  human_edit_distance: number | null;
  generated_version_number: number | null;
  approved_human_version_number: number | null;
  feedback_categories: string[];
  quality_evaluation: MarketingQualityEvaluation | null;
};

export type MarketingAcceptanceDashboard = {
  dataset_version: string;
  configured_provider: string;
  mock_preparation_allowed: boolean;
  cases: MarketingAcceptanceCase[];
  summary: {
    total: number;
    prepared: number;
    reviewed: number;
    approved: number;
    rejected: number;
    average_human_edit_distance: number | null;
    common_feedback_categories: Record<string, number>;
    quality_metric_summary: Record<string, number>;
    brand_guideline_validation: "pending" | "completed";
    brand_guideline_note: string;
    openai_comparison_state: "not_run" | "completed" | "deferred";
    openai_comparison_note: string;
  };
};

export type PublicContentVersion = {
  id: string;
  tenant_id: string;
  public_content_item_id: string;
  version_number: number;
  origin: "human" | "rollback" | string;
  title: string;
  summary: string;
  seo_title: string;
  seo_description: string;
  structured_content: Record<string, unknown>;
  media_references: Array<Record<string, unknown>>;
  source_type: string;
  source_reference_id: string | null;
  source_structuring_run_id: string | null;
  source_candidate_key: string | null;
  source_filename: string | null;
  source_checksum: string | null;
  content_sha256: string;
  based_on_version_id: string | null;
  created_by: string;
  created_at: string;
};

export type PublicContentItem = {
  id: string;
  tenant_id: string;
  page_type: "solution" | "industry" | "case_study" | "guide" | "product";
  slug: string;
  locale: "en" | "zh-CN";
  title: string;
  summary: string;
  seo_title: string;
  seo_description: string;
  canonical_path: string;
  status: "draft" | "review" | "approved" | "published" | "archived";
  is_synthetic: boolean;
  current_version_id: string | null;
  approved_version_id: string | null;
  published_version_id: string | null;
  created_by: string;
  approved_by: string | null;
  published_by: string | null;
  record_version: number;
  created_at: string;
  updated_at: string;
  published_at: string | null;
  archived_at: string | null;
  archived_by: string | null;
  archive_reason: string | null;
  current_version: PublicContentVersion | null;
  approved_version: PublicContentVersion | null;
  published_version: PublicContentVersion | null;
};

export type PublicContentDecision = {
  id: string;
  public_content_item_id: string;
  public_content_version_id: string;
  decision_type: string;
  decided_by: string;
  content_sha256: string;
  comment: string | null;
  created_at: string;
};

export type PublicContentAuditLog = {
  id: string;
  actor_membership_id: string;
  action: string;
  public_content_item_id: string;
  public_content_version_id: string | null;
  before_metadata: Record<string, unknown>;
  after_metadata: Record<string, unknown>;
  details: Record<string, unknown>;
  correlation_id: string | null;
  created_at: string;
};

export type PublicContentGovernanceCommand = {
  item: PublicContentItem;
  decision: PublicContentDecision | null;
  publication: PublicContentPublicationEvent | null;
};

export type PublicContentPublicationEvent = {
  event_id: string;
  tenant_id: string;
  page_type: PublicContentItem["page_type"];
  slug: string;
  locale: PublicContentItem["locale"];
  published_version_id: string;
  canonical_path: string;
  canonical_url: string;
  published_at: string;
};

export type MediaAsset = {
  id: string;
  tenant_id: string;
  media_type: "image";
  original_filename: string;
  mime_type: "image/jpeg" | "image/png" | "image/webp";
  file_size: number;
  checksum: string;
  storage_provider: string;
  width: number;
  height: number;
  title: string;
  alt_text: string;
  caption: string | null;
  visibility: "private" | "public";
  public_use_status:
    "uploaded" | "review" | "approved" | "revoked" | "archived";
  source_type: "manual_upload" | "docx_import" | "pdf_import" | "html_import";
  source_reference_id: string | null;
  uploaded_by: string;
  approved_by: string | null;
  record_version: number;
  created_at: string;
  updated_at: string;
  approved_at: string | null;
  revoked_at: string | null;
  archived_at: string | null;
};

export type MediaAuditLog = {
  id: string;
  media_asset_id: string;
  actor_membership_id: string;
  action: string;
  before_metadata: Record<string, unknown>;
  after_metadata: Record<string, unknown>;
  details: Record<string, unknown>;
  correlation_id: string | null;
  created_at: string;
};

export type PublicContentImportBlock = {
  kind: "heading" | "paragraph" | "list" | "table";
  text: string;
  order: number;
  level: number | null;
  page_number: number | null;
  section_title: string | null;
};

export type PublicContentImport = {
  id: string;
  tenant_id: string;
  source_type: "docx" | "pdf" | "html" | "txt" | "markdown";
  original_filename: string;
  mime_type: string;
  checksum: string;
  file_size: number;
  requested_by: string;
  storage_provider: string;
  processing_status: "uploaded" | "processing" | "completed" | "failed";
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  failure_reason: string | null;
  extraction_metadata: Record<string, unknown>;
  extraction_result: {
    title?: string | null;
    blocks?: PublicContentImportBlock[];
    media?: Array<{
      media_asset_id: string;
      order: number;
      page_number: number | null;
      section_title: string | null;
    }>;
  };
  extracted_media_ids: string[];
};

export type PublicContentStructuringRun = {
  id: string;
  tenant_id: string;
  public_content_import_id: string;
  requested_by: string;
  selected_page_type:
    "solution" | "industry" | "case_study" | "guide" | "product";
  recommended_page_type:
    "solution" | "industry" | "case_study" | "guide" | "product" | null;
  provider: string;
  model: string;
  locale: "en" | "zh-CN";
  status: "running" | "completed" | "failed";
  outcome: "ready" | "requires_human_input" | "insufficient_source" | null;
  result: {
    title?: string | null;
    summary?: string | null;
    seo_title?: string | null;
    seo_description?: string | null;
    content?: Record<string, unknown>;
    cms_structured_content?: Record<string, unknown>;
    multiple_products_detected?: boolean;
    product_candidates?: Array<{
      candidate_key: string;
      slug_suggestion: string;
      title: string | null;
      summary: string | null;
      seo_title: string | null;
      seo_description: string | null;
      content: Record<string, unknown>;
      cms_structured_content: Record<string, unknown>;
      missing_fields: string[];
      media_suggestions: Array<{
        media_asset_id: string;
        role: "hero" | "gallery";
        order: number;
        source_page: number | null;
        source_section: string | null;
      }>;
      evidence: Array<{
        field_path: string;
        import_id: string;
        block_order: number | null;
        source_section: string | null;
        source_page: number | null;
        media_asset_id: string | null;
      }>;
    }>;
    media_suggestions?: Array<{
      media_asset_id: string;
      role: "hero" | "gallery";
      order: number;
      source_page: number | null;
      source_section: string | null;
    }>;
    evidence?: Array<{
      field_path: string;
      import_id: string;
      block_order: number | null;
      source_section: string | null;
      source_page: number | null;
      media_asset_id: string | null;
    }>;
  };
  missing_fields: string[];
  failure_reason: string | null;
  duration_ms: number | null;
  correlation_id: string | null;
};

export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}

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
    throw new ApiRequestError(
      problem?.detail ?? `API request failed (${response.status})`,
      response.status,
    );
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
