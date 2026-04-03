"use client";

import { nanoid } from "nanoid";
import { create } from "zustand";
import {
  createJSONStorage,
  persist,
  type StateStorage,
} from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

import {
  buildInitialProject,
  createBlankPage,
  createElementTemplate,
} from "@/lib/builder-factories";
import {
  DEFAULT_WORKSPACE_USERNAME,
  type BuilderProjectSnapshot,
} from "@/lib/project-api";
import {
  type BackendActionType,
  type BuilderAutomation,
  type BuilderElement,
  type BuilderElementContent,
  type BuilderElementStyle,
  type BuilderElementType,
  type BuilderPage,
  type ThemePresetId,
  backendActionCatalog,
  elementLabels,
} from "@/lib/builder-types";

type LayoutPatch = Partial<BuilderElement["layout"]>;

interface BuilderProjectMetadata {
  username: string;
  projectId: number | null;
  publishedUrl: string | null;
  lastSavedAt: string | null;
}

interface BuilderStoreState {
  username: string;
  projectId: number | null;
  publishedUrl: string | null;
  lastSavedAt: string | null;
  projectName: string;
  themeId: ThemePresetId;
  currentPageId: string;
  selectedElementId: string | null;
  pages: BuilderPage[];
  elements: Record<string, BuilderElement>;
  backendActions: BuilderAutomation[];
  hasHydrated: boolean;
  setHasHydrated: (value: boolean) => void;
  setUsername: (username: string) => void;
  setProjectName: (name: string) => void;
  setTheme: (themeId: ThemePresetId) => void;
  setCurrentPage: (pageId: string) => void;
  selectElement: (elementId: string | null) => void;
  hydrateProject: (
    snapshot: BuilderProjectSnapshot,
    metadata?: Partial<BuilderProjectMetadata>,
  ) => void;
  exportProject: () => BuilderProjectSnapshot;
  setProjectMetadata: (metadata: Partial<BuilderProjectMetadata>) => void;
  startNewProject: (name?: string) => void;
  createPage: (name?: string) => void;
  deletePage: (pageId: string) => void;
  addElement: (type: BuilderElementType, parentId: string) => void;
  updateElementLayout: (elementId: string, patch: LayoutPatch) => void;
  updateElementStyle: (elementId: string, patch: Partial<BuilderElementStyle>) => void;
  updateElementContent: (
    elementId: string,
    patch: Partial<BuilderElementContent>,
  ) => void;
  renameElement: (elementId: string, name: string) => void;
  deleteElement: (elementId: string) => void;
  moveElementToContainer: (elementId: string, nextParentId: string) => void;
  toggleAutomationForElement: (
    elementId: string,
    actionType: BackendActionType,
  ) => void;
  updateAutomation: (
    automationId: string,
    patch: {
      label?: string;
      enabled?: boolean;
      config?: Partial<BuilderAutomation["config"]>;
    },
  ) => void;
  resetProject: () => void;
}

const initialState = buildInitialProject();
const storageKey = "website-builder-project-v2";
const initialProjectMetadata: BuilderProjectMetadata = {
  username: DEFAULT_WORKSPACE_USERNAME,
  projectId: null,
  publishedUrl: null,
  lastSavedAt: null,
};

type PersistedBuilderState = BuilderProjectSnapshot & BuilderProjectMetadata;

const noopStorage: StateStorage = {
  getItem: () => null,
  setItem: () => undefined,
  removeItem: () => undefined,
};

function collectSubtreeIds(
  elements: Record<string, BuilderElement>,
  elementId: string,
  output = new Set<string>(),
  visited = new Set<string>(),
) {
  if (visited.has(elementId)) {
    return output;
  }

  visited.add(elementId);
  output.add(elementId);

  for (const childId of elements[elementId]?.childrenIds ?? []) {
    collectSubtreeIds(elements, childId, output, visited);
  }

  return output;
}

function syncPageIdForSubtree(
  elements: Record<string, BuilderElement>,
  elementId: string,
  pageId: string,
  visited = new Set<string>(),
) {
  if (visited.has(elementId)) {
    return;
  }

  visited.add(elementId);
  const element = elements[elementId];

  if (!element) {
    return;
  }

  element.pageId = pageId;

  for (const childId of element.childrenIds) {
    syncPageIdForSubtree(elements, childId, pageId, visited);
  }
}

function isDescendant(
  elements: Record<string, BuilderElement>,
  parentId: string,
  searchId: string,
  visited = new Set<string>(),
): boolean {
  if (visited.has(parentId)) {
    return false;
  }

  visited.add(parentId);

  if (parentId === searchId) {
    return true;
  }

  return (
    elements[parentId]?.childrenIds.some((childId) =>
      isDescendant(elements, childId, searchId, visited),
    ) ?? false
  );
}

function pickProjectSnapshot(
  state: BuilderProjectSnapshot | PersistedBuilderState | BuilderStoreState,
): BuilderProjectSnapshot {
  return {
    projectName: state.projectName,
    themeId: state.themeId,
    currentPageId: state.currentPageId,
    selectedElementId: state.selectedElementId,
    pages: state.pages,
    elements: state.elements,
    backendActions: state.backendActions,
  };
}

function pickPersistedState(
  state: PersistedBuilderState | BuilderStoreState,
): PersistedBuilderState {
  return {
    username: state.username,
    projectId: state.projectId,
    publishedUrl: state.publishedUrl,
    lastSavedAt: state.lastSavedAt,
    ...pickProjectSnapshot(state),
  };
}

function isThemePresetId(value: unknown): value is ThemePresetId {
  return (
    value === "minimalist" ||
    value === "brutalism" ||
    value === "neumorphism" ||
    value === "glassmorphism" ||
    value === "material" ||
    value === "cyberpunk" ||
    value === "corporate-flat" ||
    value === "retro-90s" ||
    value === "high-contrast" ||
    value === "elegant-serif"
  );
}

function cloneElement(element: BuilderElement) {
  return {
    ...element,
    childrenIds: [...element.childrenIds],
    layout: { ...element.layout },
    style: { ...element.style },
    content: {
      ...element.content,
      fields: [...element.content.fields],
    },
  } satisfies BuilderElement;
}

function sanitizePersistedState(
  persistedState: unknown,
): PersistedBuilderState {
  const fallback = {
    ...initialProjectMetadata,
    ...pickProjectSnapshot(buildInitialProject()),
  };

  if (!persistedState || typeof persistedState !== "object") {
    return fallback;
  }

  const snapshot = persistedState as Partial<PersistedBuilderState>;
  const inputPages = Array.isArray(snapshot.pages) ? snapshot.pages : [];
  const inputElements =
    snapshot.elements && typeof snapshot.elements === "object"
      ? (snapshot.elements as Record<string, BuilderElement>)
      : {};

  if (!inputPages.length || !Object.keys(inputElements).length) {
    return fallback;
  }

  const sanitizedPages: BuilderStoreState["pages"] = [];
  const sanitizedElements: BuilderStoreState["elements"] = {};

  const cloneSubtree = (
    elementId: string,
    pageId: string,
    parentId: string | null,
    lineage = new Set<string>(),
  ): boolean => {
    if (lineage.has(elementId)) {
      return false;
    }

    const source = inputElements[elementId];

    if (!source) {
      return false;
    }

    const nextLineage = new Set(lineage);
    nextLineage.add(elementId);

    const sanitizedElement = cloneElement(source);
    sanitizedElement.pageId = pageId;
    sanitizedElement.parentId = parentId;
    sanitizedElement.childrenIds = [];

    sanitizedElements[elementId] = sanitizedElement;

    const uniqueChildren = Array.from(new Set(source.childrenIds ?? []));
    for (const childId of uniqueChildren) {
      if (cloneSubtree(childId, pageId, elementId, nextLineage)) {
        sanitizedElement.childrenIds.push(childId);
      }
    }

    return true;
  };

  for (const page of inputPages) {
    if (!page || typeof page !== "object" || typeof page.rootId !== "string") {
      continue;
    }

    const root = inputElements[page.rootId];
    if (!root || root.type !== "container") {
      continue;
    }

    if (!cloneSubtree(page.rootId, page.id, null)) {
      continue;
    }

    sanitizedElements[page.rootId].locked = true;
    sanitizedElements[page.rootId].parentId = null;
    sanitizedPages.push({
      id: page.id,
      name: page.name,
      description: page.description,
      rootId: page.rootId,
    });
  }

  if (!sanitizedPages.length || !Object.keys(sanitizedElements).length) {
    return fallback;
  }

  const sanitizedActions = Array.isArray(snapshot.backendActions)
    ? snapshot.backendActions.filter((action) => {
        if (!action || typeof action !== "object") {
          return false;
        }

        if (!(action.sourceElementId in sanitizedElements)) {
          return false;
        }

        if (
          action.actionType !== "email" &&
          action.actionType !== "database" &&
          action.actionType !== "webhook" &&
          action.actionType !== "success-message"
        ) {
          return false;
        }

        return true;
      })
    : [];

  const currentPageId = sanitizedPages.some(
    (page) => page.id === snapshot.currentPageId,
  )
    ? (snapshot.currentPageId as string)
    : sanitizedPages[0].id;

  const selectedElementId =
    typeof snapshot.selectedElementId === "string" &&
    snapshot.selectedElementId in sanitizedElements
      ? snapshot.selectedElementId
      : null;

  return {
    username:
      typeof snapshot.username === "string" && snapshot.username.trim()
        ? snapshot.username
        : fallback.username,
    projectId:
      typeof snapshot.projectId === "number" && Number.isInteger(snapshot.projectId)
        ? snapshot.projectId
        : null,
    publishedUrl:
      typeof snapshot.publishedUrl === "string" && snapshot.publishedUrl.trim()
        ? snapshot.publishedUrl
        : null,
    lastSavedAt:
      typeof snapshot.lastSavedAt === "string" && snapshot.lastSavedAt.trim()
        ? snapshot.lastSavedAt
        : null,
    projectName:
      typeof snapshot.projectName === "string" && snapshot.projectName.trim()
        ? snapshot.projectName
        : fallback.projectName,
    themeId: isThemePresetId(snapshot.themeId)
      ? snapshot.themeId
      : fallback.themeId,
    currentPageId,
    selectedElementId,
    pages: sanitizedPages,
    elements: sanitizedElements,
    backendActions: sanitizedActions,
  };
}

function applySnapshot(
  state: BuilderStoreState,
  snapshot: PersistedBuilderState,
  metadata?: Partial<BuilderProjectMetadata>,
) {
  state.username = metadata?.username?.trim() || snapshot.username;
  state.projectId = metadata?.projectId ?? snapshot.projectId;
  state.publishedUrl = metadata?.publishedUrl ?? snapshot.publishedUrl;
  state.lastSavedAt = metadata?.lastSavedAt ?? snapshot.lastSavedAt;
  state.projectName = snapshot.projectName;
  state.themeId = snapshot.themeId;
  state.currentPageId = snapshot.currentPageId;
  state.selectedElementId = snapshot.selectedElementId;
  state.pages = snapshot.pages;
  state.elements = snapshot.elements;
  state.backendActions = snapshot.backendActions;
}

export const useBuilderStore = create<BuilderStoreState>()(
  persist(
    immer((set, get) => ({
      ...initialProjectMetadata,
      ...initialState,
      setHasHydrated: (value) =>
        set((state) => {
          state.hasHydrated = value;
        }),
      setUsername: (username) =>
        set((state) => {
          const nextUsername = username.trim() || DEFAULT_WORKSPACE_USERNAME;

          if (state.username !== nextUsername) {
            state.projectId = null;
            state.publishedUrl = null;
            state.lastSavedAt = null;
          }

          state.username = nextUsername;
        }),
      setProjectName: (name) =>
        set((state) => {
          state.projectName = name;
        }),
      setTheme: (themeId) =>
        set((state) => {
          state.themeId = themeId;
        }),
      setCurrentPage: (pageId) =>
        set((state) => {
          const pageExists = state.pages.some((page) => page.id === pageId);

          if (!pageExists) {
            return;
          }

          state.currentPageId = pageId;
          state.selectedElementId = null;
        }),
      selectElement: (elementId) =>
        set((state) => {
          state.selectedElementId = elementId;
        }),
      hydrateProject: (snapshot, metadata) =>
        set((state) => {
          const sanitized = sanitizePersistedState({
            ...snapshot,
            username: metadata?.username ?? state.username,
            projectId: metadata?.projectId ?? null,
            publishedUrl: metadata?.publishedUrl ?? null,
            lastSavedAt: metadata?.lastSavedAt ?? null,
          });

          applySnapshot(state, sanitized, metadata);
        }),
      exportProject: () => pickProjectSnapshot(get()),
      setProjectMetadata: (metadata) =>
        set((state) => {
          if (metadata.username !== undefined) {
            state.username = metadata.username.trim() || DEFAULT_WORKSPACE_USERNAME;
          }

          if (metadata.projectId !== undefined) {
            state.projectId = metadata.projectId;
          }

          if (metadata.publishedUrl !== undefined) {
            state.publishedUrl = metadata.publishedUrl;
          }

          if (metadata.lastSavedAt !== undefined) {
            state.lastSavedAt = metadata.lastSavedAt;
          }
        }),
      startNewProject: (name) =>
        set((state) => {
          const fresh = buildInitialProject();
          const nextName = name?.trim() || fresh.projectName;
          const preservedUsername = state.username;

          state.username = preservedUsername;
          state.projectId = null;
          state.publishedUrl = null;
          state.lastSavedAt = null;
          state.projectName = nextName;
          state.themeId = fresh.themeId;
          state.currentPageId = fresh.currentPageId;
          state.selectedElementId = fresh.selectedElementId;
          state.pages = fresh.pages;
          state.elements = fresh.elements;
          state.backendActions = fresh.backendActions;
        }),
      createPage: (name) =>
        set((state) => {
          const pageName = name?.trim() || `Page ${state.pages.length + 1}`;
          const { page, elements, focusElementId } = createBlankPage(
            pageName,
            state.pages.length,
          );

          state.pages.push(page);
          Object.assign(state.elements, elements);
          state.currentPageId = page.id;
          state.selectedElementId = focusElementId;
        }),
      deletePage: (pageId) =>
        set((state) => {
          if (state.pages.length === 1) {
            return;
          }

          const page = state.pages.find((item) => item.id === pageId);

          if (!page) {
            return;
          }

          const idsToRemove = collectSubtreeIds(state.elements, page.rootId);

          for (const id of idsToRemove) {
            delete state.elements[id];
          }

          state.backendActions = state.backendActions.filter(
            (automation) => !idsToRemove.has(automation.sourceElementId),
          );
          state.pages = state.pages.filter((item) => item.id !== pageId);

          if (state.currentPageId === pageId) {
            state.currentPageId = state.pages[0].id;
            state.selectedElementId = null;
          }
        }),
      addElement: (type, parentId) =>
        set((state) => {
          const parent = state.elements[parentId];

          if (!parent || parent.type !== "container") {
            return;
          }

          const siblingCount = parent.childrenIds.length;
          const stagger = 18 * Math.min(siblingCount, 5);
          const newElement = createElementTemplate(type, parent.pageId, parent.id, {
            name: `${elementLabels[type]} ${siblingCount + 1}`,
            layout: {
              x: 28 + stagger,
              y: 34 + stagger,
              width:
                type === "container"
                  ? Math.min(420, Math.max(parent.layout.width - 56, 320))
                  : undefined,
              height: type === "container" ? 260 : undefined,
            },
          });

          state.elements[newElement.id] = newElement;
          parent.childrenIds.push(newElement.id);
          state.selectedElementId = newElement.id;
        }),
      updateElementLayout: (elementId, patch) =>
        set((state) => {
          const element = state.elements[elementId];

          if (!element || element.locked) {
            return;
          }

          Object.assign(element.layout, patch);
        }),
      updateElementStyle: (elementId, patch) =>
        set((state) => {
          const element = state.elements[elementId];

          if (!element) {
            return;
          }

          Object.assign(element.style, patch);
        }),
      updateElementContent: (elementId, patch) =>
        set((state) => {
          const element = state.elements[elementId];

          if (!element) {
            return;
          }

          Object.assign(element.content, patch);
        }),
      renameElement: (elementId, name) =>
        set((state) => {
          const element = state.elements[elementId];

          if (!element) {
            return;
          }

          element.name = name;
        }),
      deleteElement: (elementId) =>
        set((state) => {
          const element = state.elements[elementId];

          if (!element || element.locked) {
            return;
          }

          const subtreeIds = collectSubtreeIds(state.elements, elementId);

          if (element.parentId) {
            const parent = state.elements[element.parentId];

            if (parent) {
              parent.childrenIds = parent.childrenIds.filter((id) => id !== elementId);
            }
          }

          for (const id of subtreeIds) {
            delete state.elements[id];
          }

          state.backendActions = state.backendActions.filter(
            (automation) => !subtreeIds.has(automation.sourceElementId),
          );

          if (state.selectedElementId && subtreeIds.has(state.selectedElementId)) {
            state.selectedElementId = null;
          }
        }),
      moveElementToContainer: (elementId, nextParentId) =>
        set((state) => {
          const element = state.elements[elementId];
          const nextParent = state.elements[nextParentId];

          if (
            !element ||
            element.locked ||
            !nextParent ||
            nextParent.type !== "container"
          ) {
            return;
          }

          if (
            element.id === nextParentId ||
            isDescendant(state.elements, elementId, nextParentId)
          ) {
            return;
          }

          if (element.parentId) {
            const currentParent = state.elements[element.parentId];

            if (currentParent) {
              currentParent.childrenIds = currentParent.childrenIds.filter(
                (id) => id !== element.id,
              );
            }
          }

          element.parentId = nextParent.id;
          element.layout.x = 24 + nextParent.childrenIds.length * 10;
          element.layout.y = 24 + nextParent.childrenIds.length * 10;
          nextParent.childrenIds.push(element.id);

          if (element.pageId !== nextParent.pageId) {
            syncPageIdForSubtree(state.elements, element.id, nextParent.pageId);
          }

          state.selectedElementId = element.id;
        }),
      toggleAutomationForElement: (elementId, actionType) =>
        set((state) => {
          const existing = state.backendActions.find(
            (action) =>
              action.sourceElementId === elementId && action.actionType === actionType,
          );

          if (existing) {
            state.backendActions = state.backendActions.filter(
              (action) => action.id !== existing.id,
            );
            return;
          }

          const template = backendActionCatalog.find(
            (action) => action.actionType === actionType,
          );

          if (!template) {
            return;
          }

          state.backendActions.push({
            id: nanoid(),
            sourceElementId: elementId,
            actionType,
            label: template.label,
            enabled: true,
            config: {
              target: template.defaultTarget,
              note: template.description,
            },
          });
        }),
      updateAutomation: (automationId, patch) =>
        set((state) => {
          const automation = state.backendActions.find(
            (item) => item.id === automationId,
          );

          if (!automation) {
            return;
          }

          if (patch.label !== undefined) {
            automation.label = patch.label;
          }

          if (patch.enabled !== undefined) {
            automation.enabled = patch.enabled;
          }

          if (patch.config) {
            automation.config = {
              ...automation.config,
              ...patch.config,
            };
          }
        }),
      resetProject: () =>
        set((state) => {
          const fresh = buildInitialProject();
          applySnapshot(
            state,
            {
              ...pickProjectSnapshot(fresh),
              username: state.username,
              projectId: null,
              publishedUrl: null,
              lastSavedAt: null,
            },
            {
              username: state.username,
              projectId: null,
              publishedUrl: null,
              lastSavedAt: null,
            },
          );
        }),
    })),
    {
      name: storageKey,
      version: 3,
      storage: createJSONStorage(() =>
        typeof window === "undefined" ? noopStorage : localStorage,
      ),
      partialize: (state) => pickPersistedState(state),
      migrate: (persistedState) => sanitizePersistedState(persistedState),
      merge: (persistedState, currentState) => ({
        ...currentState,
        ...sanitizePersistedState(persistedState),
      }),
      onRehydrateStorage: () => (state) => {
        if (typeof window !== "undefined") {
          window.localStorage.removeItem("website-builder-project");
        }
        state?.setHasHydrated(true);
      },
    },
  ),
);
