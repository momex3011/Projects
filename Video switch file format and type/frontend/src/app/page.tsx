"use client";

import { useMemo, useState } from "react";

import { FileUploader } from "../components/FileUploader";
import { NavBar } from "../components/NavBar";
import { ToolOptionsPanel } from "../components/ToolOptionsPanel";
import {
  defaultToolId,
  toolDefinitionMap,
  toolDefinitions,
  type ToolId,
} from "../lib/tools";
import { defaultUploadDefaults } from "../lib/uploadDefaults";

const summaryAccents = [
  "from-[var(--accent-sky)] to-[#d7e2ff]",
  "from-[var(--accent-peach)] to-[#ffe1bc]",
  "from-[var(--accent-coral)] to-[#ffc0b8]",
  "from-[var(--accent-mint)] to-[#dafbee]",
];

const createInitialSelections = () =>
  Object.fromEntries(
    toolDefinitions.map((tool) => [
      tool.id,
      Object.fromEntries(tool.optionGroups.map((group) => [group.key, group.choices[0] ?? ""])),
    ]),
  ) as Record<ToolId, Record<string, string>>;

const getHeroCards = (toolId: ToolId) => {
  switch (toolId) {
    case "gif-maker":
      return [
        {
          eyebrow: "Input",
          title: "Clips or stills",
          body: "Start from a short clip or a single image and shape it into a repeatable loop.",
        },
        {
          eyebrow: "Best for",
          title: "Quick loops",
          body: "Ideal for short motion bursts that need to replay cleanly.",
        },
        {
          eyebrow: "Output",
          title: "Animated GIF",
          body: "Keep the result simple and easy to share.",
        },
      ];
    case "video-to-gif":
      return [
        {
          eyebrow: "Input",
          title: "Short clips",
          body: "Start from a moment worth replaying.",
        },
        {
          eyebrow: "Best for",
          title: "Highlights",
          body: "Turn a longer clip into a focused repeating moment.",
        },
        {
          eyebrow: "Output",
          title: "Animated GIF",
          body: "Keep the motion compact for quick sharing.",
        },
      ];
    case "gif-to-mp4":
      return [
        {
          eyebrow: "Input",
          title: "GIF files",
          body: "Move a loop into a more polished playback format.",
        },
        {
          eyebrow: "Best for",
          title: "Sharing",
          body: "Useful when video delivers more smoothly than a GIF.",
        },
        {
          eyebrow: "Output",
          title: "MP4 video",
          body: "Keep the motion ready for modern playback surfaces.",
        },
      ];
    case "gif-to-webm":
      return [
        {
          eyebrow: "Input",
          title: "GIF files",
          body: "Move a loop into a lighter web-first format.",
        },
        {
          eyebrow: "Best for",
          title: "Web delivery",
          body: "A good fit for modern browser playback.",
        },
        {
          eyebrow: "Output",
          title: "WebM video",
          body: "Keep the motion light and flexible.",
        },
      ];
    case "gif-to-mov":
      return [
        {
          eyebrow: "Input",
          title: "GIF files",
          body: "Rewrap a loop for editing or review handoff.",
        },
        {
          eyebrow: "Best for",
          title: "Presentation",
          body: "Useful for cleaner creative delivery.",
        },
        {
          eyebrow: "Output",
          title: "MOV video",
          body: "Carry the motion into a familiar handoff format.",
        },
      ];
    case "webp-to-gif":
      return [
        {
          eyebrow: "Input",
          title: "WebP motion",
          body: "Convert a newer animated image into a broader format.",
        },
        {
          eyebrow: "Best for",
          title: "Compatibility",
          body: "Helpful when a GIF fits the destination better.",
        },
        {
          eyebrow: "Output",
          title: "Animated GIF",
          body: "Keep the result easy to place and share.",
        },
      ];
    case "apng-to-gif":
      return [
        {
          eyebrow: "Input",
          title: "APNG files",
          body: "Simplify animated PNG motion into a classic loop.",
        },
        {
          eyebrow: "Best for",
          title: "Easy placement",
          body: "A good fit for spaces that prefer GIF output.",
        },
        {
          eyebrow: "Output",
          title: "Animated GIF",
          body: "Keep the motion portable and easy to reuse.",
        },
      ];
    case "avif-to-gif":
      return [
        {
          eyebrow: "Input",
          title: "AVIF motion",
          body: "Move newer animated images into a simpler loop format.",
        },
        {
          eyebrow: "Best for",
          title: "Cross-platform",
          body: "Useful when broad sharing matters more than novelty.",
        },
        {
          eyebrow: "Output",
          title: "Animated GIF",
          body: "Keep the motion familiar and easy to drop in.",
        },
      ];
  }
};

const summaryMeta = {
  title: "Current tool setup",
  note: "These choices update as you click different tools above, so the workspace always reflects the format you are currently using.",
};

export default function HomePage() {
  const [activeToolId, setActiveToolId] = useState<ToolId>(defaultToolId);
  const [toolSelections, setToolSelections] = useState<Record<ToolId, Record<string, string>>>(
    createInitialSelections,
  );

  const activeTool = toolDefinitionMap[activeToolId];
  const activeSelections = toolSelections[activeToolId] ?? {};
  const uploadDefaults = defaultUploadDefaults;

  const heroCards = useMemo(() => {
    return getHeroCards(activeToolId);
  }, [activeToolId]);

  const summaryItems = useMemo(() => {
    return activeTool.optionGroups.map((group, index) => ({
      title: group.label,
      value: activeSelections[group.key] ?? group.choices[0] ?? "",
      accent: summaryAccents[index % summaryAccents.length],
    }));
  }, [activeSelections, activeTool]);

  const updateToolSelection = (groupKey: string, choice: string) => {
    setToolSelections((current) => ({
      ...current,
      [activeToolId]: {
        ...(current[activeToolId] ?? {}),
        [groupKey]: choice,
      },
    }));
  };

  return (
    <div className="min-h-screen overflow-x-hidden pb-16">
      <div className="clay-grid fixed inset-0 -z-20 opacity-25" />
      <div className="fixed inset-0 -z-10 bg-[radial-gradient(circle_at_20%_18%,rgba(255,142,127,0.18),transparent_24%),radial-gradient(circle_at_80%_14%,rgba(154,183,255,0.22),transparent_24%),radial-gradient(circle_at_50%_84%,rgba(141,231,207,0.14),transparent_30%)]" />

      <NavBar activeToolId={activeToolId} onSelect={setActiveToolId} />

      <main className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-4 pt-6 sm:px-6 lg:px-8">
        <section className="clay-shell rounded-[34px] px-6 py-6 sm:px-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-[var(--text-muted)]/70">
                Current Tool
              </p>
              <h2 className="mt-2 font-display text-3xl text-white">Using {activeTool.label}</h2>
              <p className="mt-2 max-w-3xl text-sm leading-7 text-[var(--text-muted)] sm:text-base">
                {activeTool.currentToolNote}
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <div className="clay-badge px-4 py-3 text-sm text-white">
                Source: <span className="font-medium">{activeTool.acceptedLabel}</span>
              </div>
              <div className="clay-badge px-4 py-3 text-sm text-white">
                Output: <span className="font-medium">{activeTool.outputLabel}</span>
              </div>
            </div>
          </div>
        </section>

        <section
          className="clay-shell relative overflow-hidden rounded-[40px] px-6 py-8 sm:px-8 sm:py-10"
        >
          <div className="absolute -left-10 top-8 h-52 w-52 rounded-full bg-[radial-gradient(circle,rgba(255,191,141,0.2),transparent_72%)] blur-2xl" />
          <div className="absolute right-0 top-0 h-56 w-56 rounded-full bg-[radial-gradient(circle,rgba(154,183,255,0.18),transparent_72%)] blur-2xl" />

          <div className="relative grid gap-8 lg:grid-cols-[minmax(0,1.32fr)_minmax(320px,0.88fr)]">
            <div className="space-y-6">
              <div className="clay-badge inline-flex w-fit items-center gap-3 px-4 py-2.5 text-xs uppercase tracking-[0.28em] text-white">
                {activeTool.badge}
                <span className="h-2.5 w-2.5 animate-pulse-glow rounded-full bg-[var(--accent-mint)]" />
              </div>

              <div className="space-y-4">
                <h1 className="max-w-3xl font-display text-4xl font-semibold leading-tight text-white sm:text-[3.35rem]">
                  {activeTool.heroTitle}
                </h1>
                <p className="max-w-2xl text-base leading-8 text-[var(--text-muted)] sm:text-lg">
                  {activeTool.heroBody}
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                {heroCards.map((card) => (
                  <div key={card.eyebrow} className="clay-card rounded-[28px] p-4">
                    <p className="text-xs uppercase tracking-[0.28em] text-[var(--text-muted)]/70">
                      {card.eyebrow}
                    </p>
                    <p className="mt-3 font-display text-2xl text-white">{card.title}</p>
                    <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">
                      {card.body}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <aside className="clay-card animate-float rounded-[34px] p-5">
              <p className="text-xs uppercase tracking-[0.28em] text-[var(--text-muted)]/70">
                Selected setup
              </p>
              <h2 className="mt-3 font-display text-2xl text-white">{summaryMeta.title}</h2>

              <div className="mt-5 grid gap-3">
                {summaryItems.map((item) => (
                  <div key={item.title} className="clay-inset rounded-[24px] px-4 py-4">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-sm text-[var(--text-muted)]">{item.title}</p>
                        <p className="mt-1 font-display text-xl text-white">{item.value}</p>
                      </div>
                      <div className={`h-10 w-10 rounded-full bg-gradient-to-br ${item.accent}`} />
                    </div>
                  </div>
                ))}
              </div>

              <div className="clay-inset mt-5 rounded-[24px] px-4 py-4 text-sm leading-6 text-[var(--text-muted)]">
                {summaryMeta.note}
              </div>
            </aside>
          </div>
        </section>

        <section className="grid gap-8 lg:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
          <div className="space-y-8">
            <FileUploader
              settings={uploadDefaults}
              activeTool={activeTool}
              toolSelections={activeSelections}
            />
            <ToolOptionsPanel
              tool={activeTool}
              selections={activeSelections}
              onSelect={updateToolSelection}
            />
          </div>

          <aside className="space-y-6">
            <div className="clay-shell rounded-[34px] px-6 py-6">
              <p className="text-xs uppercase tracking-[0.28em] text-[var(--text-muted)]/70">
                How it works
              </p>
              <h2 className="mt-3 font-display text-2xl text-white">
                A clear three-step journey
              </h2>

              <div className="mt-5 space-y-3">
                {activeTool.workflow.map((item, index) => (
                  <div key={item.title} className="clay-inset flex gap-4 rounded-[24px] p-4">
                    <div className="clay-pill mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full font-display text-sm text-white">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium text-white">{item.title}</p>
                      <p className="mt-1 text-sm leading-6 text-[var(--text-muted)]">{item.body}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="clay-shell rounded-[34px] px-6 py-6">
              <p className="text-xs uppercase tracking-[0.28em] text-[var(--text-muted)]/70">
                Helpful guidance
              </p>
              <div className="mt-4 grid gap-3">
                {activeTool.guidance.map((item) => (
                  <div key={item.title} className="clay-card rounded-[24px] p-4">
                    <p className="font-medium text-white">{item.title}</p>
                    <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">
                      {item.body}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </aside>
        </section>
      </main>
    </div>
  );
}
