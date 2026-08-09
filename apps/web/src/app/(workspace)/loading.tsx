export default function Loading() {
  return (
    <div className="card animate-pulse p-8">
      <div className="h-4 w-28 rounded bg-[var(--line)]" />
      <div className="mt-4 h-9 w-64 rounded bg-[var(--line)]" />
      <div className="mt-8 h-64 rounded-2xl bg-[var(--line)]/70" />
    </div>
  );
}
