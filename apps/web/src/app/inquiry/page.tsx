import { redirect } from "next/navigation";

export default async function InquiryPage({
  searchParams,
}: PageProps<"/inquiry">) {
  const submitted = (await searchParams).submitted === "1";
  redirect(submitted ? "/contact?submitted=1" : "/contact");
}
