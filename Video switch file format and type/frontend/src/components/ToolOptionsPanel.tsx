"use client";

import type { ToolDefinition } from "../lib/tools";

type ToolOptionsPanelProps = {
  tool: ToolDefinition;
  selections: Record<string, string>;
  onSelect: (groupKey: string, choice: string) => void;
};

const choiceHelpText: Record<string, string> = {
  Gentle: "keeps the motion soft and relaxed, which works well for calm or elegant loops.",
  Steady: "gives the loop an even rhythm that feels balanced and dependable.",
  Lively: "speeds up the feel so the animation reads with more energy.",
  Square: "centers the subject in a compact frame that works well for feeds and previews.",
  Landscape: "keeps a wider frame that feels natural for scenic or horizontal content.",
  Portrait: "leans into a taller crop that fits vertical subjects better.",
  Endless: "repeats the motion continuously with no intentional pause.",
  "Pause at end": "adds a short resting beat before the loop begins again.",
  Boomerang: "plays forward and then backward for a more playful repeating motion.",
  "6 seconds": "keeps the loop short and quickly readable.",
  "10 seconds": "gives the motion a little more room while staying fairly compact.",
  "15 seconds": "holds onto more of the original moment for a fuller loop.",
  Balanced: "keeps the result in the middle ground between clarity and file size.",
  Sharper: "leans toward extra detail and crispness over smaller size.",
  "Smaller file": "prioritizes a lighter export that is easier to share.",
  "Keep full frame": "preserves the original framing without trimming the edges.",
  "Center crop": "focuses attention toward the middle of the frame.",
  "Square crop": "reshapes the frame into a more compact square presentation.",
  Presentation: "leans toward a richer, cleaner result for review or display.",
  Compact: "keeps the output lighter and more streamlined for quick sharing.",
  "Keep edge matte": "preserves the current edge treatment instead of changing the frame border.",
  "White matte": "places the motion against a bright, clean edge treatment.",
  "Black matte": "places the motion against a darker edge treatment for stronger contrast.",
  "Native loop": "keeps the playback close to the original source feel.",
  "Softer playback": "smooths the overall feel so the motion reads more gently.",
  "Sharper cadence": "gives the loop a more defined, punchy playback feel.",
  "Keep alpha": "preserves transparency so the output can sit over other backgrounds.",
  "Flatten softly": "blends transparent areas into a softer fixed background treatment.",
  "Solid backdrop": "removes transparency in favor of a stable background.",
  Smaller: "leans toward a lighter export to keep delivery easy.",
  Seamless: "aims for a loop that restarts with as little interruption as possible.",
  "Single play": "treats the motion more like a one-time pass than a constant loop.",
  Editing: "keeps the output oriented toward creative review or edit handoff.",
  Archival: "leans toward a more careful preservation-style export profile.",
  "Transparent feel": "keeps the frame treatment as open and light as possible.",
  Native: "stays close to the source motion without extra stylizing.",
  Smoothed: "softens the rhythm so the motion feels less abrupt.",
  "Frame hold": "lets each moment sit a little longer for a more deliberate feel.",
  "Soft gradients": "aims for a gentler color transition in the final loop.",
  "Punchier contrast": "adds a stronger visual separation between tones.",
  Forever: "keeps the loop repeating continuously.",
  "One cycle": "plays the loop once instead of repeating forever.",
  Original: "keeps the output close to the source dimensions.",
  "1080 wide": "reshapes the output around a larger widescreen presentation.",
  "Social ready": "leans toward a size that feels easier to place on social surfaces.",
  "Keep timing": "preserves the current speed and replay rhythm.",
  "Slightly smoother": "softens the replay feel without changing it too drastically.",
  "Faster loop": "shortens the feel so the motion restarts more quickly.",
  Lighter: "leans toward a lighter export profile for easier sharing.",
  "Image set": "treats the source as a sequence of individual frames.",
  "Clip strip": "keeps the feeling of a short, flowing motion strip.",
  "Preview loop": "leans toward a quick, repeating preview-style playback.",
  Faithful: "stays close to the source color character.",
  Warmer: "pushes the palette toward a slightly warmer overall tone.",
  Punchier: "adds extra color energy and contrast to the result.",
  Showcase: "leans toward a richer output that favors presence over a lighter file.",
};

export function ToolOptionsPanel({
  tool,
  selections,
  onSelect,
}: ToolOptionsPanelProps) {
  return (
    <section className="clay-shell rounded-[34px] px-6 py-6 sm:px-7">
        <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-[var(--text-muted)]/70">
              Tool Options
            </p>
            <h2 className="mt-2 font-display text-2xl text-white">{tool.label}</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--text-muted)]">
              Pick the conversion feel you want. Clicking a different tool above swaps these
              controls instantly.
            </p>
          </div>
          <div className="clay-badge w-fit px-4 py-2.5 text-sm text-white">
            {tool.optionGroups.length} option group{tool.optionGroups.length === 1 ? "" : "s"}
          </div>
        </div>

        <div className="clay-inset rounded-[24px] px-4 py-4 text-sm leading-6 text-[var(--text-muted)]">
          Need a quick read? Each setting below includes a short explanation bar that updates when
          you choose a different option.
        </div>

        <div className="grid gap-4">
          {tool.optionGroups.map((group) => (
            <div key={group.key} className="clay-card rounded-[28px] p-5">
              {(() => {
                const selectedChoice = selections[group.key] ?? group.choices[0];
                const helpText = choiceHelpText[selectedChoice] ?? "adjusts the feel of this setting.";

                return (
                  <>
              <div className="flex flex-col gap-2">
                <p className="font-display text-lg text-white">{group.label}</p>
                <p className="text-sm leading-6 text-[var(--text-muted)]">{group.description}</p>
              </div>

              <div className="clay-inset mt-4 rounded-[22px] px-4 py-3">
                <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]/70">
                  What This Does
                </p>
                <p className="mt-2 text-sm leading-6 text-white">
                  <span className="font-medium">{selectedChoice}</span> {helpText}
                </p>
              </div>

              <div className="mt-4 flex flex-wrap gap-3">
                {group.choices.map((choice) => {
                  const isActive = selectedChoice === choice;

                  return (
                    <button
                      key={choice}
                      type="button"
                      onClick={() => onSelect(group.key, choice)}
                      className={`clay-button rounded-full px-4 py-2.5 text-sm font-medium transition ${
                        isActive
                          ? "bg-[linear-gradient(145deg,rgba(255,191,141,0.34),rgba(154,183,255,0.22))] text-white"
                          : "bg-[linear-gradient(145deg,rgba(255,255,255,0.1),rgba(255,255,255,0.04))] text-[var(--text-muted)]"
                      }`}
                    >
                      {choice}
                    </button>
                  );
                })}
              </div>
                  </>
                );
              })()}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
