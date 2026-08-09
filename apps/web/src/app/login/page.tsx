import { login } from "./actions";

export default function LoginPage() {
  return (
    <main className="grid min-h-screen place-items-center bg-[var(--canvas)] px-6">
      <form
        action={login}
        className="w-full max-w-md rounded-3xl border border-[var(--line)] bg-white p-8 shadow-xl"
      >
        <p className="text-xs font-bold uppercase tracking-[0.22em] text-[var(--accent)]">
          Sari Arta
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight">
          Sales workspace
        </h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Sign in with your authorized business account.
        </p>
        <label className="mt-8 block text-sm font-semibold" htmlFor="email">
          Email
        </label>
        <input
          className="field mt-2"
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
        />
        <label className="mt-5 block text-sm font-semibold" htmlFor="password">
          Password
        </label>
        <input
          className="field mt-2"
          id="password"
          name="password"
          type="password"
          required
          autoComplete="current-password"
        />
        <button className="button-primary mt-7 w-full" type="submit">
          Sign in
        </button>
      </form>
    </main>
  );
}
