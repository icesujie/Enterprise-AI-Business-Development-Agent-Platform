import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { privateMetadata } from "@/lib/seo";

export const metadata: Metadata = privateMetadata;

export default async function InquiryPage({
  searchParams,
}: PageProps<"/inquiry">) {
  const submitted = (await searchParams).submitted === "1";
  redirect(submitted ? "/contact?submitted=1" : "/contact");
}
