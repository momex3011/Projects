"use client";

import { Wand2 } from "lucide-react";

import { ClayButton } from "@/components/clay/ClayButton";
import { ClayCard } from "@/components/clay/ClayCard";
import { PanelTitle } from "@/components/ui/PanelTitle";
import { HelpHint, Tooltip } from "@/components/ui/Tooltip";
import { backendActionCatalog } from "@/lib/builder-types";
import { useBuilderStore } from "@/store/useBuilderStore";

function numberValue(value: string) {
  const parsed = Number(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

const helperCopy = {
  container:
    "Containers help you group and nest blocks. Use them to create sections, cards, and structured layouts.",
  text: "Text blocks are best for headlines, body copy, and short editorial sections.",
  image:
    "Image blocks set the visual tone of the page. Keep alt text and captions meaningful when you customize them.",
  form: "Forms collect leads and can trigger backend automations like email, database storage, or webhooks.",
} as const;

export function Properties() {
  const selectedElementId = useBuilderStore((state) => state.selectedElementId);
  const elements = useBuilderStore((state) => state.elements);
  const element = selectedElementId ? elements[selectedElementId] : null;
  const renameElement = useBuilderStore((state) => state.renameElement);
  const updateElementLayout = useBuilderStore((state) => state.updateElementLayout);
  const updateElementStyle = useBuilderStore((state) => state.updateElementStyle);
  const updateElementContent = useBuilderStore((state) => state.updateElementContent);
  const toggleAutomationForElement = useBuilderStore(
    (state) => state.toggleAutomationForElement,
  );
  const updateAutomation = useBuilderStore((state) => state.updateAutomation);
  const backendActions = useBuilderStore((state) => state.backendActions);
  const automations = selectedElementId
    ? backendActions.filter(
        (automation) => automation.sourceElementId === selectedElementId,
      )
    : [];

  if (!element) {
    return (
      <ClayCard className="rounded-[34px] p-5">
        <PanelTitle
          eyebrow="Properties"
          title="Select a block"
          description="Click any element on the canvas to edit its content, styling, layout, and backend actions."
          helpText="Properties are contextual. The controls here change based on the currently selected block."
        />
        <div className="clay-panel-inset mt-6 rounded-[28px] p-6 text-sm leading-7 text-slate-600">
          The selected block will show editable settings here. Try choosing the
          hero copy, a nested card, or the contact form.
        </div>
      </ClayCard>
    );
  }

  return (
    <ClayCard className="builder-scroll h-full rounded-[34px] p-5">
      <div className="space-y-6">
        <PanelTitle
          eyebrow="Properties"
          title={element.name}
          description="Update the selected block and watch the canvas preview refresh immediately."
          helpText={helperCopy[element.type]}
          trailing={
            <div className="clay-tag">
              <Wand2 className="h-3.5 w-3.5" />
              {element.type}
            </div>
          }
        />

        <div className="rounded-[24px] border border-slate-200 bg-white px-4 py-3 text-sm leading-6 text-slate-600 shadow-clay-soft">
          {helperCopy[element.type]}
        </div>

        <section className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-600">
            Overview
          </p>
          <input
            className="builder-input"
            value={element.name}
            onChange={(event) => renameElement(element.id, event.target.value)}
            placeholder="Block name"
          />
        </section>

        <section className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-600">
            Layout
          </p>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "X", value: element.layout.x, key: "x" },
              { label: "Y", value: element.layout.y, key: "y" },
              { label: "Width", value: element.layout.width, key: "width" },
              { label: "Height", value: element.layout.height, key: "height" },
            ].map((field) => (
              <label key={field.key} className="space-y-2 text-sm">
                <span className="text-slate-600">{field.label}</span>
                <input
                  type="number"
                  className="builder-input"
                  value={field.value}
                  onChange={(event) =>
                    updateElementLayout(element.id, {
                      [field.key]: numberValue(event.target.value),
                    })
                  }
                />
              </label>
            ))}
          </div>
        </section>

        <section className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-600">
            Appearance
          </p>
          <div className="grid grid-cols-2 gap-3">
            <label className="space-y-2 text-sm">
              <span className="text-slate-600">Radius</span>
              <input
                type="number"
                className="builder-input"
                value={element.style.borderRadius}
                onChange={(event) =>
                  updateElementStyle(element.id, {
                    borderRadius: numberValue(event.target.value),
                  })
                }
              />
            </label>
            <label className="space-y-2 text-sm">
              <span className="text-slate-600">Padding</span>
              <input
                type="number"
                className="builder-input"
                value={element.style.padding}
                onChange={(event) =>
                  updateElementStyle(element.id, {
                    padding: numberValue(event.target.value),
                  })
                }
              />
            </label>
            <label className="space-y-2 text-sm">
              <span className="text-slate-600">Opacity</span>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                className="builder-input"
                value={element.style.opacity}
                onChange={(event) =>
                  updateElementStyle(element.id, {
                    opacity: numberValue(event.target.value),
                  })
                }
              />
            </label>
            <label className="space-y-2 text-sm">
              <span className="text-slate-600">Text Align</span>
              <select
                className="builder-input"
                value={element.style.textAlign}
                onChange={(event) =>
                  updateElementStyle(element.id, {
                    textAlign: event.target.value as typeof element.style.textAlign,
                  })
                }
              >
                <option value="left">Left</option>
                <option value="center">Center</option>
                <option value="right">Right</option>
              </select>
            </label>
          </div>
          <label className="space-y-2 text-sm">
            <span className="text-slate-600">Custom Background</span>
            <input
              className="builder-input"
              value={element.style.background ?? ""}
              onChange={(event) =>
                updateElementStyle(element.id, {
                  background: event.target.value || undefined,
                })
              }
              placeholder="Optional CSS color or gradient"
            />
          </label>
        </section>

        {element.type === "text" ? (
          <section className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-600">
              Text Content
            </p>
            <select
              className="builder-input"
              value={element.content.headingLevel}
              onChange={(event) =>
                updateElementContent(element.id, {
                  headingLevel: event.target.value as typeof element.content.headingLevel,
                })
              }
            >
              <option value="h1">Hero Heading</option>
              <option value="h2">Section Heading</option>
              <option value="h3">Card Heading</option>
              <option value="p">Paragraph</option>
            </select>
            <input
              className="builder-input"
              value={element.content.eyebrow}
              onChange={(event) =>
                updateElementContent(element.id, { eyebrow: event.target.value })
              }
              placeholder="Eyebrow label"
            />
            <textarea
              className="builder-input min-h-[180px] resize-y"
              value={element.content.text}
              onChange={(event) =>
                updateElementContent(element.id, { text: event.target.value })
              }
            />
          </section>
        ) : null}

        {element.type === "image" ? (
          <section className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-600">
              Image Content
            </p>
            <input
              className="builder-input"
              value={element.content.src}
              onChange={(event) =>
                updateElementContent(element.id, { src: event.target.value })
              }
              placeholder="Image URL"
            />
            <input
              className="builder-input"
              value={element.content.caption}
              onChange={(event) =>
                updateElementContent(element.id, { caption: event.target.value })
              }
              placeholder="Caption"
            />
          </section>
        ) : null}

        {element.type === "form" ? (
          <section className="space-y-4">
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-600">
                Form Content
              </p>
              <input
                className="builder-input"
                value={element.content.title}
                onChange={(event) =>
                  updateElementContent(element.id, { title: event.target.value })
                }
                placeholder="Form heading"
              />
              <textarea
                className="builder-input min-h-[110px] resize-y"
                value={element.content.intro}
                onChange={(event) =>
                  updateElementContent(element.id, { intro: event.target.value })
                }
              />
              <input
                className="builder-input"
                value={element.content.submitLabel}
                onChange={(event) =>
                  updateElementContent(element.id, {
                    submitLabel: event.target.value,
                  })
                }
                placeholder="Submit label"
              />
            </div>

            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-600">
                Backend Actions
              </p>
              <div className="grid gap-3">
                {backendActionCatalog.map((action) => {
                  const isEnabled = automations.some(
                    (automation) => automation.actionType === action.actionType,
                  );

                  return (
                    <Tooltip
                      key={action.actionType}
                      content={`${action.label}: ${action.description}`}
                    >
                      <button
                        type="button"
                        className={`w-full rounded-[22px] border px-4 py-3 text-left shadow-clay-soft transition ${
                          isEnabled
                            ? "border-blue-200 bg-blue-50"
                            : "border-slate-200 bg-white"
                        }`}
                        onClick={() =>
                          toggleAutomationForElement(element.id, action.actionType)
                        }
                      >
                        <p className="text-sm font-semibold text-slate-800">
                          {action.label}
                        </p>
                        <p className="mt-1 text-sm leading-6 text-slate-600">
                          {action.description}
                        </p>
                      </button>
                    </Tooltip>
                  );
                })}
              </div>
            </div>

            {automations.length ? (
              <div className="space-y-3">
                {automations.map((automation) => (
                  <div
                    key={automation.id}
                    className="rounded-[24px] border border-slate-200 bg-white p-4 shadow-clay-soft"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold text-slate-800">
                          {automation.label}
                        </p>
                        <HelpHint
                          content="Toggle this action off if you want to keep the connection configured but temporarily inactive."
                          label={`${automation.label} help`}
                        />
                      </div>
                      <ClayButton
                        type="button"
                        variant="ghost"
                        className="px-3 py-1.5 text-xs"
                        onClick={() =>
                          updateAutomation(automation.id, {
                            enabled: !automation.enabled,
                          })
                        }
                      >
                        {automation.enabled ? "Enabled" : "Disabled"}
                      </ClayButton>
                    </div>
                    <div className="mt-3 space-y-3">
                      <input
                        className="builder-input"
                        value={automation.config.target}
                        onChange={(event) =>
                          updateAutomation(automation.id, {
                            config: { target: event.target.value },
                          })
                        }
                        placeholder="Target"
                      />
                      <textarea
                        className="builder-input min-h-[88px] resize-y"
                        value={automation.config.note}
                        onChange={(event) =>
                          updateAutomation(automation.id, {
                            config: { note: event.target.value },
                          })
                        }
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </section>
        ) : null}
      </div>
    </ClayCard>
  );
}
