import type { BuilderElementType } from "@/lib/builder-types";

export const paletteBlocks: Array<{
  type: BuilderElementType;
  title: string;
  description: string;
}> = [
  {
    type: "container",
    title: "Container",
    description: "Nest boxes inside this section to compose structured layouts.",
  },
  {
    type: "text",
    title: "Text",
    description: "Drop editorial copy blocks for headlines, body text, and callouts.",
  },
  {
    type: "image",
    title: "Image",
    description: "Add visual anchors with rounded media panels and captions.",
  },
  {
    type: "form",
    title: "Contact Form",
    description: "Capture leads and connect them to visual backend actions.",
  },
];
