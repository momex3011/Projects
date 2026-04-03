"use client";

import { useRef, useState } from "react";
import { Move, MoveDiagonal2, PackagePlus, Trash2 } from "lucide-react";

import { useBuilderDrag } from "@/components/builder/BuilderDragContext";
import { ElementRenderer } from "@/components/elements/ElementRenderer";
import { Tooltip } from "@/components/ui/Tooltip";
import { cn } from "@/lib/utils";
import { useBuilderStore } from "@/store/useBuilderStore";

type ResizeCorner = "nw" | "ne" | "sw" | "se";

const MIN_WIDTH = 180;
const MIN_HEIGHT = 140;

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function getParentBounds(node: HTMLDivElement | null) {
  const parent = node?.parentElement;

  return {
    width: parent?.clientWidth ?? 1200,
    height: parent?.clientHeight ?? 800,
  };
}

export function CanvasElement({
  elementId,
  ancestorIds = [],
}: {
  elementId: string;
  ancestorIds?: string[];
}) {
  const isLoop = ancestorIds.includes(elementId);
  const element = useBuilderStore((state) => state.elements[elementId]);
  const selectedElementId = useBuilderStore((state) => state.selectedElementId);
  const selectElement = useBuilderStore((state) => state.selectElement);
  const updateElementLayout = useBuilderStore((state) => state.updateElementLayout);
  const deleteElement = useBuilderStore((state) => state.deleteElement);
  const frameRef = useRef<HTMLDivElement | null>(null);
  const [isContainerDragOver, setIsContainerDragOver] = useState(false);
  const { startExistingDrag, clearDrag, handleContainerDrop, activeDrag } =
    useBuilderDrag();

  const childIds = element?.childrenIds ?? [];
  const isSelected = selectedElementId === elementId;
  const isOver = isContainerDragOver && Boolean(activeDrag);

  if (isLoop || !element) {
    return null;
  }

  const nextAncestorIds = [...ancestorIds, elementId];

  const startMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (element.locked) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    selectElement(element.id);

    const bounds = getParentBounds(frameRef.current);
    const startX = event.clientX;
    const startY = event.clientY;
    const origin = { ...element.layout };

    const onPointerMove = (pointerEvent: PointerEvent) => {
      const deltaX = pointerEvent.clientX - startX;
      const deltaY = pointerEvent.clientY - startY;
      const nextX = clamp(origin.x + deltaX, 0, bounds.width - origin.width);
      const nextY = clamp(origin.y + deltaY, 0, bounds.height - origin.height);

      updateElementLayout(element.id, {
        x: Math.round(nextX),
        y: Math.round(nextY),
      });
    };

    const onPointerUp = () => {
      document.body.style.userSelect = "";
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
    };

    document.body.style.userSelect = "none";
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp, { once: true });
  };

  const startResize =
    (corner: ResizeCorner) => (event: React.PointerEvent<HTMLButtonElement>) => {
      if (element.locked) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();
      selectElement(element.id);

      const bounds = getParentBounds(frameRef.current);
      const startX = event.clientX;
      const startY = event.clientY;
      const origin = { ...element.layout };

      const onPointerMove = (pointerEvent: PointerEvent) => {
        const deltaX = pointerEvent.clientX - startX;
        const deltaY = pointerEvent.clientY - startY;

        let nextX = origin.x;
        let nextY = origin.y;
        let nextWidth = origin.width;
        let nextHeight = origin.height;

        if (corner.includes("e")) {
          nextWidth = clamp(origin.width + deltaX, MIN_WIDTH, bounds.width - origin.x);
        }

        if (corner.includes("s")) {
          nextHeight = clamp(
            origin.height + deltaY,
            MIN_HEIGHT,
            bounds.height - origin.y,
          );
        }

        if (corner.includes("w")) {
          nextX = clamp(origin.x + deltaX, 0, origin.x + origin.width - MIN_WIDTH);
          nextWidth = clamp(
            origin.width - (nextX - origin.x),
            MIN_WIDTH,
            bounds.width - nextX,
          );
        }

        if (corner.includes("n")) {
          nextY = clamp(origin.y + deltaY, 0, origin.y + origin.height - MIN_HEIGHT);
          nextHeight = clamp(
            origin.height - (nextY - origin.y),
            MIN_HEIGHT,
            bounds.height - nextY,
          );
        }

        updateElementLayout(element.id, {
          x: Math.round(nextX),
          y: Math.round(nextY),
          width: Math.round(nextWidth),
          height: Math.round(nextHeight),
        });
      };

      const onPointerUp = () => {
        document.body.style.userSelect = "";
        window.removeEventListener("pointermove", onPointerMove);
        window.removeEventListener("pointerup", onPointerUp);
      };

      document.body.style.userSelect = "none";
      window.addEventListener("pointermove", onPointerMove);
      window.addEventListener("pointerup", onPointerUp, { once: true });
    };

  return (
    <div
      ref={frameRef}
      className={cn("absolute overflow-visible", isSelected && "z-20")}
      style={{
        left: element.layout.x,
        top: element.layout.y,
        width: element.layout.width,
        height: element.layout.height,
        zIndex: element.layout.zIndex,
      }}
    >
      <div
        className="group relative h-full w-full"
        onMouseDown={(event) => {
          event.stopPropagation();
          selectElement(element.id);
        }}
      >
        <div
          className={cn(
            "absolute inset-0 rounded-[30px] border-2 border-transparent transition duration-200",
            isSelected &&
              "border-blue-500 ring-2 ring-blue-100 ring-offset-1 ring-offset-transparent",
          )}
        />

        {!element.locked ? (
          <div className="absolute left-3 right-3 top-3 z-30 flex items-center justify-between gap-2">
            <Tooltip
              side="bottom"
              content="Drag this handle to move the block around inside its current container."
            >
              <div
                className={cn(
                  "flex cursor-grab items-center gap-2 rounded-full border px-3 py-2 text-xs font-semibold shadow-clay-soft",
                  isSelected
                    ? "border-blue-500 bg-blue-500 text-white"
                    : "border-slate-200 bg-white text-slate-800",
                )}
                onPointerDown={startMove}
              >
                <Move className="h-3.5 w-3.5" />
                {element.name}
              </div>
            </Tooltip>

            <div className="pointer-events-none flex items-center gap-2 opacity-0 transition duration-150 group-hover:pointer-events-auto group-hover:opacity-100">
              <Tooltip
                side="bottom"
                content="Pick up this block and drop it into another container."
              >
                <button
                  type="button"
                  draggable
                  className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-full border shadow-clay-soft",
                    isSelected
                      ? "border-blue-500 bg-blue-500 text-white"
                      : "border-slate-200 bg-white text-slate-800",
                  )}
                  aria-label="Move block into another container"
                  onDragStart={(event) => {
                    event.stopPropagation();
                    event.dataTransfer.effectAllowed = "move";
                    startExistingDrag({
                      kind: "existing",
                      elementId,
                      label: element.name ?? "Block",
                    });
                  }}
                  onDragEnd={() => clearDrag()}
                >
                  <PackagePlus className="h-4 w-4" />
                </button>
              </Tooltip>
              <Tooltip
                side="bottom"
                content="Delete this block and everything nested inside it."
              >
                <button
                  type="button"
                  className="flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white shadow-clay-soft"
                  aria-label="Delete block"
                  onClick={(event) => {
                    event.stopPropagation();
                    deleteElement(element.id);
                  }}
                >
                  <Trash2 className="h-4 w-4 text-rose-500" />
                </button>
              </Tooltip>
            </div>
          </div>
        ) : null}

        <ElementRenderer
          element={element}
          isDropTarget={isOver}
          dropHandlers={
            element.type === "container"
              ? {
                  onDragOver: (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    setIsContainerDragOver(true);
                  },
                  onDragEnter: (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    setIsContainerDragOver(true);
                  },
                  onDragLeave: (event) => {
                    event.stopPropagation();
                    const nextTarget = event.relatedTarget;
                    if (
                      !(nextTarget instanceof Node) ||
                      !event.currentTarget.contains(nextTarget)
                    ) {
                      setIsContainerDragOver(false);
                    }
                  },
                  onDrop: (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    setIsContainerDragOver(false);
                    handleContainerDrop(element.id);
                    clearDrag();
                  },
                }
              : undefined
          }
        >
          {childIds
            .filter((childId, index) => childIds.indexOf(childId) === index)
            .map((childId) => (
              <CanvasElement
                key={childId}
                elementId={childId}
                ancestorIds={nextAncestorIds}
              />
          ))}
        </ElementRenderer>

        {!element.locked ? (
          <>
            <div className="pointer-events-none absolute bottom-3 right-4 z-30 rounded-full bg-white/70 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.26em] text-[color:var(--builder-muted)] opacity-0 backdrop-blur-md transition duration-150 group-hover:opacity-100">
              <MoveDiagonal2 className="mr-1 inline h-3 w-3" />
              Resize
            </div>

            <Tooltip
              side="right"
              content="Drag this corner to resize the block."
              className="absolute -left-2.5 -top-2.5 z-30"
            >
              <button
                type="button"
                aria-label="Resize top left"
                className="h-4 w-4 rounded-full border-2 border-white bg-blue-500 shadow-lg"
                onPointerDown={startResize("nw")}
              />
            </Tooltip>
            <Tooltip
              side="left"
              content="Drag this corner to resize the block."
              className="absolute -right-2.5 -top-2.5 z-30"
            >
              <button
                type="button"
                aria-label="Resize top right"
                className="h-4 w-4 rounded-full border-2 border-white bg-blue-500 shadow-lg"
                onPointerDown={startResize("ne")}
              />
            </Tooltip>
            <Tooltip
              side="right"
              content="Drag this corner to resize the block."
              className="absolute -bottom-2.5 -left-2.5 z-30"
            >
              <button
                type="button"
                aria-label="Resize bottom left"
                className="h-4 w-4 rounded-full border-2 border-white bg-blue-500 shadow-lg"
                onPointerDown={startResize("sw")}
              />
            </Tooltip>
            <Tooltip
              side="left"
              content="Drag this corner to resize the block."
              className="absolute -bottom-2.5 -right-2.5 z-30"
            >
              <button
                type="button"
                aria-label="Resize bottom right"
                className="h-4 w-4 rounded-full border-2 border-white bg-blue-500 shadow-lg"
                onPointerDown={startResize("se")}
              />
            </Tooltip>
          </>
        ) : null}
      </div>
    </div>
  );
}
