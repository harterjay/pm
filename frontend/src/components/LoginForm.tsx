"use client";

import { type FormEvent, useState } from "react";

interface LoginFormProps {
  onSuccess?: () => void;
}

export const LoginForm = ({ onSuccess }: LoginFormProps) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    const response = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    setSubmitting(false);

    if (!response.ok) {
      setError("Invalid username or password.");
      return;
    }

    if (onSuccess) {
      onSuccess();
    } else {
      window.location.href = "/";
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex w-full max-w-sm flex-col gap-4 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur"
    >
      <label className="flex flex-col gap-2 text-sm font-semibold text-[var(--navy-dark)]">
        Username
        <input
          className="rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2 outline-none"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          autoComplete="username"
        />
      </label>
      <label className="flex flex-col gap-2 text-sm font-semibold text-[var(--navy-dark)]">
        Password
        <input
          type="password"
          className="rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2 outline-none"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
        />
      </label>
      {error && (
        <p
          role="alert"
          data-testid="login-error"
          className="text-sm font-semibold text-red-600"
        >
          {error}
        </p>
      )}
      <button
        type="submit"
        disabled={submitting}
        className="mt-2 rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-sm font-semibold text-white transition disabled:opacity-60"
      >
        Log in
      </button>
    </form>
  );
};
