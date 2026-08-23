"use client";

import { publicConsultationOpenEvent } from "@/lib/public-consultation-ui";

export function PublicConsultationCta({
  label,
  className = "",
}: {
  label: string;
  className?: string;
}) {
  return (
    <button
      className={`button-primary ${className}`}
      onClick={() =>
        window.dispatchEvent(new Event(publicConsultationOpenEvent))
      }
      type="button"
    >
      {label}
    </button>
  );
}
