export type ToolId =
  | "gif-maker"
  | "video-to-gif"
  | "gif-to-mp4"
  | "gif-to-webm"
  | "gif-to-mov"
  | "webp-to-gif"
  | "apng-to-gif"
  | "avif-to-gif";

export type ToolOptionGroup = {
  key: string;
  label: string;
  description: string;
  choices: string[];
};

export type ToolDefinition = {
  id: ToolId;
  label: string;
  kind: "converter";
  badge: string;
  heroTitle: string;
  heroBody: string;
  currentToolNote: string;
  acceptedExtensions: string[];
  acceptedLabel: string;
  outputLabel: string;
  liveUpload: boolean;
  workflow: { title: string; body: string }[];
  guidance: { title: string; body: string }[];
  optionGroups: ToolOptionGroup[];
};

const converterWorkflow = [
  {
    title: "Choose the source",
    body: "Start with the file you want to reshape into a new delivery format.",
  },
  {
    title: "Tune the feel",
    body: "Pick the options that best match the way the motion should look and replay.",
  },
  {
    title: "Export the result",
    body: "The final file is shaped for easier sharing in the format you selected.",
  },
];

const converterGuidance = [
  {
    title: "Lead with the destination",
    body: "Choose settings that fit where the finished file will actually be watched or shared.",
  },
  {
    title: "Keep the motion readable",
    body: "A clean, understandable loop usually lands better than a crowded one.",
  },
  {
    title: "Use balance first",
    body: "Starting in the middle makes it easier to see whether you need more clarity or a lighter file.",
  },
];

export const toolDefinitions: ToolDefinition[] = [
  {
    id: "gif-maker",
    label: "GIF maker",
    kind: "converter",
    badge: "Legacy Converter",
    heroTitle: "Build a looping GIF with controls for pace, crop, and replay style.",
    heroBody:
      "Start from a still image or a short clip, then shape the loop so it feels clean, readable, and easy to share.",
    currentToolNote:
      "You are currently using GIF maker. The uploader stays available here too, so you can choose a source and shape the loop in one place.",
    acceptedExtensions: ["jpg", "jpeg", "png", "webp", "mp4", "mov", "webm"],
    acceptedLabel: "Clips or still images",
    outputLabel: "Animated GIF",
    liveUpload: true,
    workflow: converterWorkflow,
    guidance: converterGuidance,
    optionGroups: [
      { key: "pace", label: "Loop pace", description: "Choose the rhythm of the loop.", choices: ["Gentle", "Steady", "Lively"] },
      { key: "shape", label: "Frame shape", description: "Pick the crop that suits the subject.", choices: ["Square", "Landscape", "Portrait"] },
      { key: "loop", label: "Loop style", description: "Control how the motion repeats.", choices: ["Endless", "Pause at end", "Boomerang"] },
    ],
  },
  {
    id: "video-to-gif",
    label: "Video to GIF",
    kind: "converter",
    badge: "Legacy Converter",
    heroTitle: "Turn a longer clip into a tighter, cleaner looping moment.",
    heroBody:
      "Choose how much of the clip to keep and how light or crisp the final GIF should feel.",
    currentToolNote:
      "You are currently using Video to GIF. The controls below now focus on clip length, motion feel, and framing.",
    acceptedExtensions: ["mp4", "mov", "webm"],
    acceptedLabel: "Video clips",
    outputLabel: "Animated GIF",
    liveUpload: true,
    workflow: converterWorkflow,
    guidance: converterGuidance,
    optionGroups: [
      { key: "clip", label: "Clip length", description: "Decide how much of the moment to keep.", choices: ["6 seconds", "10 seconds", "15 seconds"] },
      { key: "motion", label: "Motion detail", description: "Balance clarity against file size.", choices: ["Balanced", "Sharper", "Smaller file"] },
      { key: "frame", label: "Frame treatment", description: "Pick the crop and layout style.", choices: ["Keep full frame", "Center crop", "Square crop"] },
    ],
  },
  {
    id: "gif-to-mp4",
    label: "GIF to MP4",
    kind: "converter",
    badge: "Legacy Converter",
    heroTitle: "Convert a looping GIF into a smoother, more polished MP4.",
    heroBody:
      "Choose the playback feel, edge treatment, and delivery balance before exporting.",
    currentToolNote:
      "You are currently using GIF to MP4. The controls below now focus on playback feel and final delivery.",
    acceptedExtensions: ["gif"],
    acceptedLabel: "GIF files",
    outputLabel: "MP4 video",
    liveUpload: true,
    workflow: converterWorkflow,
    guidance: converterGuidance,
    optionGroups: [
      { key: "delivery", label: "Delivery profile", description: "Decide how the MP4 should feel.", choices: ["Balanced", "Presentation", "Compact"] },
      { key: "edge", label: "Edge treatment", description: "Control how the frame edges are handled.", choices: ["Keep edge matte", "White matte", "Black matte"] },
      { key: "motion", label: "Playback feel", description: "Set the overall motion character.", choices: ["Native loop", "Softer playback", "Sharper cadence"] },
    ],
  },
  {
    id: "gif-to-webm",
    label: "GIF to WebM",
    kind: "converter",
    badge: "Legacy Converter",
    heroTitle: "Move a GIF into a lighter web-first video format.",
    heroBody:
      "Shape the transparency, loop feel, and quality balance for a cleaner web delivery result.",
    currentToolNote:
      "You are currently using GIF to WebM. The controls below now focus on transparency, quality, and loop feel.",
    acceptedExtensions: ["gif"],
    acceptedLabel: "GIF files",
    outputLabel: "WebM video",
    liveUpload: true,
    workflow: converterWorkflow,
    guidance: converterGuidance,
    optionGroups: [
      { key: "transparency", label: "Transparency", description: "Choose how the background is handled.", choices: ["Keep alpha", "Flatten softly", "Solid backdrop"] },
      { key: "quality", label: "Quality balance", description: "Tune the tradeoff between clarity and size.", choices: ["Presentation", "Balanced", "Smaller"] },
      { key: "loop", label: "Loop feel", description: "Set the way the motion repeats.", choices: ["Seamless", "Pause at end", "Single play"] },
    ],
  },
  {
    id: "gif-to-mov",
    label: "GIF to MOV",
    kind: "converter",
    badge: "Legacy Converter",
    heroTitle: "Rewrap a GIF into an editing-friendly MOV workflow.",
    heroBody:
      "Pick the background treatment, motion character, and delivery profile that suit review or handoff.",
    currentToolNote:
      "You are currently using GIF to MOV. The controls below now focus on delivery style, background, and motion character.",
    acceptedExtensions: ["gif"],
    acceptedLabel: "GIF files",
    outputLabel: "MOV video",
    liveUpload: true,
    workflow: converterWorkflow,
    guidance: converterGuidance,
    optionGroups: [
      { key: "delivery", label: "Delivery profile", description: "Choose how the MOV should be tuned.", choices: ["Editing", "Presentation", "Archival"] },
      { key: "background", label: "Background treatment", description: "Control how empty edges are presented.", choices: ["Transparent feel", "White matte", "Black matte"] },
      { key: "motion", label: "Motion character", description: "Set the overall feel of the converted loop.", choices: ["Native", "Smoothed", "Frame hold"] },
    ],
  },
  {
    id: "webp-to-gif",
    label: "WebP to GIF",
    kind: "converter",
    badge: "Legacy Converter",
    heroTitle: "Turn WebP motion into a GIF with clearer control over color and size.",
    heroBody:
      "Choose the palette feel, loop behavior, and delivery size that best fit the destination.",
    currentToolNote:
      "You are currently using WebP to GIF. The controls below now focus on palette, loop behavior, and delivery size.",
    acceptedExtensions: ["webp"],
    acceptedLabel: "WebP motion",
    outputLabel: "Animated GIF",
    liveUpload: true,
    workflow: converterWorkflow,
    guidance: converterGuidance,
    optionGroups: [
      { key: "palette", label: "Palette feel", description: "Choose the look of the final color range.", choices: ["Soft gradients", "Balanced", "Punchier contrast"] },
      { key: "loop", label: "Loop behavior", description: "Set the way the final GIF repeats.", choices: ["Forever", "One cycle", "Pause at end"] },
      { key: "size", label: "Delivery size", description: "Choose how large the final GIF should feel.", choices: ["Original", "1080 wide", "Social ready"] },
    ],
  },
  {
    id: "apng-to-gif",
    label: "APNG to GIF",
    kind: "converter",
    badge: "Legacy Converter",
    heroTitle: "Move animated PNG motion into a simpler, shareable GIF format.",
    heroBody:
      "Adjust the background feel, timing character, and delivery balance so the conversion stays readable.",
    currentToolNote:
      "You are currently using APNG to GIF. The controls below now focus on timing, background treatment, and delivery balance.",
    acceptedExtensions: ["apng", "png"],
    acceptedLabel: "APNG files",
    outputLabel: "Animated GIF",
    liveUpload: true,
    workflow: converterWorkflow,
    guidance: converterGuidance,
    optionGroups: [
      { key: "background", label: "Background treatment", description: "Choose how transparent areas should resolve.", choices: ["Flatten softly", "White matte", "Black matte"] },
      { key: "timing", label: "Timing feel", description: "Set the replay character of the loop.", choices: ["Keep timing", "Slightly smoother", "Faster loop"] },
      { key: "delivery", label: "Delivery balance", description: "Pick the clarity-to-size balance for the output.", choices: ["Balanced", "Sharper", "Lighter"] },
    ],
  },
  {
    id: "avif-to-gif",
    label: "AVIF to GIF",
    kind: "converter",
    badge: "Legacy Converter",
    heroTitle: "Turn AVIF motion into a simpler GIF workflow with adjustable color and sequence feel.",
    heroBody:
      "Choose how vivid the color should feel, how the frames should behave as a loop, and how compact the result should be.",
    currentToolNote:
      "You are currently using AVIF to GIF. The controls below now focus on sequence style, color feel, and output balance.",
    acceptedExtensions: ["avif"],
    acceptedLabel: "AVIF motion",
    outputLabel: "Animated GIF",
    liveUpload: true,
    workflow: converterWorkflow,
    guidance: converterGuidance,
    optionGroups: [
      { key: "sequence", label: "Sequence style", description: "Choose how the frame sequence should read.", choices: ["Image set", "Clip strip", "Preview loop"] },
      { key: "color", label: "Color feel", description: "Set the look of the final palette.", choices: ["Faithful", "Warmer", "Punchier"] },
      { key: "output", label: "Output balance", description: "Control how rich or compact the GIF should be.", choices: ["Balanced", "Smaller", "Showcase"] },
    ],
  },
];

export const defaultToolId: ToolId = "gif-maker";

export const toolDefinitionMap = Object.fromEntries(
  toolDefinitions.map((tool) => [tool.id, tool]),
) as Record<ToolId, ToolDefinition>;
