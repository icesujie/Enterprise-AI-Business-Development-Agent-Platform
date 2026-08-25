import {
  absolutePublicUrl,
  isCanonicalPublicPath,
  isEligiblePublishedPublicRoute,
  type PublishedPublicRoute,
} from "@/lib/search-foundation";

export type IndexNowCandidate = Pick<
  PublishedPublicRoute,
  "path" | "status" | "isPublic"
> & { wasPublished?: boolean };

export function isIndexNowEnabled(value: string | undefined): boolean {
  return value === "true";
}

export function eligibleIndexNowUrls(
  candidates: readonly IndexNowCandidate[],
  action: "publish" | "remove" = "publish",
): string[] {
  return candidates
    .filter((candidate) => {
      if (candidate.path.includes("?") || candidate.path.includes("#")) {
        return false;
      }
      if (action === "remove") {
        return (
          candidate.isPublic &&
          candidate.wasPublished === true &&
          candidate.status === "archived" &&
          (isCanonicalPublicPath(candidate.path) ||
            isEligiblePublicPath(candidate.path))
        );
      }
      if (isCanonicalPublicPath(candidate.path)) {
        return candidate.isPublic && candidate.status === "published";
      }
      return isEligiblePublishedPublicRoute(candidate);
    })
    .map((candidate) => absolutePublicUrl(candidate.path))
    .filter((url, index, urls) => urls.indexOf(url) === index);
}

function isEligiblePublicPath(path: string): boolean {
  return isEligiblePublishedPublicRoute({
    path,
    status: "published",
    isPublic: true,
  });
}
