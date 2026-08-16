import type { MetadataRoute } from "next";

export const siteIdentity = {
  name: "Sari Arta",
  defaultTitle: "Sari Arta | Commercial Kitchen Engineering Indonesia",
  description:
    "Sari Arta is an Indonesia commercial kitchen engineering partner coordinating design, manufacturing capability, logistics, local installation, and commissioning.",
} as const;

export const publicIndexableRoutes = [
  { path: "/", changeFrequency: "weekly", priority: 1 },
  { path: "/solutions", changeFrequency: "monthly", priority: 0.8 },
  { path: "/industries", changeFrequency: "monthly", priority: 0.8 },
  { path: "/projects", changeFrequency: "monthly", priority: 0.8 },
  { path: "/about", changeFrequency: "monthly", priority: 0.8 },
  { path: "/contact", changeFrequency: "monthly", priority: 0.9 },
] as const satisfies ReadonlyArray<{
  path: string;
  changeFrequency: MetadataRoute.Sitemap[number]["changeFrequency"];
  priority: number;
}>;

export const privateRoutePrefixes = [
  "/api",
  "/dashboard",
  "/leads",
  "/opportunities",
  "/follow-up",
  "/organizations",
  "/contacts",
  "/tasks",
  "/knowledge",
  "/agent-playground",
  "/marketing-content",
  "/login",
  "/inquiry",
] as const;

const futurePublicPrefixes = [
  "/solutions/",
  "/industries/",
  "/projects/",
  "/guides/",
] as const;

export type PublishedPublicRoute = {
  path: string;
  status: "draft" | "review" | "approved" | "published" | "archived";
  isPublic: boolean;
  lastModified?: Date;
  changeFrequency?: MetadataRoute.Sitemap[number]["changeFrequency"];
  priority?: number;
};

export function getSiteUrl(): string {
  const configured = process.env.NEXT_PUBLIC_SITE_URL?.trim();
  return (configured || "http://localhost:3000").replace(/\/$/, "");
}

export function absolutePublicUrl(path: string): string {
  return new URL(normalizePath(path), `${getSiteUrl()}/`).toString();
}

export function isPrivateSearchRoute(pathname: string): boolean {
  const normalized = normalizePath(pathname);
  return privateRoutePrefixes.some(
    (prefix) => normalized === prefix || normalized.startsWith(`${prefix}/`),
  );
}

export function isCanonicalPublicPath(pathname: string): boolean {
  const normalized = normalizePath(pathname);
  return publicIndexableRoutes.some((route) => route.path === normalized);
}

export function isEligiblePublishedPublicRoute(
  route: PublishedPublicRoute,
): boolean {
  if (route.path.includes("?") || route.path.includes("#")) return false;
  const normalized = normalizePath(route.path);
  return (
    route.isPublic &&
    route.status === "published" &&
    !isPrivateSearchRoute(normalized) &&
    futurePublicPrefixes.some((prefix) => normalized.startsWith(prefix))
  );
}

export function buildSitemap(
  futureRoutes: readonly PublishedPublicRoute[] = [],
): MetadataRoute.Sitemap {
  const staticEntries: MetadataRoute.Sitemap = publicIndexableRoutes.map(
    (route) => ({
      url: absolutePublicUrl(route.path),
      changeFrequency: route.changeFrequency,
      priority: route.priority,
    }),
  );
  const dynamicEntries: MetadataRoute.Sitemap = futureRoutes
    .filter(isEligiblePublishedPublicRoute)
    .map((route) => ({
      url: absolutePublicUrl(route.path),
      lastModified: route.lastModified,
      changeFrequency: route.changeFrequency ?? "monthly",
      priority: route.priority ?? 0.7,
    }));
  return [...staticEntries, ...dynamicEntries].filter(
    (entry, index, entries) =>
      entries.findIndex((candidate) => candidate.url === entry.url) === index,
  );
}

function normalizePath(path: string): string {
  const pathname = path.split(/[?#]/, 1)[0] || "/";
  const withSlash = pathname.startsWith("/") ? pathname : `/${pathname}`;
  return withSlash.length > 1 ? withSlash.replace(/\/$/, "") : withSlash;
}
