"use client";

import { toolDefinitions, type ToolId } from "../lib/tools";

type NavBarProps = {
  activeToolId: ToolId;
  onSelect: (toolId: ToolId) => void;
};

export function NavBar({ activeToolId, onSelect }: NavBarProps) {
  return (
    <header className="sticky top-0 z-40 px-4 pt-4 sm:px-6 lg:px-8">
      <div className="clay-shell mx-auto flex w-full max-w-7xl flex-col gap-5 rounded-[32px] px-5 py-5 backdrop-blur-xl sm:px-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-4">
            <div className="clay-card flex h-14 w-14 items-center justify-center rounded-[22px] bg-[linear-gradient(135deg,rgba(255,191,141,0.34),rgba(154,183,255,0.2))] font-display text-xl font-semibold text-white">
              RS
            </div>

            <div>
              <p className="font-display text-xl font-semibold tracking-tight text-white">
                RetroScale
              </p>
              <p className="mt-1 text-sm text-[var(--text-muted)]">
                Sculpted tools for switching clips and motion formats with clarity.
              </p>
            </div>
          </div>

          <div className="clay-badge inline-flex w-fit items-center gap-3 px-4 py-3 text-sm text-white">
            <span className="inline-flex h-3 w-3 animate-pulse-glow rounded-full bg-[var(--accent-mint)] shadow-[0_0_18px_rgba(141,231,207,0.7)]" />
            <span className="font-medium">Format Switchboard</span>
          </div>
        </div>

        <nav className="overflow-x-auto" aria-label="Tool selection">
          <div className="flex min-w-max gap-3 pb-1">
            {toolDefinitions.map((tool) => {
              const isActive = activeToolId === tool.id;

              return (
                <button
                  key={tool.id}
                  type="button"
                  onClick={() => onSelect(tool.id)}
                  aria-pressed={isActive}
                  className={`clay-button rounded-full px-4 py-2.5 text-sm ${
                    isActive
                      ? "bg-[linear-gradient(145deg,rgba(255,191,141,0.28),rgba(154,183,255,0.2))] text-white"
                      : "bg-[linear-gradient(145deg,rgba(255,255,255,0.1),rgba(255,255,255,0.04))] text-[var(--text-muted)]"
                  }`}
                >
                  {tool.label}
                </button>
              );
            })}
          </div>
        </nav>
      </div>
    </header>
  );
}
