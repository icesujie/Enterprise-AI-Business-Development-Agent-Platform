import { StatusBadge } from "@/components/ui/status";

export function WorkspaceTopbar() {
  return (
    <header className="flex min-h-16 items-center justify-between gap-4 border-b border-[var(--color-line)] bg-white px-5 sm:px-8">
      <div>
        <p className="text-xs font-semibold text-[var(--color-muted)]">
          Workspace
        </p>
        <p className="text-sm font-bold">Sari Arta Indonesia</p>
      </div>
      <div className="flex items-center gap-3">
        <StatusBadge tone="success">Preview ready</StatusBadge>
        <span
          className="grid h-9 w-9 place-items-center rounded-full bg-[var(--color-brand)] text-xs font-bold text-white"
          aria-label="Signed in user"
        >
          SA
        </span>
      </div>
    </header>
  );
}
