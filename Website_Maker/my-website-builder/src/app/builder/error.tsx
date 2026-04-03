"use client";

import { useEffect } from "react";
import Link from "next/link";

export default function BuilderError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Builder route error", error);
    void fetch("/api/client-errors", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        route: "/builder",
        message: error.message,
        digest: error.digest,
        stack: error.stack,
      }),
    }).catch(() => undefined);
  }, [error]);

  const handleResetData = () => {
    window.localStorage.removeItem("website-builder-project");
    window.localStorage.removeItem("website-builder-project-v2");
    reset();
    window.location.reload();
  };

  return (
    <main className="builder-shell flex items-center justify-center">
      <div className="clay-panel max-w-2xl rounded-[38px] px-10 py-12 text-center">
        <p className="clay-tag mx-auto w-fit">Builder Recovery</p>
        <h1 className="mt-4 text-3xl font-semibold text-[color:var(--builder-ink)]">
          The builder hit a runtime error.
        </h1>
        <p className="mt-4 text-sm leading-7 text-[color:var(--builder-muted)]">
          We can reset the saved canvas data and reload a fresh starter project
          with seeded pages and nested content blocks.
        </p>
        <p className="mt-3 text-xs leading-6 text-[color:var(--builder-muted)]">
          {error.message || "Unknown runtime error"}
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <button className="clay-button clay-button-accent" onClick={handleResetData}>
            Reset Builder Data
          </button>
          <button className="clay-button" onClick={() => reset()}>
            Retry
          </button>
          <Link href="/" className="clay-button">
            Return to Dashboard
          </Link>
          <Link href="/backend-view" className="clay-button">
            Open Backend View
          </Link>
        </div>
      </div>
    </main>
  );
}
