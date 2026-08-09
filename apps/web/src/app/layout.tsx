import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Sari Arta | Commercial Kitchen Engineering",
    template: "%s | Sari Arta",
  },
  description:
    "Commercial kitchen engineering, manufacturing coordination, and local project delivery in Indonesia.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
