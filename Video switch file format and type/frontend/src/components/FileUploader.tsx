"use client";

import { useEffect, useRef, useState } from "react";

import {
  completeUpload,
  initializeUpload,
  uploadChunk,
  type CompleteUploadResponse,
} from "../lib/api";
import type { ToolDefinition } from "../lib/tools";
import type { UploadDefaults } from "../lib/uploadDefaults";
import { ProgressBar } from "./ProgressBar";

type FileUploaderProps = {
  settings: UploadDefaults;
  activeTool: ToolDefinition;
  toolSelections: Record<string, string>;
};

type UploadStage = "idle" | "uploading" | "processing" | "finished" | "error";

const CHUNK_SIZE_BYTES = 5 * 1024 * 1024;

const formatBytes = (value: number) => {
  const units = ["B", "KB", "MB", "GB"];
  let size = value;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }

  return `${size.toFixed(size >= 100 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
};

const getErrorMessage = (error: unknown) => {
  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong while preparing your upload. Please try again.";
};

const matchesAcceptedExtension = (file: File, activeTool: ToolDefinition) => {
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  return activeTool.acceptedExtensions.includes(extension);
};

const getActionLabels = () => ({
  choose: "Choose file",
  begin: "Create export",
  remove: "Remove file",
});

const getStageCopy = (
  tool: ToolDefinition,
): Record<UploadStage, { eyebrow: string; title: string; description: string }> => {
  return {
    idle: {
      eyebrow: "Ready",
      title: `Choose a file for ${tool.label}.`,
      description:
        "Start with a supported source file, tune the options below, and export from the same workspace.",
    },
    uploading: {
      eyebrow: "Uploading",
      title: "Uploading your source file safely.",
      description:
        "Your file is moving in steady 5 MB pieces so the transfer remains calm and dependable.",
    },
    processing: {
      eyebrow: "Exporting",
      title: `Building your ${tool.outputLabel.toLowerCase()}.`,
      description:
        "The source is in and the selected options are now shaping the final export.",
    },
    finished: {
      eyebrow: "Ready",
      title: "Your export is ready to download.",
      description:
        "The result has been created and a download action now stays visible in this workspace.",
    },
    error: {
      eyebrow: "Error",
      title: "This export needs a quick adjustment.",
      description:
        "Review the message below, make any needed change, and try again when you are ready.",
    },
  };
};

const getNextStepCopy = (
  uploadStage: UploadStage,
  tool: ToolDefinition,
  result: CompleteUploadResponse | null,
) => {
  if (uploadStage === "finished" && result?.download_url) {
    return "Your export is ready to save. You can download it now or choose another source for a new version.";
  }

  return {
    idle: "Choose a source file, tune the tool options below, and export when the setup looks right.",
    uploading: "Keep this page open while we move the file across.",
    processing: "The export is underway. Your current tool choices are already attached to this file.",
    finished: "This result is ready to save, and you can create another one from the same workspace afterward.",
    error: "Nothing is final yet. You can retry with the same file or swap to another one.",
  }[uploadStage];
};

const getSelectionSummary = (_settings: UploadDefaults, tool: ToolDefinition, selections: Record<string, string>) => {
  return tool.optionGroups
    .map((group) => selections[group.key] ?? group.choices[0] ?? "")
    .filter(Boolean)
    .join(" / ");
};

export function FileUploader({ settings, activeTool, toolSelections }: FileUploaderProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploadStage, setUploadStage] = useState<UploadStage>("idle");
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<CompleteUploadResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    setSelectedFile(null);
    setDragActive(false);
    setUploadStage("idle");
    setProgress(0);
    setResult(null);
    setErrorMessage(null);

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }, [activeTool.id]);

  const chooseFile = () => {
    inputRef.current?.click();
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setUploadStage("idle");
    setProgress(0);
    setResult(null);
    setErrorMessage(null);

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  const queueFile = (file: File | null) => {
    if (!file) {
      return;
    }

    if (!matchesAcceptedExtension(file, activeTool)) {
      setSelectedFile(null);
      setUploadStage("error");
      setErrorMessage(`Please choose ${activeTool.acceptedLabel.toLowerCase()} for ${activeTool.label}.`);
      return;
    }

    setSelectedFile(file);
    setUploadStage("idle");
    setProgress(0);
    setResult(null);
    setErrorMessage(null);
  };

  const uploadFileInChunks = async (file: File) => {
    try {
      setUploadStage("uploading");
      setProgress(0);
      setErrorMessage(null);
      setResult(null);

      const totalChunks = Math.max(1, Math.ceil(file.size / CHUNK_SIZE_BYTES));

      const initResponse = await initializeUpload({
        toolId: activeTool.id,
        filename: file.name,
        totalSize: file.size,
        totalChunks,
        contentType: file.type || "application/octet-stream",
      });

      for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex += 1) {
        const start = chunkIndex * CHUNK_SIZE_BYTES;
        const end = Math.min(file.size, start + CHUNK_SIZE_BYTES);
        const blob = file.slice(start, end);

        await uploadChunk({
          uploadId: initResponse.upload_id,
          chunkIndex,
          totalChunks,
          blob,
          fileName: file.name,
        });

        setProgress(((chunkIndex + 1) / totalChunks) * 100);
      }

      setUploadStage("processing");

      const completeResponse = await completeUpload({
        uploadId: initResponse.upload_id,
        toolId: activeTool.id,
        resolution: settings.resolution,
        colorize: settings.colorize,
        interpolate60fps: settings.interpolate60fps,
        audioRestore: settings.audioRestore,
        filmRestore: settings.filmRestore,
        toolOptions: toolSelections,
      });

      setResult(completeResponse);
      setProgress(100);
      setUploadStage("finished");
    } catch (error) {
      setUploadStage("error");
      setErrorMessage(getErrorMessage(error));
    }
  };

  const stageCopy = getStageCopy(activeTool);
  const actionLabels = getActionLabels();
  const selectionSummary = getSelectionSummary(settings, activeTool, toolSelections);

  return (
    <section className="clay-shell rounded-[36px] px-6 py-6 sm:px-7">
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-[var(--text-muted)]/70">
              {stageCopy[uploadStage].eyebrow}
            </p>
            <h2 className="mt-2 font-display text-2xl text-white">
              {stageCopy[uploadStage].title}
            </h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--text-muted)]">
              {stageCopy[uploadStage].description}
            </p>
          </div>

          <div className="clay-badge px-4 py-3 text-sm text-white">
            Best source: <span className="font-medium">{activeTool.acceptedLabel}</span>
          </div>
        </div>

        <div
          onDragEnter={(event) => {
            event.preventDefault();
            setDragActive(true);
          }}
          onDragOver={(event) => {
            event.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={(event) => {
            event.preventDefault();
            setDragActive(false);
          }}
          onDrop={(event) => {
            event.preventDefault();
            setDragActive(false);
            queueFile(event.dataTransfer.files?.[0] ?? null);
          }}
          className={`relative overflow-hidden rounded-[34px] border p-6 transition ${
            dragActive
              ? "border-white/20 bg-[linear-gradient(145deg,rgba(255,191,141,0.14),rgba(154,183,255,0.12))]"
              : "border-white/10"
          }`}
        >
          <div className="clay-card absolute inset-0 rounded-[34px]" />
          <div className="absolute -left-8 top-8 h-40 w-40 rounded-full bg-[radial-gradient(circle,rgba(255,142,127,0.28),transparent_70%)] blur-xl" />
          <div className="absolute bottom-0 right-0 h-44 w-44 rounded-full bg-[radial-gradient(circle,rgba(154,183,255,0.24),transparent_72%)] blur-xl" />

          <div className="relative z-10 flex flex-col gap-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="clay-badge px-4 py-2 text-xs uppercase tracking-[0.28em] text-[var(--text-muted)]">
                Using {activeTool.label}
              </div>
              <div className="clay-inset rounded-[20px] px-4 py-3 text-sm text-[var(--text-muted)]">
                5 MB chunked transfer
              </div>
            </div>

            <div className="max-w-3xl space-y-3">
              <h3 className="font-display text-3xl leading-tight text-white sm:text-[2rem]">
                {activeTool.heroTitle}
              </h3>
              <p className="text-sm leading-7 text-[var(--text-muted)] sm:text-base">
                {activeTool.heroBody}
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                disabled={uploadStage === "uploading" || uploadStage === "processing"}
                onClick={() => {
                  if (!selectedFile) {
                    chooseFile();
                    return;
                  }

                  void uploadFileInChunks(selectedFile);
                }}
                className="clay-button rounded-full bg-[linear-gradient(145deg,rgba(255,142,127,0.36),rgba(255,191,141,0.22))] px-5 py-3 text-sm font-medium text-white"
              >
                {selectedFile ? actionLabels.begin : actionLabels.choose}
              </button>
              {selectedFile && uploadStage !== "uploading" && uploadStage !== "processing" ? (
                <button
                  type="button"
                  onClick={clearSelection}
                  className="clay-button rounded-full bg-[linear-gradient(145deg,rgba(255,255,255,0.12),rgba(185,178,207,0.06))] px-5 py-3 text-sm font-medium text-white"
                >
                  {actionLabels.remove}
                </button>
              ) : null}
            </div>

            <input
              ref={inputRef}
              type="file"
              accept={activeTool.acceptedExtensions.map((extension) => `.${extension}`).join(",")}
              className="hidden"
              onChange={(event) => queueFile(event.target.files?.[0] ?? null)}
            />
          </div>
        </div>

        <div className="grid gap-5 lg:grid-cols-[minmax(0,1.2fr)_minmax(290px,0.8fr)]">
          <div className="clay-card rounded-[30px] p-5">
            <ProgressBar
              value={uploadStage === "processing" ? 100 : progress}
              label={uploadStage === "processing" ? "Upload complete" : "Transfer progress"}
              stage={uploadStage}
            />

            <div className="mt-6 grid gap-5 px-1 sm:grid-cols-2 xl:grid-cols-3">
              <div className="clay-inset min-h-[7.5rem] rounded-[24px] px-4 py-5">
                <p className="text-xs uppercase tracking-[0.28em] text-[var(--text-muted)]/70">
                  Selected file
                </p>
                <p className="mt-3 truncate text-sm text-white">
                  {selectedFile?.name ?? "No file selected yet"}
                </p>
              </div>
              <div className="clay-inset min-h-[7.5rem] rounded-[24px] px-4 py-5">
                <p className="text-xs uppercase tracking-[0.28em] text-[var(--text-muted)]/70">
                  File size
                </p>
                <p className="mt-3 text-sm text-white">
                  {selectedFile ? formatBytes(selectedFile.size) : "--"}
                </p>
              </div>
              <div className="clay-inset min-h-[7.5rem] rounded-[24px] px-4 py-5">
                <p className="text-xs uppercase tracking-[0.28em] text-[var(--text-muted)]/70">
                  Result type
                </p>
                <p className="mt-3 text-sm text-white">{activeTool.outputLabel}</p>
              </div>
            </div>
          </div>

          <div className="clay-card rounded-[30px] p-5">
            <p className="text-xs uppercase tracking-[0.28em] text-[var(--text-muted)]/70">
              Session overview
            </p>

            <dl className="mt-4 space-y-3 text-sm text-[var(--text-muted)]">
              <div className="clay-inset flex items-center justify-between gap-4 rounded-[22px] px-4 py-3">
                <dt>Current step</dt>
                <dd className="font-medium text-white">{stageCopy[uploadStage].eyebrow}</dd>
              </div>
              <div className="clay-inset flex items-center justify-between gap-4 rounded-[22px] px-4 py-3">
                <dt>Output</dt>
                <dd className="max-w-[12rem] truncate font-medium text-white">
                  {activeTool.outputLabel}
                </dd>
              </div>
              <div className="clay-inset flex items-center justify-between gap-4 rounded-[22px] px-4 py-3">
                <dt>Workspace</dt>
                <dd className="max-w-[12rem] truncate font-medium text-white">{activeTool.label}</dd>
              </div>
              <div className="clay-inset rounded-[22px] px-4 py-3">
                <dt className="mb-2">What happens next</dt>
                <dd className="leading-6 text-[var(--text-muted)]">
                  {getNextStepCopy(uploadStage, activeTool, result)}
                </dd>
              </div>
              <div className="clay-inset rounded-[22px] px-4 py-3">
                <dt className="mb-2">Chosen options</dt>
                <dd className="leading-6 text-[var(--text-muted)]">
                  {selectionSummary || "Your current choices will appear here."}
                </dd>
              </div>
            </dl>
          </div>
        </div>

        {errorMessage ? (
          <div className="clay-card rounded-[26px] bg-[linear-gradient(145deg,rgba(255,127,143,0.18),rgba(255,191,141,0.12))] px-5 py-4 text-sm text-white">
            {errorMessage}
          </div>
        ) : null}

        {result ? (
          <div className="clay-card rounded-[28px] bg-[linear-gradient(145deg,rgba(141,231,207,0.18),rgba(154,183,255,0.12))] px-5 py-5 sm:px-6">
            <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center lg:gap-8">
              <div className="pr-1 lg:pr-4">
                <p className="text-xs uppercase tracking-[0.28em] text-white/70">
                  {result.status_headline ?? "Ready"}
                </p>
                <h3 className="mt-2 font-display text-2xl text-white">
                  {result.result_filename ?? selectedFile?.name ?? "Your file is ready"}
                </h3>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-white/80">
                  {result.status_message ?? "Your file is ready to keep or download."}
                </p>
              </div>

              {result.download_url ? (
                <a
                  href={result.download_url}
                  download
                  className="clay-button inline-flex w-fit shrink-0 items-center justify-center self-start rounded-full bg-[linear-gradient(145deg,rgba(255,255,255,0.16),rgba(141,231,207,0.18))] px-6 py-3 text-center text-sm font-medium leading-5 text-white lg:min-w-[10.5rem] lg:self-center"
                >
                  {result.download_label ?? "Download file"}
                </a>
              ) : null}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
