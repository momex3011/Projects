"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Bot,
  ExternalLink,
  History,
  LayoutGrid,
  Palette,
  Plus,
  RefreshCw,
  Sparkles,
} from "lucide-react";

import { ClayButton } from "@/components/clay/ClayButton";
import { ClayCard } from "@/components/clay/ClayCard";
import {
  fetchProject,
  fetchProjects,
  fetchProjectVersion,
  fetchProjectVersions,
  type ProjectSummary,
  type ProjectVersionSummary,
} from "@/lib/project-api";
import { siteThemeMap } from "@/lib/styles/themes";
import { useMounted } from "@/lib/use-mounted";
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

export function DashboardHome() {
  const router = useRouter();
  const mounted = useMounted();
  const username = useBuilderStore((state) => state.username);
  const setUsername = useBuilderStore((state) => state.setUsername);
  const projectId = useBuilderStore((state) => state.projectId);
  const projectName = useBuilderStore((state) => state.projectName);
  const pages = useBuilderStore((state) => state.pages);
  const elements = useBuilderStore((state) => state.elements);
  const themeId = useBuilderStore((state) => state.themeId);
  const automations = useBuilderStore((state) => state.backendActions);
  const lastSavedAt = useBuilderStore((state) => state.lastSavedAt);
  const hydrateProject = useBuilderStore((state) => state.hydrateProject);
  const startNewProject = useBuilderStore((state) => state.startNewProject);
  const theme = siteThemeMap[themeId];

  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [versionsByProject, setVersionsByProject] = useState<
    Record<number, ProjectVersionSummary[]>
  >({});
  const [expandedProjectId, setExpandedProjectId] = useState<number | null>(null);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [actionLabel, setActionLabel] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!mounted) {
      return;
    }

    let cancelled = false;

    async function loadProjects() {
      setProjectsLoading(true);
      setErrorMessage(null);

      try {
        const savedProjects = await fetchProjects(username);

        if (!cancelled) {
          setProjects(savedProjects);
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(
            error instanceof Error
              ? error.message
              : "The saved project list could not be loaded.",
          );
        }
      } finally {
        if (!cancelled) {
          setProjectsLoading(false);
        }
      }
    }

    void loadProjects();

    return () => {
      cancelled = true;
    };
  }, [mounted, username, lastSavedAt, projectId]);

  if (!mounted) {
    return (
      <main className="builder-shell flex items-center justify-center">
        <ClayCard className="max-w-xl rounded-[36px] px-10 py-12 text-center">
          <p className="clay-tag mx-auto w-fit">Initializing Project</p>
          <h1 className="mt-4 text-3xl font-semibold text-[color:var(--builder-ink)]">
            Preparing your website builder workspace...
          </h1>
        </ClayCard>
      </main>
    );
  }

  const formCount = Object.values(elements).filter((element) => element.type === "form")
    .length;

  async function handleOpenProject(nextProjectId: number) {
    setActionLabel(`Opening project ${nextProjectId}...`);
    setErrorMessage(null);

    try {
      const project = await fetchProject(nextProjectId, username);

      hydrateProject(project.project, {
        username: project.username ?? username,
        projectId: project.id,
        publishedUrl: project.publishedUrl,
        lastSavedAt: project.latestVersion?.createdAt ?? null,
      });
      router.push("/builder");
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "The selected project could not be opened.",
      );
    } finally {
      setActionLabel(null);
    }
  }

  async function handleToggleHistory(nextProjectId: number) {
    if (expandedProjectId === nextProjectId) {
      setExpandedProjectId(null);
      return;
    }

    setExpandedProjectId(nextProjectId);
    setErrorMessage(null);

    if (versionsByProject[nextProjectId]) {
      return;
    }

    setActionLabel(`Loading history for project ${nextProjectId}...`);

    try {
      const versions = await fetchProjectVersions(nextProjectId, username);
      setVersionsByProject((current) => ({
        ...current,
        [nextProjectId]: versions,
      }));
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "The project history could not be loaded.",
      );
    } finally {
      setActionLabel(null);
    }
  }

  async function handleLoadVersion(projectSummary: ProjectSummary, versionId: number) {
    setActionLabel(`Restoring version ${versionId}...`);
    setErrorMessage(null);

    try {
      const version = await fetchProjectVersion(projectSummary.id, versionId, username);
      hydrateProject(version.project, {
        username: projectSummary.username ?? username,
        projectId: projectSummary.id,
        publishedUrl: projectSummary.publishedUrl,
        lastSavedAt: version.createdAt,
      });
      router.push("/builder");
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "That saved iteration could not be restored.",
      );
    } finally {
      setActionLabel(null);
    }
  }

  function handleStartFreshProject() {
    startNewProject();
    router.push("/builder");
  }

  return (
    <main className="builder-shell space-y-6">
      <section className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
        <ClayCard className="rounded-[42px] p-8 md:p-10">
          <div className="space-y-6">
            <span className="clay-tag">Claymorphism Builder</span>
            <div className="space-y-4">
              <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-[color:var(--builder-ink)] md:text-6xl">
                {projectName}
              </h1>
              <p className="max-w-2xl text-base leading-8 text-[color:var(--builder-muted)] md:text-lg">
                Build multi-page informational websites with nested containers,
                saved projects, and version history inside a soft floating
                builder interface.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link href="/builder" className="clay-button clay-button-accent px-5 py-3">
                Open Builder
              </Link>
              <Link href="/backend-view" className="clay-button px-5 py-3">
                Open Backend View
              </Link>
              <ClayButton
                type="button"
                variant="ghost"
                className="px-5 py-3"
                onClick={handleStartFreshProject}
              >
                <Plus className="h-4 w-4" />
                New Project
              </ClayButton>
            </div>
            <div className="rounded-[28px] border border-white/70 bg-white/55 px-5 py-4 shadow-clay-soft">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[color:var(--builder-muted)]">
                Current Save Status
              </p>
              <p className="mt-2 text-lg font-semibold text-[color:var(--builder-ink)]">
                {projectId ? `Project #${projectId}` : "Unsaved draft"}
              </p>
              <p className="mt-2 text-sm leading-6 text-[color:var(--builder-muted)]">
                Last saved: {formatSavedTime(lastSavedAt)}
              </p>
            </div>
          </div>
        </ClayCard>

        <ClayCard className="rounded-[42px] p-8">
          <div className="space-y-5">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.34em] text-[color:var(--builder-muted)]">
                Workspace Owner
              </p>
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="builder-input mt-3"
                placeholder="username"
              />
              <p className="mt-3 text-sm leading-6 text-[color:var(--builder-muted)]">
                Switch this field to separate projects by person or client.
              </p>
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.34em] text-[color:var(--builder-muted)]">
                Current Theme
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-[color:var(--builder-ink)]">
                {theme.label}
              </h2>
              <p className="mt-2 text-sm leading-6 text-[color:var(--builder-muted)]">
                {theme.tagline}
              </p>
            </div>
            <div
              className="rounded-[28px] border border-white/70 p-5 shadow-clay-soft"
              style={{
                background: theme.variables.background,
                color: theme.variables.text,
              }}
            >
              <div
                className="rounded-[22px] p-4"
                style={{
                  background: theme.variables.surface,
                  border: `${theme.variables.borderWidth} ${theme.variables.borderStyle} ${theme.variables.border}`,
                  boxShadow: theme.variables.shadow,
                }}
              >
                <p className="text-xs uppercase tracking-[0.28em]">{theme.label}</p>
                <p className="mt-3 text-sm">{theme.tagline}</p>
              </div>
            </div>
          </div>
        </ClayCard>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        {[
          {
            icon: LayoutGrid,
            label: "Pages",
            value: pages.length,
            hint: "Multi-page site structure",
          },
          {
            icon: Palette,
            label: "Theme Presets",
            value: 10,
            hint: "Exact visual systems ready to swap",
          },
          {
            icon: Sparkles,
            label: "Canvas Blocks",
            value: Object.keys(elements).length,
            hint: "Nested content blocks in the project",
          },
          {
            icon: Bot,
            label: "Automations",
            value: automations.length + formCount,
            hint: "Forms and actions wired visually",
          },
        ].map((item) => (
          <ClayCard key={item.label} className="rounded-[30px] p-6">
            <item.icon className="h-5 w-5 text-[color:var(--builder-accent)]" />
            <p className="mt-5 text-sm font-medium text-[color:var(--builder-muted)]">
              {item.label}
            </p>
            <p className="mt-2 text-4xl font-semibold text-[color:var(--builder-ink)]">
              {item.value}
            </p>
            <p className="mt-3 text-sm leading-6 text-[color:var(--builder-muted)]">
              {item.hint}
            </p>
          </ClayCard>
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <ClayCard className="builder-scroll rounded-[36px] p-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-2xl font-semibold text-[color:var(--builder-ink)]">
                Saved Projects
              </h2>
              <p className="mt-2 text-sm leading-6 text-[color:var(--builder-muted)]">
                Open another project, switch clients, or restore an older
                iteration.
              </p>
            </div>
            <ClayButton
              type="button"
              variant="ghost"
              className="px-4"
              onClick={() => {
                setProjectsLoading(true);
                setErrorMessage(null);
                void fetchProjects(username)
                  .then((savedProjects) => setProjects(savedProjects))
                  .catch((error: unknown) =>
                    setErrorMessage(
                      error instanceof Error
                        ? error.message
                        : "The saved project list could not be refreshed.",
                    ),
                  )
                  .finally(() => setProjectsLoading(false));
              }}
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </ClayButton>
          </div>

          {actionLabel ? (
            <div className="mt-5 rounded-[22px] border border-white/70 bg-white/55 px-4 py-3 text-sm text-[color:var(--builder-muted)] shadow-clay-soft">
              {actionLabel}
            </div>
          ) : null}

          {errorMessage ? (
            <div className="mt-5 rounded-[22px] border border-rose-200 bg-rose-50/85 px-4 py-3 text-sm text-rose-700 shadow-clay-soft">
              {errorMessage}
            </div>
          ) : null}

          <div className="mt-6 space-y-4">
            {projectsLoading ? (
              <div className="rounded-[24px] border border-white/70 bg-white/55 px-5 py-6 text-sm leading-7 text-[color:var(--builder-muted)] shadow-clay-soft">
                Loading saved projects for <strong>{username}</strong>...
              </div>
            ) : null}

            {!projectsLoading && !projects.length ? (
              <div className="rounded-[24px] border border-white/70 bg-white/55 px-5 py-6 text-sm leading-7 text-[color:var(--builder-muted)] shadow-clay-soft">
                No saved projects are available yet for <strong>{username}</strong>.
                Open the builder, make changes, and hit Save to create your first
                versioned project.
              </div>
            ) : null}

            {projects.map((project) => {
              const isCurrentProject = project.id === projectId;
              const versions = versionsByProject[project.id] ?? [];
              const isExpanded = expandedProjectId === project.id;

              return (
                <div
                  key={project.id}
                  className="rounded-[28px] border border-white/70 bg-white/55 p-5 shadow-clay-soft"
                >
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-lg font-semibold text-[color:var(--builder-ink)]">
                          {project.name}
                        </p>
                        {isCurrentProject ? (
                          <span className="clay-tag">Current</span>
                        ) : null}
                      </div>
                      <p className="mt-2 text-sm leading-6 text-[color:var(--builder-muted)]">
                        {project.pageCount} pages, {project.elementCount} blocks,{" "}
                        {project.versionCount} saved iterations.
                      </p>
                      <p className="mt-1 text-sm leading-6 text-[color:var(--builder-muted)]">
                        Latest save: {formatSavedTime(project.latestVersion?.createdAt ?? null)}
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <ClayButton
                        type="button"
                        variant="accent"
                        className="px-4"
                        onClick={() => void handleOpenProject(project.id)}
                      >
                        Open
                      </ClayButton>
                      <ClayButton
                        type="button"
                        variant="ghost"
                        className="px-4"
                        onClick={() => void handleToggleHistory(project.id)}
                      >
                        <History className="h-4 w-4" />
                        {isExpanded ? "Hide History" : "View History"}
                      </ClayButton>
                      {project.publishedUrl ? (
                        <a
                          href={project.publishedUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="clay-button px-4"
                        >
                          <ExternalLink className="h-4 w-4" />
                          Visit Site
                        </a>
                      ) : null}
                    </div>
                  </div>

                  {isExpanded ? (
                    <div className="mt-4 space-y-3">
                      {!versions.length ? (
                        <div className="rounded-[22px] border border-white/70 bg-white/55 px-4 py-3 text-sm text-[color:var(--builder-muted)]">
                          No versions have been loaded yet for this project.
                        </div>
                      ) : null}

                      {versions.map((version) => (
                        <div
                          key={version.id}
                          className="flex flex-wrap items-center justify-between gap-3 rounded-[22px] border border-white/70 bg-white/70 px-4 py-3"
                        >
                          <div>
                            <p className="text-sm font-semibold text-[color:var(--builder-ink)]">
                              {version.label}
                            </p>
                            <p className="mt-1 text-sm leading-6 text-[color:var(--builder-muted)]">
                              {formatSavedTime(version.createdAt)} with {version.pageCount} pages
                              and {version.elementCount} blocks.
                            </p>
                          </div>
                          <ClayButton
                            type="button"
                            variant="ghost"
                            className="px-4"
                            onClick={() => void handleLoadVersion(project, version.id)}
                          >
                            Restore
                          </ClayButton>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </ClayCard>

        <div className="space-y-6">
          <ClayCard className="rounded-[36px] p-8">
            <h2 className="text-2xl font-semibold text-[color:var(--builder-ink)]">
              Current Project Pages
            </h2>
            <div className="mt-6 space-y-3">
              {pages.map((page) => (
                <div
                  key={page.id}
                  className="rounded-[24px] border border-white/70 bg-white/55 px-5 py-4 shadow-clay-soft"
                >
                  <p className="text-base font-semibold text-[color:var(--builder-ink)]">
                    {page.name}
                  </p>
                  <p className="mt-1 text-sm leading-6 text-[color:var(--builder-muted)]">
                    {page.description}
                  </p>
                </div>
              ))}
            </div>
          </ClayCard>

          <ClayCard className="rounded-[36px] p-8">
            <h2 className="text-2xl font-semibold text-[color:var(--builder-ink)]">
              Builder Workflow
            </h2>
            <div className="mt-6 grid gap-4">
              {[
                "Use Dashboard to move between projects instead of being trapped in one route.",
                "Save in the builder whenever you want a new iteration recorded in history.",
                "Restore any older save from the project history list to branch your work.",
                "Open Backend View to inspect the contact form automations visually.",
              ].map((item) => (
                <div
                  key={item}
                  className="rounded-[24px] border border-white/70 bg-white/55 p-5 text-sm leading-7 text-[color:var(--builder-muted)] shadow-clay-soft"
                >
                  {item}
                </div>
              ))}
            </div>
          </ClayCard>
        </div>
      </section>
    </main>
  );
}
