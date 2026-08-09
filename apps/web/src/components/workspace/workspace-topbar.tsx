import { logout } from "@/app/login/actions";
import { LanguageSwitcher } from "@/components/i18n/language-switcher";
import { StatusBadge } from "@/components/ui/status";
import type { Messages } from "@/i18n/messages";

export function WorkspaceTopbar({ copy }: { copy: Messages["workspace"] }) {
  return (
    <header className="flex min-h-16 items-center justify-between gap-4 border-b border-[var(--color-line)] bg-white px-5 sm:px-8">
      <div>
        <p className="text-xs font-semibold text-[var(--color-muted)]">
          {copy.workspace}
        </p>
        <p className="text-sm font-bold">Sari Arta Indonesia</p>
      </div>
      <div className="flex items-center gap-3">
        <LanguageSwitcher compact />
        <StatusBadge tone="success">{copy.internal}</StatusBadge>
        <form action={logout}>
          <button className="text-xs font-semibold text-[var(--color-muted)] hover:text-[var(--color-ink)]">
            {copy.signOut}
          </button>
        </form>
        <span
          className="grid h-9 w-9 place-items-center rounded-full bg-[var(--color-brand)] text-xs font-bold text-white"
          aria-label={copy.signedInUser}
        >
          SA
        </span>
      </div>
    </header>
  );
}
