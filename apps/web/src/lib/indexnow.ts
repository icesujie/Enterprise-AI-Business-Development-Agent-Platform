import "server-only";

import {
  eligibleIndexNowUrls,
  isIndexNowEnabled,
  type IndexNowCandidate,
} from "@/lib/indexnow-policy";
import { getSiteUrl } from "@/lib/search-foundation";

export type IndexNowResult =
  | { status: "disabled"; submitted: 0 }
  | { status: "not_configured"; submitted: 0 }
  | { status: "no_eligible_urls"; submitted: 0 }
  | { status: "submitted"; submitted: number };

type IndexNowEnvironment = {
  INDEXNOW_ENABLED?: string;
  INDEXNOW_KEY?: string;
  INDEXNOW_KEY_LOCATION?: string;
  INDEXNOW_ENDPOINT?: string;
};

export async function notifyIndexNow(
  candidates: readonly IndexNowCandidate[],
  options: {
    environment?: IndexNowEnvironment;
    fetcher?: typeof fetch;
    action?: "publish" | "remove";
  } = {},
): Promise<IndexNowResult> {
  const environment = options.environment ?? process.env;
  if (!isIndexNowEnabled(environment.INDEXNOW_ENABLED)) {
    return { status: "disabled", submitted: 0 };
  }

  const key = environment.INDEXNOW_KEY?.trim();
  const keyLocation = environment.INDEXNOW_KEY_LOCATION?.trim();
  const site = new URL(getSiteUrl());
  if (
    !key ||
    !/^[A-Za-z0-9-]{8,128}$/.test(key) ||
    !keyLocation ||
    !isSameOriginHttpsUrl(keyLocation, site) ||
    site.hostname === "localhost"
  ) {
    return { status: "not_configured", submitted: 0 };
  }

  const urls = eligibleIndexNowUrls(candidates, options.action);
  if (!urls.length) return { status: "no_eligible_urls", submitted: 0 };

  const endpoint = new URL(
    environment.INDEXNOW_ENDPOINT?.trim() ||
      "https://api.indexnow.org/indexnow",
  );
  if (endpoint.protocol !== "https:") {
    return { status: "not_configured", submitted: 0 };
  }
  const response = await (options.fetcher ?? fetch)(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      host: site.hostname,
      key,
      keyLocation,
      urlList: urls,
    }),
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`IndexNow submission failed (${response.status}).`);
  }
  return { status: "submitted", submitted: urls.length };
}

function isSameOriginHttpsUrl(value: string, site: URL): boolean {
  try {
    const url = new URL(value);
    return url.protocol === "https:" && url.origin === site.origin;
  } catch {
    return false;
  }
}
