"use client";

import {
  Box,
  FormInput,
  Image as ImageIcon,
  Layers3,
  MousePointerSquareDashed,
  Type,
} from "lucide-react";

import { useBuilderDrag } from "@/components/builder/BuilderDragContext";
import { ClayCard } from "@/components/clay/ClayCard";
import { PanelTitle } from "@/components/ui/PanelTitle";
import { Tooltip } from "@/components/ui/Tooltip";
import { paletteBlocks } from "@/lib/dnd/palette";
import type { BuilderElementType } from "@/lib/builder-types";
import { cn } from "@/lib/utils";
import { useBuilderStore } from "@/store/useBuilderStore";

const iconMap: Record<BuilderElementType, typeof Box> = {
  container: Box,
  text: Type,
  image: ImageIcon,
  form: FormInput,
};

function PaletteItem({
  type,
  title,
  description,
  onAdd,
}: {
  type: BuilderElementType;
  title: string;
  description: string;
  onAdd: (type: BuilderElementType) => void;
}) {
  const Icon = iconMap[type];
  const { startPaletteDrag, clearDrag, activeDrag } = useBuilderDrag();
  const isDragging = activeDrag?.kind === "palette" && activeDrag.elementType === type;

  return (
    <Tooltip content={`Drag ${title} onto the canvas to ${description.toLowerCase()}`}>
      <button
        type="button"
        draggable
        className={cn(
          "w-full rounded-[24px] border border-slate-200 bg-white p-4 text-left shadow-clay-soft transition duration-200 hover:-translate-y-0.5 hover:border-blue-200",
          isDragging && "scale-[0.98] opacity-60",
        )}
        onClick={() => onAdd(type)}
        onDragStart={(event) => {
          event.dataTransfer.effectAllowed = "move";
          startPaletteDrag({
            kind: "palette",
            elementType: type,
            label: title,
          });
        }}
        onDragEnd={() => clearDrag()}
      >
        <div className="flex items-start gap-3">
          <span className="clay-chip flex h-11 w-11 items-center justify-center">
            <Icon className="h-4.5 w-4.5 text-[color:var(--builder-accent)]" />
          </span>
          <div>
            <h3 className="text-sm font-semibold text-slate-800">
              {title}
            </h3>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              {description}
            </p>
          </div>
        </div>
      </button>
    </Tooltip>
  );
}

export function Sidebar() {
  const currentPageId = useBuilderStore((state) => state.currentPageId);
  const pages = useBuilderStore((state) => state.pages);
  const page = pages.find((item) => item.id === currentPageId);
  const selectedElementId = useBuilderStore((state) => state.selectedElementId);
  const elements = useBuilderStore((state) => state.elements);
  const addElement = useBuilderStore((state) => state.addElement);
  const targetContainerId =
    selectedElementId && elements[selectedElementId]?.type === "container"
      ? selectedElementId
      : page?.rootId;

  return (
    <ClayCard className="builder-scroll h-full rounded-[34px] p-5">
      <div className="space-y-6">
        <PanelTitle
          eyebrow="Sidebar"
          title="Canvas Blocks"
          description="Drag from here into the page canvas or inside nested containers."
          helpText="This panel is your block library. Start with a container for grouped sections, then add text, images, or forms inside it."
        />

        <div className="space-y-3">
          {paletteBlocks.map((block) => (
            <PaletteItem
              key={block.type}
              {...block}
              onAdd={(type) => {
                if (targetContainerId) {
                  addElement(type, targetContainerId);
                }
              }}
            />
          ))}
        </div>

        <div className="clay-panel-inset rounded-[28px] p-5">
          <div className="flex items-center gap-3">
            <span className="clay-chip flex h-10 w-10 items-center justify-center">
              <Layers3 className="h-4.5 w-4.5 text-[color:var(--builder-accent)]" />
            </span>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-600">
                Active Page
              </p>
              <p className="mt-1 text-lg font-semibold text-slate-800">
                {page?.name}
              </p>
              <p className="mt-1 text-xs leading-5 text-slate-600">
                Add blocks to {targetContainerId === page?.rootId ? "the page root" : "the selected container"}.
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-clay-soft">
          <div className="flex items-center gap-3">
            <MousePointerSquareDashed className="h-5 w-5 text-[color:var(--builder-accent)]" />
            <h3 className="text-sm font-semibold text-slate-800">
              Builder Tips
            </h3>
          </div>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-slate-600">
            <li>Drag a container onto the page first when you want nested groups.</li>
            <li>Use the move handle on a selected block to re-parent it into another box.</li>
            <li>Resize any block from the edges to shape the layout visually.</li>
          </ul>
        </div>
      </div>
    </ClayCard>
  );
}
