"use client";

export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <div className="card p-10 text-center">
      <p className="eyebrow">Unable to load workspace</p>
      <h1 className="mt-3 text-2xl font-semibold">Something needs attention</h1>
      <p className="mt-3 text-sm text-[var(--muted)]">
        The API may be unavailable or your session may have expired.
      </p>
      <button className="button-primary mt-6" onClick={reset}>
        Try again
      </button>
    </div>
  );
}
