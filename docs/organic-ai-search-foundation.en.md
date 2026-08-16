# Organic & AI Search Technical Foundation

**Phase:** 3.2.4A  
**Status:** Implemented technical foundation  
**Primary engineering baseline:** English  
**Chinese translation:** `organic-ai-search-foundation.zh-CN.md`

## 1. Purpose and boundary

Phase 3.2.4A makes the existing public Sari Arta website technically understandable to traditional and AI-powered search systems. It does not generate, approve, or publish marketing content. Phase 3.2 business acceptance remains deferred and production Marketing Content Agent activation remains disabled.

The foundation covers:

- explicit public/private crawl boundaries;
- canonical URLs, server-rendered metadata, and public structured data;
- a maintainable sitemap policy;
- provider-neutral crawler readiness;
- a disabled-by-default IndexNow adapter;
- lightweight search-acquisition attribution that preserves the existing CRM intake path.

## 2. Search trust boundary

| Route class | Examples | Search behavior |
|---|---|---|
| Canonical public pages | `/`, `/solutions`, `/industries`, `/projects`, `/about`, `/contact` | `index, follow`; canonical URL; included in sitemap |
| Future approved public pages | `/solutions/*`, `/industries/*`, `/projects/*`, `/guides/*` | Eligible only when explicitly public and `published` |
| Internal workspace | `/dashboard`, `/leads`, `/opportunities`, `/knowledge`, `/marketing-content` | Excluded from robots and sitemap; `noindex` metadata and `X-Robots-Tag` |
| Authentication and private intake | `/login`, `/inquiry` | Excluded and `noindex` |
| API and unknown routes | `/api/*`, missing pages | Excluded where applicable; normal non-success status for missing routes |

`robots.txt` is crawler guidance, not an authorization control. Authentication, tenant isolation, RBAC, PostgreSQL RLS, and knowledge/content governance remain the security controls.

## 3. Crawlability and indexability

### 3.1 Robots policy

`/robots.txt` contains an explicit common policy for:

- generic crawlers (`*`);
- Googlebot;
- Bingbot;
- OAI-SearchBot.

The named crawler rules currently share the same public/private boundary. This makes review explicit without granting any crawler access to authenticated data. The policy can be changed centrally if business or legal policy later differs by crawler.

### 3.2 Private route defense in depth

Internal routes receive both:

```text
robots meta: noindex, nofollow, noarchive, nosnippet
X-Robots-Tag: noindex, nofollow, noarchive, nosnippet
```

They are also absent from the sitemap. The response header is applied at the Next.js proxy boundary, including redirects and responses that do not render the workspace layout.

### 3.3 Server-rendered public pages

The public pages retain Next.js server-rendered output with metadata emitted in the initial HTML. The implementation does not rely on a browser-only SEO overlay or hidden crawler content.

## 4. Sitemap policy

`/sitemap.xml` currently lists exactly the six canonical public pages. It does not fabricate `lastModified` values.

The shared sitemap builder supports future publication records but includes one only when all conditions are true:

1. the record is explicitly public;
2. the status is `published`;
3. its path is under an approved public prefix;
4. its URL has no query or fragment;
5. it is not an internal route.

Future public content must be connected to this builder only after the exact governed content version has been human-approved and published. Draft, review, archived, private, or internal records must never enter the sitemap.

## 5. Metadata architecture

Each canonical public page has English and Chinese metadata aligned with the visible page purpose:

- a concise page title;
- an original description;
- one absolute canonical URL;
- Open Graph title, description, URL, site identity, and locale;
- language metadata;
- index/follow directives.

The root metadata defines the site name as **Sari Arta** and the positioning as **Indonesia Commercial Kitchen Engineering Partner**. Verification tokens are configuration values, not source-controlled credentials:

```text
GOOGLE_SITE_VERIFICATION
BING_SITE_VERIFICATION
NEXT_PUBLIC_SITE_URL
```

The current website uses a preference cookie for English/Chinese content at the same canonical URL. Therefore, it intentionally does not emit misleading language-alternate URLs. Dedicated locale URLs and `hreflang` may be added later if the public routing strategy changes.

## 6. Structured data

The public marketing layout emits reusable JSON-LD for:

- `Organization`;
- `WebSite`.

Public section pages emit `BreadcrumbList`. Reusable future `Article`, article-based case-study, and `Service` builders are prepared for governed publication paths.

Only facts already represented by approved site content are included. The implementation does not invent addresses, ratings, awards, certifications, customer names, prices, delivery claims, or performance metrics.

Future builders may additionally cover FAQ and more specific public entities after the corresponding public content model exists. `Product` was evaluated but deliberately deferred because the current site is an engineering-services website and has no governed public product-entity or offer model. Structured data must describe the visible page and must not become a separate source of unsupported claims.

## 7. AI-search readiness

The design is provider-neutral. Search systems receive the same visible, factual, server-rendered content and machine-readable identity signals. Readiness depends on:

- consistent organization and service naming;
- clear solution, industry, and project page purpose;
- factual public evidence and provenance;
- canonical URLs and stable page identity;
- crawlable content without crawler-specific hidden text;
- human-governed publication in future phases.

No provider is promised indexing, ranking, citation, or answer inclusion.

## 8. IndexNow readiness

The server-only IndexNow adapter is dormant and is never called by normal page rendering, content generation, or CRM intake. It is disabled unless:

```text
INDEXNOW_ENABLED=true
```

It also requires a valid key, a same-origin HTTPS key location, a non-local production site URL, and an HTTPS endpoint. Candidate URLs pass the same public/published route policy as the sitemap.

Before enabling it in production, an operator must:

1. generate and securely store a production key;
2. expose the required key file at the configured public HTTPS location;
3. verify the production canonical host;
4. connect submission only to an exact, human-approved publication event;
5. monitor failure without blocking publication;
6. document key rotation and disablement.

IndexNow notification does not guarantee crawling or indexing.

## 9. Search console readiness

The project is ready for a future manual onboarding sequence:

1. configure the production HTTPS `NEXT_PUBLIC_SITE_URL`;
2. set the Google Search Console and Bing Webmaster verification tokens in production secrets;
3. deploy and verify the rendered verification metadata;
4. verify domain/property ownership in each provider console;
5. submit the production `/sitemap.xml`;
6. inspect index coverage and crawler responses;
7. keep provider account credentials outside the application.

No search-provider account, credential, or production property was created by this phase.

## 10. Acquisition attribution

The browser records a minimal, session-scoped first-touch classification:

| Classification | Example signal |
|---|---|
| `organic_google` | Google referrer or an explicit organic Google UTM |
| `organic_bing` | Bing referrer or an explicit organic Bing UTM |
| `ai_search` | Recognized AI-search referrer such as ChatGPT, Perplexity, Copilot, or Gemini |
| `social` | Recognized social referrer or social UTM |
| `referral` | Other external referrer |
| `direct` | No eligible external signal |

Only the classification, landing path, and referrer domain are retained. Full referrer URLs, query strings, and search queries are not stored.

The existing business source remains authoritative:

- standard contact form: `website`;
- public assistant lead: `website_ai_assistant`.

Search attribution is stored as supplementary lead requirement metadata. It does not change lead status, ownership, qualification, deduplication, audit behavior, or CRM workflow. This is an attribution foundation, not an analytics platform.

## 11. Security and governance

- Public search visibility never bypasses tenant, RBAC, RLS, agent, knowledge, or content permissions.
- Only public, approved, published content may become future indexable dynamic content.
- Internal pricing, supplier data, private customer data, CRM records, internal SOP, engineering notes, and confidential commercial terms remain forbidden.
- IndexNow is disabled by default and has no automatic trigger.
- Verification tokens and IndexNow keys remain environment-managed secrets/configuration.
- No crawler receives API, CRM, private knowledge, Marketing Workspace, or Agent Playground access.
- Phase 3.2 business-acceptance blockers still prevent production generated-content activation and automated publication.

## 12. Validation and regression coverage

Automated coverage verifies:

- the six canonical sitemap URLs and exclusion of internal paths;
- future sitemap publication filtering;
- generic, Googlebot, Bingbot, and OAI-SearchBot policies;
- private-route `noindex` directives;
- bilingual canonical and Open Graph metadata;
- Organization, WebSite, Breadcrumb, and future Article, case-study, and Service JSON-LD construction;
- safe JSON-LD serialization;
- attribution classification and public-assistant source preservation;
- IndexNow disabled state and eligible URL filtering.

## 13. Production work remaining

Before a production search launch:

- select and configure the final HTTPS canonical domain;
- verify Google Search Console and Bing Webmaster Tools;
- submit and monitor the production sitemap;
- test CDN/WAF behavior for the reviewed crawlers;
- decide whether dedicated locale URLs and `hreflang` are needed;
- approve the first real public content and structured facts;
- complete privacy review for referral attribution;
- decide whether to activate IndexNow and implement its approved publication-event trigger;
- add analytics only under a separate approved measurement scope.

These tasks do not authorize Marketing Content Agent production activation or automatic publication.
