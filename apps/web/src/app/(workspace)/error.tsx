"use client";

import { ErrorState } from "@/components/workspace/states";

export default function ErrorPage({ reset }: { reset: () => void }) {
  return <ErrorState onRetry={reset} />;
}
