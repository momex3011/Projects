import type { DragEventHandler, ReactNode } from "react";

import type { BuilderElement } from "@/lib/builder-types";
import { ContainerBlock } from "@/components/elements/ContainerBlock";
import { FormBlock } from "@/components/elements/FormBlock";
import { ImageBlock } from "@/components/elements/ImageBlock";
import { TextBlock } from "@/components/elements/TextBlock";

interface ElementRendererProps {
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

export function ElementRenderer({
  element,
  children,
  isDropTarget,
  dropHandlers,
}: ElementRendererProps) {
  switch (element.type) {
    case "container":
      return (
        <ContainerBlock
          element={element}
          isDropTarget={isDropTarget}
          dropHandlers={dropHandlers}
        >
          {children}
        </ContainerBlock>
      );
    case "image":
      return <ImageBlock element={element} />;
    case "form":
      return <FormBlock element={element} />;
    case "text":
    default:
      return <TextBlock element={element} />;
  }
}
