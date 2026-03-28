export type UploadDefaults = {
  resolution: "1080p" | "4K";
  colorize: boolean;
  interpolate60fps: boolean;
  audioRestore: boolean;
  filmRestore: boolean;
};

export const defaultUploadDefaults: UploadDefaults = {
  resolution: "4K",
  colorize: true,
  interpolate60fps: true,
  audioRestore: true,
  filmRestore: true,
};
