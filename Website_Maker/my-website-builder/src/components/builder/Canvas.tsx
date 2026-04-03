"use client";

import { useMemo, useState } from "react";
import { Layers, Sparkles } from "lucide-react";

import { useBuilderDrag } from "@/components/builder/BuilderDragContext";
import { CanvasElement } from "@/components/builder/CanvasElement";
import { ClayCard } from "@/components/clay/ClayCard";
import { PanelTitle } from "@/components/ui/PanelTitle";
import { getSiteThemeStyle, siteThemeMap } from "@/lib/styles/themes";
import { cn } from "@/lib/utils";
import { useBuilderStore } from "@/store/useBuilderStore";

export function Canvas({ activeLabel }: { activeLabel?: string | null }) {
  const currentPageId = useBuilderStore((state) => state.currentPageId);
  const pages = useBuilderStore((state) => state.pages);
  const page = pages.find((item) => item.id === currentPageId) ?? pages[0];
  const elements = useBuilderStore((state) => state.elements);
  const root = elements[page.rootId];
  const selectedElementId = useBuilderStore((state) => state.selectedElementId);
  const selectedElement = selectedElementId ? elements[selectedElementId] : null;
  const themeId = useBuilderStore((state) => state.themeId);
  const selectElement = useBuilderStore((state) => state.selectElement);
  const theme = siteThemeMap[themeId];
  const { handleContainerDrop, clearDrag, activeDrag } = useBuilderDrag();
  const [isRootDragOver, setIsRootDragOver] = useState(false);

  const rootIsOver = isRootDragOver && Boolean(activeDrag);
  const rootChildIds = useMemo(() => root?.childrenIds ?? [], [root?.childrenIds]);
  const stageWidth = root?.layout.width ?? 1160;
  const stageViewportHeight = root?.layout.height ?? 760;
  const previewWidth = stageWidth + 56;
  const previewHeight = stageViewportHeight + 56;
  const contentHeight = useMemo(() => {
    const maxChildBottom = rootChildIds.reduce((currentBottom, childId) => {
      const child = elements[childId];

      if (!child) {
        return currentBottom;
      }

      return Math.max(currentBottom, child.layout.y + child.layout.height);
    }, 0);

    return Math.max(stageViewportHeight, maxChildBottom + 84);
  }, [elements, rootChildIds, stageViewportHeight]);

  return (
    <ClayCard className="flex h-full min-h-[920px] flex-col rounded-[34px] p-5">
      <PanelTitle
        eyebrow="Canvas"
        title={`${page.name} Website Preview`}
        description="Drop new blocks here, nest them inside containers, or drag selected blocks around their parent canvas."
        helpText="The canvas previews the current page. Click a block to edit it, drag blocks to reposition them, and use corner handles to resize them."
        trailing={
          <div className="clay-tag hidden md:inline-flex">
            <Sparkles className="h-3.5 w-3.5" />
            {theme.label}
          </div>
        }
      />

      <div className="mt-4 flex flex-wrap gap-3">
        <div className="clay-tag">
          Active page: {page.name}
        </div>
        <div className="clay-tag">
          Selected: {selectedElement?.name ?? "Nothing selected"}
        </div>
        <div className="clay-tag">
          Tip: drag, drop, then fine-tune in Properties
        </div>
      </div>

      <div className="clay-panel-inset mt-5 flex-1 overflow-auto rounded-[30px] border border-slate-200 bg-white p-5">
        <div className="canvas-grid min-h-full rounded-[28px] border border-slate-200 bg-slate-50 p-5 md:p-8">
          <div
            data-site-style={theme.surfaceTreatment}
            className={cn(
              "site-preview mx-auto max-w-[1280px] transition duration-200",
              rootIsOver && "ring-4 ring-blue-500/80",
            )}
            style={{
              ...getSiteThemeStyle(themeId),
              width: previewWidth,
              height: previewHeight,
              padding: 0,
            }}
          >
            <div
              className="site-preview-canvas"
              style={{
                width: previewWidth,
                minHeight: contentHeight + 56,
                padding: 28,
              }}
              onMouseDown={() => selectElement(null)}
              onDragOver={(event) => {
                event.preventDefault();
                setIsRootDragOver(true);
              }}
              onDragEnter={(event) => {
                event.preventDefault();
                setIsRootDragOver(true);
              }}
              onDragLeave={(event) => {
                const nextTarget = event.relatedTarget;
                if (
                  !(nextTarget instanceof Node) ||
                  !event.currentTarget.contains(nextTarget)
                ) {
                  setIsRootDragOver(false);
                }
              }}
              onDrop={(event) => {
                event.preventDefault();
                setIsRootDragOver(false);
                handleContainerDrop(page.rootId);
                clearDrag();
              }}
            >
              {activeLabel ? (
                <div className="pointer-events-none absolute right-6 top-6 z-20 rounded-full bg-white/40 px-4 py-2 text-xs font-semibold uppercase tracking-[0.28em] text-[color:var(--site-text)] backdrop-blur-md">
                  Drop {activeLabel}
                </div>
              ) : null}

              <div className="pointer-events-none absolute left-6 top-6 z-20 flex items-center gap-2 rounded-full bg-white/40 px-4 py-2 text-xs font-semibold uppercase tracking-[0.28em] text-[color:var(--site-text)] backdrop-blur-md">
                <Layers className="h-3.5 w-3.5" />
                {page.description}
              </div>

              {rootChildIds.map((childId) => (
                <CanvasElement key={childId} elementId={childId} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </ClayCard>
  );
}
