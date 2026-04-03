"use client";

import { useState } from "react";

import {
  BuilderDragProvider,
  type ActiveBuilderDrag,
} from "@/components/builder/BuilderDragContext";
import { Canvas } from "@/components/builder/Canvas";
import { Properties } from "@/components/builder/Properties";
import { Sidebar } from "@/components/builder/Sidebar";
import { Topbar } from "@/components/builder/Topbar";
import { ClayCard } from "@/components/clay/ClayCard";
import { useMounted } from "@/lib/use-mounted";
import { useBuilderStore } from "@/store/useBuilderStore";

export function BuilderWorkspace() {
  const mounted = useMounted();
  const hasHydrated = useBuilderStore((state) => state.hasHydrated);
  const addElement = useBuilderStore((state) => state.addElement);
  const moveElementToContainer = useBuilderStore(
    (state) => state.moveElementToContainer,
  );
  const [activeDrag, setActiveDrag] = useState<ActiveBuilderDrag>(null);

  const handleContainerDrop = (containerId: string) => {
    if (activeDrag) {
      if (activeDrag.kind === "palette") {
        addElement(activeDrag.elementType, containerId);
      }

      if (activeDrag.kind === "existing") {
        moveElementToContainer(activeDrag.elementId, containerId);
      }
    }

    setActiveDrag(null);
  };

  if (!mounted || !hasHydrated) {
    return (
      <main className="builder-shell flex items-center justify-center">
        <ClayCard className="max-w-2xl rounded-[38px] px-10 py-12 text-center">
          <p className="clay-tag mx-auto w-fit">Loading Builder</p>
          <h1 className="mt-4 text-3xl font-semibold text-[color:var(--builder-ink)]">
            Restoring your pages, blocks, and theme settings...
          </h1>
        </ClayCard>
      </main>
    );
  }

  return (
    <main className="builder-shell space-y-6">
      <Topbar />
      <BuilderDragProvider
        value={{
          activeDrag,
          startPaletteDrag: (payload) => setActiveDrag(payload),
          startExistingDrag: (payload) => setActiveDrag(payload),
          clearDrag: () => setActiveDrag(null),
          handleContainerDrop,
        }}
      >
        <div className="grid gap-6 xl:grid-cols-[300px_minmax(0,1fr)_350px]">
          <Sidebar />
          <Canvas activeLabel={activeDrag?.label ?? null} />
          <Properties />
        </div>
      </BuilderDragProvider>

      {activeDrag ? (
        <div className="pointer-events-none fixed bottom-6 right-6 z-50 clay-chip px-4 py-3 text-sm font-semibold text-[color:var(--builder-ink)] shadow-clay">
          Dragging {activeDrag.label}
        </div>
      ) : null}
    </main>
  );
}
