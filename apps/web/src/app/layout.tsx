import type { Metadata } from "next";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "Sari Arta | Commercial Kitchen Engineering Indonesia",
    template: "%s | Sari Arta",
  },
  description:
    "Sari Arta is an Indonesia commercial kitchen engineering partner coordinating kitchen design, China-based manufacturing capability, logistics, local installation, and commissioning.",
  openGraph: {
    type: "website",
    siteName: "Sari Arta",
    title: "Sari Arta | Commercial Kitchen Engineering Indonesia",
    description:
      "Commercial kitchen design, manufacturing coordination, and local project delivery for institutional and industrial operations in Indonesia.",
    url: "/",
    images: [
      {
        url: "/sari-arta-social-card.png",
        width: 1730,
        height: 909,
        alt: "Sari Arta commercial kitchen engineering and delivery model",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Sari Arta | Commercial Kitchen Engineering Indonesia",
    description:
      "Commercial kitchen design, manufacturing coordination, and local project delivery in Indonesia.",
    images: ["/sari-arta-social-card.png"],
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
