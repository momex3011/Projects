import type {
  BuilderAutomation,
  BuilderElement,
  BuilderPage,
  ThemePresetId,
} from "@/lib/builder-types";

export const DEFAULT_WORKSPACE_USERNAME = "local-builder";

export interface BuilderProjectSnapshot {
  projectName: string;
  themeId: ThemePresetId;
  currentPageId: string;
  selectedElementId: string | null;
  pages: BuilderPage[];
  elements: Record<string, BuilderElement>;
  backendActions: BuilderAutomation[];
}

export interface ProjectVersionSummary {
  id: number;
  projectId: number;
  label: string;
  createdAt: string;
  pageCount: number;
  elementCount: number;
}

export interface ProjectSummary {
  id: number;
  userId: number;
  username: string | null;
  name: string;
  publishedUrl: string | null;
  themeId: ThemePresetId | null;
  pageCount: number;
  elementCount: number;
  versionCount: number;
  latestVersion: ProjectVersionSummary | null;
}

export interface ProjectRecord extends ProjectSummary {
  project: BuilderProjectSnapshot;
}

interface ProjectsListResponse {
  status: string;
  projects: ProjectSummary[];
}

interface ProjectResponse {
  status: string;
  project: ProjectRecord;
  projectId: number;
}

interface VersionsResponse {
  status: string;
  versions: ProjectVersionSummary[];
}

interface VersionResponse {
  status: string;
  version: ProjectVersionSummary & {
    project: BuilderProjectSnapshot;
  };
}

interface SaveProjectRequest {
  username: string;
  projectId?: number | null;
  name: string;
  project: BuilderProjectSnapshot;
  versionLabel?: string;
}

interface SaveProjectResponse {
  status: string;
  savedAt: string;
  projectId: number;
  project: ProjectRecord;
  version: ProjectVersionSummary;
}

interface PublishProjectRequest {
  username: string;
  projectId?: number | null;
  name: string;
  project: BuilderProjectSnapshot;
  versionLabel?: string;
}

interface PublishProjectResponse extends SaveProjectResponse {
  publishedUrl: string;
}

async function requestJson<T>(input: string, init?: RequestInit) {
  const response = await fetch(input, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  const payload = (await response.json().catch(() => null)) as
    | (T & { message?: string; status?: string })
    | null;

  if (!response.ok || payload?.status === "error") {
    throw new Error(payload?.message || "The request could not be completed.");
  }

  if (!payload) {
    throw new Error("The server returned an empty response.");
  }

  return payload as T;
}

export async function fetchProjects(username: string) {
  const query = encodeURIComponent(username.trim() || DEFAULT_WORKSPACE_USERNAME);
  const payload = await requestJson<ProjectsListResponse>(
    `/api/projects?username=${query}`,
  );

  return payload.projects ?? [];
}

export async function fetchProject(projectId: number, username: string) {
  const query = encodeURIComponent(username.trim() || DEFAULT_WORKSPACE_USERNAME);
  const payload = await requestJson<ProjectResponse>(
    `/api/projects?project_id=${projectId}&username=${query}`,
  );

  return payload.project;
}

export async function saveProject(request: SaveProjectRequest) {
  const payload = await requestJson<SaveProjectResponse>("/api/projects", {
    method: "POST",
    body: JSON.stringify({
      username: request.username.trim() || DEFAULT_WORKSPACE_USERNAME,
      projectId: request.projectId ?? undefined,
      name: request.name,
      project: request.project,
      versionLabel: request.versionLabel,
    }),
  });

  return payload;
}

export async function publishProject(request: PublishProjectRequest) {
  const payload = await requestJson<PublishProjectResponse>("/api/projects/publish", {
    method: "POST",
    body: JSON.stringify({
      username: request.username.trim() || DEFAULT_WORKSPACE_USERNAME,
      projectId: request.projectId ?? undefined,
      name: request.name,
      project: request.project,
      versionLabel: request.versionLabel,
    }),
  });

  return payload;
}

export async function fetchProjectVersions(projectId: number, username: string) {
  const query = encodeURIComponent(username.trim() || DEFAULT_WORKSPACE_USERNAME);
  const payload = await requestJson<VersionsResponse>(
    `/api/projects/${projectId}/versions?username=${query}`,
  );

  return payload.versions ?? [];
}

export async function fetchProjectVersion(
  projectId: number,
  versionId: number,
  username: string,
) {
  const query = encodeURIComponent(username.trim() || DEFAULT_WORKSPACE_USERNAME);
  const payload = await requestJson<VersionResponse>(
    `/api/projects/${projectId}/versions/${versionId}?username=${query}`,
  );

  return payload.version;
}
