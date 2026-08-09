import { Button } from "@/components/ui/button";

export function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="grid min-h-60 place-items-center p-8 text-center">
      <div>
        <span
          className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-[var(--color-success-soft)] font-bold text-[var(--color-success)]"
          aria-hidden
        >
          +
        </span>
        <h3 className="mt-4 font-semibold">{title}</h3>
        <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-[var(--color-muted)]">
          {description}
        </p>
      </div>
    </div>
  );
}

export function LoadingState() {
  return (
    <div className="card animate-pulse p-7" aria-label="Loading content">
      <div className="h-3 w-24 rounded bg-[var(--color-line)]" />
      <div className="mt-4 h-8 w-60 rounded bg-[var(--color-line)]" />
      <div className="mt-7 grid gap-3">
        <div className="h-16 rounded-xl bg-[var(--color-line)]/70" />
        <div className="h-16 rounded-xl bg-[var(--color-line)]/70" />
        <div className="h-16 rounded-xl bg-[var(--color-line)]/70" />
      </div>
    </div>
  );
}

export function ErrorState({ onRetry }: { onRetry?: () => void }) {
  return (
    <div className="card border-[var(--color-danger)]/25 p-8 text-center">
      <p className="eyebrow text-[var(--color-danger)]">Unable to load</p>
      <h2 className="mt-3 text-xl font-semibold">Something needs attention</h2>
      <p className="mt-2 text-sm text-[var(--color-muted)]">
        Try again. If the problem continues, share the correlation ID with
        support.
      </p>
      {onRetry ? (
        <Button className="mt-5" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
    </div>
  );
}
