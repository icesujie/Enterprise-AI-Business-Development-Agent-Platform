import type { MarketingContentVersion } from "@/lib/api";

export function MarketingChannelPreview({
  contentType,
  version,
  zh,
}: {
  contentType: string;
  version: MarketingContentVersion;
  zh: boolean;
}) {
  const body = version.content_body;
  return (
    <section className="card p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">
          {zh ? "渠道预览" : "Channel preview"}
        </h2>
        <span className="status-badge">{contentType.replaceAll("_", " ")}</span>
      </div>
      <div className="mt-5 rounded-xl border border-[var(--color-line)] bg-white p-5">
        {contentType === "website_article" ? <ArticlePreview body={body} zh={zh} /> : null}
        {["tiktok_script", "instagram_reel_script"].includes(contentType) ? (
          <VideoPreview body={body} zh={zh} />
        ) : null}
        {contentType === "facebook_post" ? <FacebookPreview body={body} zh={zh} /> : null}
        {contentType === "email_draft" ? <EmailPreview body={body} zh={zh} /> : null}
        {!knownType(contentType) ? (
          <p className="whitespace-pre-wrap text-sm leading-7">{version.plain_text}</p>
        ) : null}
      </div>
      <ReferencePreview citations={version.citations} zh={zh} />
    </section>
  );
}

function ArticlePreview({ body, zh }: PreviewProps) {
  return (
    <article>
      <p className="eyebrow">{zh ? "网站文章" : "Website article"}</p>
      <h1 className="mt-2 text-2xl font-semibold">{value(body.title)}</h1>
      <p className="mt-3 text-base leading-7 text-[var(--color-muted)]">{value(body.summary)}</p>
      <div className="mt-6 space-y-5">
        {records(body.sections).map((section, index) => (
          <section key={`${value(section.heading)}-${index}`}>
            <h2 className="font-semibold">{value(section.heading)}</h2>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-7">{value(section.body)}</p>
          </section>
        ))}
      </div>
      <Cta value={value(body.call_to_action)} />
    </article>
  );
}

function VideoPreview({ body, zh }: PreviewProps) {
  return (
    <article>
      <p className="eyebrow">{zh ? "短视频脚本" : "Short-form video script"}</p>
      <h1 className="mt-2 text-xl font-semibold">{value(body.title)}</h1>
      <div className="mt-4 rounded-lg bg-[var(--color-brand-soft)] p-4">
        <strong>{zh ? "Hook" : "Hook"}</strong>
        <p className="mt-1">{value(body.hook)}</p>
      </div>
      <div className="mt-5 space-y-4">
        {records(body.scenes).map((scene, index) => (
          <section className="rounded-lg border border-[var(--color-line)] p-4" key={index}>
            <strong>{zh ? `场景 ${index + 1}` : `Scene ${index + 1}`}</strong>
            <PreviewRow label={zh ? "画面方向" : "Visual direction"} text={value(scene.visual)} />
            <PreviewRow label={zh ? "旁白" : "Voiceover"} text={value(scene.voiceover)} />
            <PreviewRow label={zh ? "屏幕文字" : "On-screen text"} text={value(scene.on_screen_text)} />
          </section>
        ))}
      </div>
      {body.caption ? <PreviewRow label="Caption" text={value(body.caption)} /> : null}
      <Cta value={value(body.call_to_action)} />
    </article>
  );
}

function FacebookPreview({ body, zh }: PreviewProps) {
  return (
    <article>
      <p className="eyebrow">Facebook</p>
      <h1 className="mt-2 text-xl font-semibold">{value(body.headline)}</h1>
      <p className="mt-4 whitespace-pre-wrap text-sm leading-7">{value(body.body)}</p>
      <Cta value={value(body.call_to_action)} />
      <p className="mt-4 text-sm font-semibold text-[var(--color-brand)]">
        {strings(body.hashtags).join(" ") || (zh ? "无 Hashtag" : "No hashtags")}
      </p>
    </article>
  );
}

function EmailPreview({ body, zh }: PreviewProps) {
  return (
    <article>
      <PreviewRow label={zh ? "主题" : "Subject"} text={value(body.subject)} />
      <PreviewRow label={zh ? "预览文字" : "Preview text"} text={value(body.preview_text)} />
      <div className="mt-5 border-t border-[var(--color-line)] pt-5">
        <p>{value(body.greeting)}</p>
        {strings(body.body_sections).map((section, index) => (
          <p className="mt-4 whitespace-pre-wrap text-sm leading-7" key={index}>{section}</p>
        ))}
        <Cta value={value(body.call_to_action)} />
        <p className="mt-5">{value(body.closing)}</p>
      </div>
    </article>
  );
}

function ReferencePreview({ citations, zh }: { citations: Array<Record<string, unknown>>; zh: boolean }) {
  return (
    <div className="mt-5 border-t border-[var(--color-line)] pt-5">
      <h3 className="text-sm font-semibold">{zh ? "来源引用" : "Source references"}</h3>
      {citations.length ? citations.map((citation, index) => (
        <p className="mt-2 break-all text-xs text-[var(--color-muted)]" key={String(citation.chunk_id)}>
          [{index + 1}] {value(citation.document_name)} · v{value(citation.document_version)} · chunk {value(citation.chunk_id)}
        </p>
      )) : <p className="mt-2 text-sm text-[var(--color-muted)]">{zh ? "当前版本没有引用。" : "No references on this version."}</p>}
    </div>
  );
}

function Cta({ value: text }: { value: string }) {
  return text ? <div className="mt-6 rounded-lg bg-[var(--color-brand)] px-4 py-3 text-sm font-semibold text-white">{text}</div> : null;
}

function PreviewRow({ label, text }: { label: string; text: string }) {
  return <div className="mt-3"><span className="text-xs font-bold uppercase tracking-wide text-[var(--color-muted)]">{label}</span><p className="mt-1 text-sm leading-6">{text || "—"}</p></div>;
}

type PreviewProps = { body: Record<string, unknown>; zh: boolean };
function value(input: unknown): string { return input == null ? "" : String(input); }
function strings(input: unknown): string[] { return Array.isArray(input) ? input.map(value) : []; }
function records(input: unknown): Array<Record<string, unknown>> { return Array.isArray(input) ? input.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object" && !Array.isArray(item)) : []; }
function knownType(value: string): boolean { return ["website_article", "tiktok_script", "instagram_reel_script", "facebook_post", "email_draft"].includes(value); }
