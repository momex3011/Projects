import type { DragEventHandler, ReactNode } from "react";

import type { BuilderElement } from "@/lib/builder-types";
import { cn } from "@/lib/utils";

interface ContainerBlockProps {
  element: BuilderElement;
  children?: ReactNode;
  isDropTarget?: boolean;
  dropHandlers?: {
    onDragOver?: DragEventHandler<HTMLElement>;
    onDrop?: DragEventHandler<HTMLElement>;
    onDragEnter?: DragEventHandler<HTMLElement>;
    onDragLeave?: DragEventHandler<HTMLElement>;
  };
}

export function ContainerBlock({
  element,
  children,
  isDropTarget,
  dropHandlers,
}: ContainerBlockProps) {
  return (
    <div
      className={cn(
        "site-block h-full w-full p-4 transition duration-200",
        isDropTarget && "ring-4 ring-blue-500/70 ring-offset-2 ring-offset-transparent",
      )}
      style={{
        padding: `${element.style.padding}px`,
        borderRadius: `${element.style.borderRadius}px`,
        background: element.style.background,
        opacity: element.style.opacity,
      }}
    >
      <div className="flex items-center justify-between pb-4">
        <div>
          <p className="site-eyebrow mb-2">Container</p>
          <h3 className="font-semibold tracking-tight text-[color:var(--site-text)]">
            {element.name}
          </h3>
        </div>
        <span className="rounded-full border border-white/20 bg-white/20 px-3 py-1 text-[11px] uppercase tracking-[0.24em] text-[color:var(--site-muted)]">
          {element.childrenIds.length} blocks
        </span>
      </div>
      <div className="relative h-[calc(100%-4.25rem)] rounded-[calc(var(--site-radius)-8px)] border border-dashed border-white/30 bg-white/10">
        <div className="relative h-full w-full" {...dropHandlers}>
          {children}
        </div>
        {!element.childrenIds.length ? (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center p-6 text-center text-sm leading-7 text-[color:var(--site-muted)]">
            Drop blocks here to build nested sections.
          </div>
        ) : null}
      </div>
    </div>
  );
}
