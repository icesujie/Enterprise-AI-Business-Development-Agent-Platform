"use server";

import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

export async function login(formData: FormData) {
  const client = await createClient();
  if (!client)
    throw new Error("Supabase Auth is not configured for this environment.");
  const email = String(formData.get("email") ?? "");
  const password = String(formData.get("password") ?? "");
  const { error } = await client.auth.signInWithPassword({ email, password });
  if (error)
    throw new Error("Sign-in failed. Check your credentials and try again.");
  redirect("/leads");
}
