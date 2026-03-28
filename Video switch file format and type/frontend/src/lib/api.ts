const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:5000";

type UploadInitPayload = {
  toolId: string;
  filename: string;
  totalSize: number;
  totalChunks: number;
  contentType: string;
};

type UploadChunkPayload = {
  uploadId: string;
  chunkIndex: number;
  totalChunks: number;
  blob: Blob;
  fileName: string;
};

type CompleteUploadPayload = {
  uploadId: string;
  toolId: string;
  resolution: "1080p" | "4K";
  colorize: boolean;
  interpolate60fps: boolean;
  audioRestore: boolean;
  filmRestore: boolean;
  toolOptions: Record<string, string>;
};

export type UploadInitResponse = {
  upload_id: string;
  filename: string;
  total_chunks: number;
  recommended_chunk_size: number;
  accepted_extensions: string[];
};

type UploadChunkResponse = {
  upload_id: string;
  chunk_index: number;
  received_chunks: number;
  total_chunks: number;
  is_complete: boolean;
};

export type CompleteUploadResponse = {
  mode: string;
  upload_id: string;
  task_id?: string | null;
  upload_path: string | null;
  processing_dir?: string | null;
  frames_dir?: string | null;
  audio_path?: string | null;
  video_metadata?: {
    width: number | null;
    height: number | null;
    fps: number | null;
    duration_seconds: number | null;
    frame_count: number | null;
  } | null;
  requested_pipeline: {
    resolution: string;
    colorize: boolean;
    interpolate_60fps: boolean;
    audio_restore: boolean;
    film_restore: boolean;
  };
  result_path?: string | null;
  result_filename?: string | null;
  download_url?: string | null;
  download_label?: string | null;
  status_headline?: string | null;
  status_message?: string | null;
  next_step: string;
};

const getErrorMessage = async (response: Response) => {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail ?? `Request failed with ${response.status}.`;
  } catch {
    return `Request failed with ${response.status}.`;
  }
};

const apiRequest = async <T>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(`${API_BASE_URL}${path}`, init);

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return (await response.json()) as T;
};

export const initializeUpload = async ({
  toolId,
  filename,
  totalSize,
  totalChunks,
  contentType,
}: UploadInitPayload) => {
  return apiRequest<UploadInitResponse>("/api/upload/init", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      tool_id: toolId,
      filename,
      total_size: totalSize,
      total_chunks: totalChunks,
      content_type: contentType,
    }),
  });
};

export const uploadChunk = async ({
  uploadId,
  chunkIndex,
  totalChunks,
  blob,
  fileName,
}: UploadChunkPayload) => {
  const formData = new FormData();
  formData.append("upload_id", uploadId);
  formData.append("chunk_index", String(chunkIndex));
  formData.append("total_chunks", String(totalChunks));
  formData.append("chunk", blob, `${fileName}.part`);

  return apiRequest<UploadChunkResponse>("/api/upload/chunk", {
    method: "POST",
    body: formData,
  });
};

export const completeUpload = async ({
  uploadId,
  toolId,
  resolution,
  colorize,
  interpolate60fps,
  audioRestore,
  filmRestore,
  toolOptions,
}: CompleteUploadPayload) => {
  return apiRequest<CompleteUploadResponse>("/api/upload/complete", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      upload_id: uploadId,
      tool_id: toolId,
      extract_frames: true,
      extract_audio: true,
      resolution,
      colorize,
      interpolate_60fps: interpolate60fps,
      audio_restore: audioRestore,
      film_restore: filmRestore,
      tool_options: toolOptions,
    }),
  });
};
