"use client";

import {
  publicConsultationOpenEvent,
  type ProductConsultationContext,
} from "@/lib/public-consultation-ui";

export function PublicConsultationCta({
  label,
  className = "",
  context,
}: {
  label: string;
  className?: string;
  context?: ProductConsultationContext;
}) {
  return (
    <button
      className={`button-primary ${className}`}
      onClick={() =>
        window.dispatchEvent(
          new CustomEvent(publicConsultationOpenEvent, { detail: context }),
        )
      }
      type="button"
    >
      {label}
    </button>
  );
}
