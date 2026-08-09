"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import {
  apiFetch,
  type Contact,
  type Lead,
  type LeadAssessment,
  type Organization,
  type Task,
} from "@/lib/api";

const optional = (formData: FormData, name: string) => {
  const value = String(formData.get(name) ?? "").trim();
  return value || null;
};

export async function createOrganization(formData: FormData) {
  await apiFetch<Organization>("/api/v1/organizations", {
    method: "POST",
    body: JSON.stringify({
      legal_name: String(formData.get("legal_name") ?? ""),
      website_url: optional(formData, "website_url"),
      industry: optional(formData, "industry"),
      country_code: optional(formData, "country_code"),
      city: optional(formData, "city"),
    }),
  });
  revalidatePath("/organizations");
}

export async function createContact(formData: FormData) {
  await apiFetch<Contact>("/api/v1/contacts", {
    method: "POST",
    body: JSON.stringify({
      organization_id: optional(formData, "organization_id"),
      first_name: optional(formData, "first_name"),
      last_name: optional(formData, "last_name"),
      email: optional(formData, "email"),
      phone_e164: optional(formData, "phone_e164"),
      job_title: optional(formData, "job_title"),
      preferred_language: optional(formData, "preferred_language"),
    }),
  });
  revalidatePath("/contacts");
}

export async function createLead(formData: FormData) {
  const lead = await apiFetch<Lead>("/api/v1/leads", {
    method: "POST",
    body: JSON.stringify({
      organization_id: optional(formData, "organization_id"),
      contact_id: optional(formData, "contact_id"),
      source_channel: "manual",
      inquiry_summary: String(formData.get("inquiry_summary") ?? ""),
      priority: String(formData.get("priority") ?? "normal"),
      project_country_code: optional(formData, "project_country_code"),
      project_city: optional(formData, "project_city"),
      project_type: optional(formData, "project_type"),
      expected_capacity: optional(formData, "expected_capacity"),
      target_timeline: optional(formData, "target_timeline"),
    }),
  });
  revalidatePath("/leads");
  redirect(`/leads/${lead.id}`);
}

export async function updateLead(
  leadId: string,
  version: number,
  formData: FormData,
) {
  await apiFetch<Lead>(`/api/v1/leads/${leadId}`, {
    method: "PATCH",
    headers: { "If-Match": `"${version}"` },
    body: JSON.stringify({
      status: String(formData.get("status") ?? "new"),
      priority: String(formData.get("priority") ?? "normal"),
      inquiry_summary: String(formData.get("inquiry_summary") ?? ""),
      project_city: optional(formData, "project_city"),
      project_type: optional(formData, "project_type"),
      expected_capacity: optional(formData, "expected_capacity"),
      target_timeline: optional(formData, "target_timeline"),
    }),
  });
  revalidatePath(`/leads/${leadId}`);
  revalidatePath("/leads");
}

export async function createTask(leadId: string, formData: FormData) {
  const rawDueAt = optional(formData, "due_at");
  await apiFetch<Task>(`/api/v1/leads/${leadId}/tasks`, {
    method: "POST",
    body: JSON.stringify({
      title: String(formData.get("title") ?? ""),
      description: optional(formData, "description"),
      priority: String(formData.get("priority") ?? "normal"),
      due_at: rawDueAt ? new Date(rawDueAt).toISOString() : null,
    }),
  });
  revalidatePath(`/leads/${leadId}`);
  revalidatePath("/tasks");
}

export async function updateTask(
  leadId: string,
  taskId: string,
  version: number,
  status: string,
) {
  await apiFetch<Task>(`/api/v1/tasks/${taskId}`, {
    method: "PATCH",
    headers: { "If-Match": `"${version}"` },
    body: JSON.stringify({ status }),
  });
  revalidatePath(`/leads/${leadId}`);
  revalidatePath("/tasks");
}

export async function createNote(leadId: string, formData: FormData) {
  await apiFetch(`/api/v1/leads/${leadId}/activities`, {
    method: "POST",
    body: JSON.stringify({
      subject: String(formData.get("subject") ?? ""),
      description: String(formData.get("description") ?? ""),
    }),
  });
  revalidatePath(`/leads/${leadId}`);
}

export async function runQualification(leadId: string) {
  await apiFetch(`/api/v1/leads/${leadId}/qualification-runs`, {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify({
      rubric_key: "commercial_kitchen_project_v1",
      language: "en",
    }),
  });
  revalidatePath(`/leads/${leadId}`);
}

export async function reviewQualification(
  leadId: string,
  assessmentId: string,
  decision: "approved" | "rejected",
) {
  await apiFetch<LeadAssessment>(
    `/api/v1/lead-assessments/${assessmentId}/reviews`,
    {
      method: "POST",
      body: JSON.stringify({ decision }),
    },
  );
  revalidatePath(`/leads/${leadId}`);
  revalidatePath("/leads");
}
