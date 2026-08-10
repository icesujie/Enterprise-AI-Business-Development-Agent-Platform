export type PlaygroundLocale = "en" | "zh-CN" | "id";
export type PlaygroundDomain =
  "commercial_kitchen" | "laboratory_animal_facility";

export type CommercialKitchenPlaygroundInput = {
  project_type: string | null;
  location: string | null;
  capacity: string | null;
  budget: string | null;
  timeline: string | null;
};

export type IvcPlaygroundInput = {
  organization: string | null;
  facility_type: string | null;
  species_research: string | null;
  capacity: string | null;
  technical_requirements: string | null;
  timeline: string | null;
};

export type PlaygroundRequest = {
  domain: PlaygroundDomain;
  response_locale: PlaygroundLocale;
  commercial_kitchen?: CommercialKitchenPlaygroundInput;
  laboratory_animal_facility?: IvcPlaygroundInput;
};

export type PlaygroundResult = {
  schema_version: "agent_playground_output_v1";
  domain: PlaygroundDomain;
  response_locale: PlaygroundLocale;
  qualification_score: number;
  qualification_level: "A" | "B" | "C";
  business_summary: string;
  missing_information: string[];
  risks: string[];
  recommended_next_actions: string[];
  demo_only: true;
  human_review_required: true;
};

export type PlaygroundRun = {
  id: string;
  workflow_type: string;
  status:
    | "queued"
    | "running"
    | "awaiting_approval"
    | "succeeded"
    | "failed"
    | "cancelled";
  result: PlaygroundResult | null;
  provider_type: string | null;
  error_message: string | null;
  attempt_count: number;
  max_attempts: number;
};

export type PlaygroundRunStart = {
  run_id: string;
  workflow_type: string;
  status: string;
  status_url: string;
  created_at: string;
};
