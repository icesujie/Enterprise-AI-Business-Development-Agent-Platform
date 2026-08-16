import {
  absolutePublicUrl,
  isCanonicalPublicPath,
  isEligiblePublishedPublicRoute,
  type PublishedPublicRoute,
} from "@/lib/search-foundation";

export type IndexNowCandidate = Pick<
  PublishedPublicRoute,
  "path" | "status" | "isPublic"
>;

export function isIndexNowEnabled(value: string | undefined): boolean {
  return value === "true";
}

export function eligibleIndexNowUrls(
  candidates: readonly IndexNowCandidate[],
): string[] {
  return candidates
    .filter((candidate) => {
      if (candidate.path.includes("?") || candidate.path.includes("#")) {
        return false;
      }
      if (isCanonicalPublicPath(candidate.path)) {
        return candidate.isPublic && candidate.status === "published";
      }
      return isEligiblePublishedPublicRoute(candidate);
    })
    .map((candidate) => absolutePublicUrl(candidate.path))
    .filter((url, index, urls) => urls.indexOf(url) === index);
}
