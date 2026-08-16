export const acquisitionSources = [
  "organic_google",
  "organic_bing",
  "ai_search",
  "direct",
  "social",
  "referral",
] as const;

export type AcquisitionSource = (typeof acquisitionSources)[number];

export type AcquisitionAttribution = {
  acquisition_source: AcquisitionSource;
  landing_path: string;
  referrer_domain: string | null;
};

const storageKey = "sari-arta-acquisition-attribution-v1";

const aiSearchDomains = [
  "chatgpt.com",
  "openai.com",
  "perplexity.ai",
  "copilot.microsoft.com",
  "gemini.google.com",
] as const;
const socialDomains = [
  "facebook.com",
  "instagram.com",
  "tiktok.com",
  "linkedin.com",
  "youtube.com",
] as const;

export function captureAcquisitionAttribution(): AcquisitionAttribution {
  const existing = readStoredAttribution();
  if (existing) return existing;
  const query = new URLSearchParams(window.location.search);
  const rawReferrerDomain = safeDomain(document.referrer);
  const referrerDomain =
    rawReferrerDomain === window.location.hostname.toLowerCase()
      ? null
      : rawReferrerDomain;
  const attribution = {
    acquisition_source: classifyAcquisitionSource(query, referrerDomain),
    landing_path: normalizeLandingPath(window.location.pathname),
    referrer_domain: referrerDomain,
  } satisfies AcquisitionAttribution;
  window.sessionStorage.setItem(storageKey, JSON.stringify(attribution));
  return attribution;
}

export function classifyAcquisitionSource(
  query: URLSearchParams,
  referrerDomain: string | null,
): AcquisitionSource {
  const source = query.get("utm_source")?.toLowerCase() ?? "";
  const medium = query.get("utm_medium")?.toLowerCase() ?? "";
  if (source.includes("google") && !isPaidMedium(medium)) {
    return "organic_google";
  }
  if (source.includes("bing") && !isPaidMedium(medium)) {
    return "organic_bing";
  }
  if (
    source.includes("chatgpt") ||
    source.includes("ai_search") ||
    source.includes("perplexity") ||
    matchesDomain(referrerDomain, aiSearchDomains)
  ) {
    return "ai_search";
  }
  if (
    medium === "social" ||
    source.includes("social") ||
    matchesDomain(referrerDomain, socialDomains)
  ) {
    return "social";
  }
  if (!referrerDomain) return "direct";
  if (matchesDomain(referrerDomain, ["google.com"])) return "organic_google";
  if (matchesDomain(referrerDomain, ["bing.com"])) return "organic_bing";
  return "referral";
}

export function isAcquisitionAttribution(
  value: unknown,
): value is AcquisitionAttribution {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<AcquisitionAttribution>;
  return (
    acquisitionSources.includes(candidate.acquisition_source as AcquisitionSource) &&
    typeof candidate.landing_path === "string" &&
    (candidate.referrer_domain === null ||
      typeof candidate.referrer_domain === "string")
  );
}

function readStoredAttribution(): AcquisitionAttribution | null {
  try {
    const value = window.sessionStorage.getItem(storageKey);
    if (!value) return null;
    const parsed: unknown = JSON.parse(value);
    return isAcquisitionAttribution(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

function safeDomain(value: string): string | null {
  if (!value) return null;
  try {
    return new URL(value).hostname.toLowerCase().replace(/^www\./, "");
  } catch {
    return null;
  }
}

function matchesDomain(
  domain: string | null,
  candidates: readonly string[],
): boolean {
  return Boolean(
    domain &&
      candidates.some(
        (candidate) => domain === candidate || domain.endsWith(`.${candidate}`),
      ),
  );
}

function isPaidMedium(medium: string): boolean {
  return ["cpc", "ppc", "paid", "paid_search", "display"].includes(medium);
}

function normalizeLandingPath(path: string): string {
  if (!path.startsWith("/")) return "/";
  return path.slice(0, 500) || "/";
}
