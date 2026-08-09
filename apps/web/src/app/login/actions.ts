"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import {
  createDemoSessionToken,
  DEMO_SESSION_COOKIE,
  getDemoAuthConfig,
  verifyDemoCredentials,
} from "@/lib/demo-auth";
import { createClient } from "@/lib/supabase/server";

export async function login(formData: FormData) {
  const email = String(formData.get("email") ?? "");
  const password = String(formData.get("password") ?? "");
  if (getDemoAuthConfig()) {
    if (!(await verifyDemoCredentials(email, password))) {
      redirect("/login?error=invalid_credentials");
    }
    const cookieStore = await cookies();
    cookieStore.set(DEMO_SESSION_COOKIE, await createDemoSessionToken(), {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 8,
    });
    redirect("/dashboard");
  }

  const client = await createClient();
  if (!client) redirect("/login?error=auth_unavailable");
  const { error } = await client.auth.signInWithPassword({ email, password });
  if (error) redirect("/login?error=invalid_credentials");
  redirect("/leads");
}

export async function logout() {
  const cookieStore = await cookies();
  if (getDemoAuthConfig()) {
    cookieStore.delete(DEMO_SESSION_COOKIE);
    redirect("/login");
  }
  const client = await createClient();
  if (client) await client.auth.signOut();
  redirect("/login");
}
