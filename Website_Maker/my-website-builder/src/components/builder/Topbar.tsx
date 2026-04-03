"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  ExternalLink,
  FolderPlus,
  Globe,
  Plus,
  Save,
  Trash2,
  Workflow,
} from "lucide-react";

import { ClayButton } from "@/components/clay/ClayButton";
import { HelpHint, Tooltip } from "@/components/ui/Tooltip";
import { publishProject, saveProject } from "@/lib/project-api";
import { siteThemes } from "@/lib/styles/themes";
import { useBuilderStore } from "@/store/useBuilderStore";

function formatSavedTime(value: string | null) {
  if (!value) {
    return "Not saved yet";
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
}

export function Topbar() {
  const username = useBuilderStore((state) => state.username);
  const setUsername = useBuilderStore((state) => state.setUsername);
  const projectId = useBuilderStore((state) => state.projectId);
  const publishedUrl = useBuilderStore((state) => state.publishedUrl);
  const lastSavedAt = useBuilderStore((state) => state.lastSavedAt);
  const projectName = useBuilderStore((state) => state.projectName);
  const setProjectName = useBuilderStore((state) => state.setProjectName);
  const pages = useBuilderStore((state) => state.pages);
  const currentPageId = useBuilderStore((state) => state.currentPageId);
  const setCurrentPage = useBuilderStore((state) => state.setCurrentPage);
  const createPage = useBuilderStore((state) => state.createPage);
  const deletePage = useBuilderStore((state) => state.deletePage);
  const themeId = useBuilderStore((state) => state.themeId);
  const setTheme = useBuilderStore((state) => state.setTheme);
  const exportProject = useBuilderStore((state) => state.exportProject);
  const setProjectMetadata = useBuilderStore((state) => state.setProjectMetadata);
  const startNewProject = useBuilderStore((state) => state.startNewProject);

  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);

  async function handleSaveProject() {
    setIsSaving(true);
    setSaveStatus("Saving a new iteration...");

    try {
      const response = await saveProject({
        username,
        projectId,
        name: projectName.trim() || "Untitled Project",
        project: exportProject(),
      });

      setProjectMetadata({
        projectId: response.projectId,
        publishedUrl: response.project.publishedUrl,
        lastSavedAt: response.savedAt,
      });
      setSaveStatus(
        `${response.version.label} saved at ${formatSavedTime(response.savedAt)}.`,
      );
    } catch (error) {
      setSaveStatus(
        error instanceof Error
          ? error.message
          : "This project could not be saved right now.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handlePublishProject() {
    setIsPublishing(true);
    setSaveStatus("Deploying a temporary live site...");

    try {
      const response = await publishProject({
        username,
        projectId,
        name: projectName.trim() || "Untitled Project",
        project: exportProject(),
        versionLabel: publishedUrl ? "Published update" : "Published snapshot",
      });

      setProjectMetadata({
        projectId: response.projectId,
        publishedUrl: response.publishedUrl,
        lastSavedAt: response.savedAt,
      });
      setSaveStatus(
        `Temporary site deployed at ${response.publishedUrl}.`,
      );

      if (typeof window !== "undefined") {
        window.open(response.publishedUrl, "_blank", "noopener,noreferrer");
      }
    } catch (error) {
      setSaveStatus(
        error instanceof Error
          ? error.message
          : "The temporary site could not be deployed right now.",
      );
    } finally {
      setIsPublishing(false);
    }
  }

  function handleNewProject() {
    startNewProject();
    setSaveStatus("Started a fresh project draft.");
  }

  return (
    <header className="clay-panel rounded-[34px] p-4">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center">
            <div className="flex flex-wrap items-center gap-2">
              <Tooltip content="Return to the project dashboard and browse saved work.">
                <Link href="/" className="clay-tag w-fit">
                  <ArrowLeft className="h-3.5 w-3.5" />
                  Dashboard
                </Link>
              </Tooltip>
              <Tooltip content="Open the no-code backend map for forms and automations.">
                <Link href="/backend-view" className="clay-button px-4">
                  <Workflow className="h-4 w-4" />
                  Backend View
                </Link>
              </Tooltip>
            </div>

            <div className="flex items-center gap-2">
              <input
                value={projectName}
                onChange={(event) => setProjectName(event.target.value)}
                className="builder-input w-full min-w-[240px] xl:w-[320px]"
                placeholder="Project name"
              />
              <HelpHint
                content="Give the project a clear name so it is easy to find later in the dashboard and version history."
                label="Project name help"
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="builder-input w-full min-w-[200px] xl:w-[220px]"
                placeholder="Workspace owner"
              />
              <HelpHint
                content="Change the workspace owner to separate projects by person, team, or client."
                label="Workspace owner help"
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Tooltip content="Start a fresh project while keeping the current saved versions available in the dashboard.">
              <ClayButton
                type="button"
                variant="ghost"
                onClick={handleNewProject}
                className="px-4"
              >
                <FolderPlus className="h-4 w-4" />
                New Project
              </ClayButton>
            </Tooltip>
            <Tooltip content="Save the current builder state as a new version so you can restore it later.">
              <ClayButton
                type="button"
                variant="accent"
                onClick={() => void handleSaveProject()}
                className="px-4"
                disabled={isSaving}
              >
                <Save className="h-4 w-4" />
                {isSaving ? "Saving..." : "Save Version"}
              </ClayButton>
            </Tooltip>
            <Tooltip content="Save the current builder state and open a temporary live website preview at a shareable project URL.">
              <ClayButton
                type="button"
                variant="ghost"
                onClick={() => void handlePublishProject()}
                className="px-4"
                disabled={isPublishing}
              >
                <Globe className="h-4 w-4" />
                {isPublishing
                  ? "Deploying..."
                  : publishedUrl
                    ? "Update Temp Site"
                    : "Deploy Temp Site"}
              </ClayButton>
            </Tooltip>
            {publishedUrl ? (
              <Tooltip content="Open the current temporary deployed site in a new tab.">
                <a
                  href={publishedUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="clay-button px-4"
                >
                  <ExternalLink className="h-4 w-4" />
                  Open Live Site
                </a>
              </Tooltip>
            ) : null}
          </div>
        </div>

        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="builder-scroll flex items-center gap-2 overflow-x-auto rounded-full border border-slate-200 bg-white px-3 py-2 shadow-clay-soft">
            {pages.map((page) => (
              <button
                key={page.id}
                onClick={() => setCurrentPage(page.id)}
                className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                  currentPageId === page.id
                    ? "border border-blue-200 bg-blue-50 text-blue-700 shadow-clay-soft"
                    : "text-slate-600"
                }`}
              >
                {page.name}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Tooltip content="Add another page to the current website project.">
              <ClayButton
                type="button"
                variant="ghost"
                onClick={() => createPage()}
                className="px-4"
              >
                <Plus className="h-4 w-4" />
                Page
              </ClayButton>
            </Tooltip>
            <Tooltip content="Remove the current page. This is disabled when only one page remains.">
              <ClayButton
                type="button"
                variant="ghost"
                onClick={() => deletePage(currentPageId)}
                className="px-4"
                disabled={pages.length === 1}
              >
                <Trash2 className="h-4 w-4" />
                Remove
              </ClayButton>
            </Tooltip>
            <div className="flex items-center gap-2">
              <select
                value={themeId}
                onChange={(event) => setTheme(event.target.value as typeof themeId)}
                className="builder-input min-w-[200px] py-2.5"
              >
                {siteThemes.map((theme) => (
                  <option key={theme.id} value={theme.id}>
                    {theme.label}
                  </option>
                ))}
              </select>
              <HelpHint
                content="Theme presets globally change the visual language of the website preview without affecting your content structure."
                label="Theme preset help"
              />
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-2 rounded-[24px] border border-slate-200 bg-white px-4 py-3 text-sm shadow-clay-soft md:flex-row md:items-center md:justify-between">
          <p className="text-slate-600">
            {projectId ? `Project #${projectId}` : "Unsaved draft"} for{" "}
            <strong className="text-slate-800">{username}</strong>
            . Last saved: {formatSavedTime(lastSavedAt)}
          </p>
          <div className="flex flex-wrap items-center gap-2 text-slate-600">
            <span>
              {saveStatus ??
                (publishedUrl
                  ? "Temporary site deployed."
                  : "Save often to build version history.")}
            </span>
            {publishedUrl ? (
              <a
                href={publishedUrl}
                target="_blank"
                rel="noreferrer"
                className="font-semibold text-blue-700 underline underline-offset-4"
              >
                {publishedUrl}
              </a>
            ) : null}
          </div>
        </div>
      </div>
    </header>
  );
}
