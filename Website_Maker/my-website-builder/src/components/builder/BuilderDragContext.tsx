"use client";

import { createContext, useContext, type ReactNode } from "react";

import type { BuilderElementType } from "@/lib/builder-types";

export type ActiveBuilderDrag =
  | {
      kind: "palette";
      label: string;
      elementType: BuilderElementType;
    }
  | {
      kind: "existing";
      label: string;
      elementId: string;
    }
  | null;

interface BuilderDragContextValue {
  activeDrag: ActiveBuilderDrag;
  startPaletteDrag: (payload: NonNullable<ActiveBuilderDrag> & { kind: "palette" }) => void;
  startExistingDrag: (payload: NonNullable<ActiveBuilderDrag> & { kind: "existing" }) => void;
  clearDrag: () => void;
  handleContainerDrop: (containerId: string) => void;
}

const BuilderDragContext = createContext<BuilderDragContextValue | null>(null);

export function BuilderDragProvider({
  value,
  children,
}: {
  value: BuilderDragContextValue;
  children: ReactNode;
}) {
  return (
    <BuilderDragContext.Provider value={value}>
      {children}
    </BuilderDragContext.Provider>
  );
}

export function useBuilderDrag() {
  const context = useContext(BuilderDragContext);

  if (!context) {
    throw new Error("useBuilderDrag must be used within a BuilderDragProvider.");
  }

  return context;
}
