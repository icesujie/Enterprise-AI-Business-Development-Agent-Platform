import type { HTMLAttributes, ReactNode } from "react";

export function SectionContainer({
  children,
  className = "",
  ...props
}: HTMLAttributes<HTMLDivElement> & { children: ReactNode }) {
  return (
    <div
      className={`mx-auto w-full max-w-[1280px] px-5 sm:px-8 lg:px-10 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
