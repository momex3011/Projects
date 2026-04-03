"use client";

import "@xyflow/react/dist/style.css";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  DatabaseZap,
  ExternalLink,
  Globe,
  Mail,
  Webhook,
  Workflow,
} from "lucide-react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";

import { ClayCard } from "@/components/clay/ClayCard";
import { HelpHint, Tooltip } from "@/components/ui/Tooltip";
import { backendActionCatalog, type BackendActionType } from "@/lib/builder-types";
import { siteThemeMap } from "@/lib/styles/themes";
import { useMounted } from "@/lib/use-mounted";
import { useBuilderStore } from "@/store/useBuilderStore";

const actionIconMap = {
  email: Mail,
  database: DatabaseZap,
  webhook: Webhook,
  "success-message": Workflow,
};

export function BackendView() {
  const mounted = useMounted();
  const hasHydrated = useBuilderStore((state) => state.hasHydrated);
  const pages = useBuilderStore((state) => state.pages);
  const elements = useBuilderStore((state) => state.elements);
  const backendActions = useBuilderStore((state) => state.backendActions);
  const themeId = useBuilderStore((state) => state.themeId);
  const projectId = useBuilderStore((state) => state.projectId);
  const publishedUrl = useBuilderStore((state) => state.publishedUrl);
  const toggleAutomationForElement = useBuilderStore(
    (state) => state.toggleAutomationForElement,
  );
  const updateAutomation = useBuilderStore((state) => state.updateAutomation);
  const theme = siteThemeMap[themeId];
  const forms = useMemo(
    () => Object.values(elements).filter((element) => element.type === "form"),
    [elements],
  );

  const [selectedFormIdState, setSelectedFormId] = useState<string | null>(null);
  const [selectedActionTypeState, setSelectedActionType] =
    useState<BackendActionType | null>(null);
  const selectedFormId = useMemo(() => {
    if (!forms.length) {
      return null;
    }

    if (
      selectedFormIdState &&
      forms.some((form) => form.id === selectedFormIdState)
    ) {
      return selectedFormIdState;
    }

    return forms[0].id;
  }, [forms, selectedFormIdState]);

  const selectedForm = useMemo(
    () => (selectedFormId ? elements[selectedFormId] ?? null : null),
    [elements, selectedFormId],
  );
  const selectedFormActions = useMemo(
    () =>
      selectedForm
        ? backendActions.filter((action) => action.sourceElementId === selectedForm.id)
        : [],
    [backendActions, selectedForm],
  );

  const selectedActionType = useMemo(() => {
    if (!selectedFormActions.length) {
      return null;
    }

    if (
      selectedActionTypeState &&
      selectedFormActions.some(
        (action) => action.actionType === selectedActionTypeState,
      )
    ) {
      return selectedActionTypeState;
    }

    return selectedFormActions[0].actionType;
  }, [selectedActionTypeState, selectedFormActions]);

  const activeAutomation = useMemo(
    () =>
      selectedActionType && selectedForm
        ? selectedFormActions.find(
            (action) => action.actionType === selectedActionType,
          ) ?? null
        : null,
    [selectedActionType, selectedForm, selectedFormActions],
  );

  if (!mounted || !hasHydrated) {
    return (
      <main className="builder-shell flex items-center justify-center">
        <ClayCard className="max-w-xl rounded-[38px] px-10 py-12 text-center">
          <p className="clay-tag mx-auto w-fit">Loading Backend View</p>
          <h1 className="mt-4 text-3xl font-semibold text-[color:var(--builder-ink)]">
            Mapping your form automations...
          </h1>
        </ClayCard>
      </main>
    );
  }

  const nodes: Node[] = [];
  const edges: Edge[] = [];

  if (!forms.length) {
    nodes.push({
      id: "empty",
      position: { x: 120, y: 160 },
      data: { label: "Add a Contact Form block in the builder to create actions." },
      style: {
        width: 320,
        borderRadius: 28,
        padding: 16,
        border: "1px solid rgba(226, 232, 240, 1)",
        background: "rgba(255,255,255,0.96)",
        boxShadow: "0 18px 36px rgba(15, 23, 42, 0.08)",
      },
    });
  }

  forms.forEach((form, formIndex) => {
    const page = pages.find((item) => item.id === form.pageId);
    const relatedActions = backendActions.filter(
      (action) => action.sourceElementId === form.id,
    );
    const formNodeId = `form-${form.id}`;

    nodes.push({
      id: formNodeId,
      position: { x: 40, y: formIndex * 240 + 60 },
      data: { label: `${page?.name ?? "Page"}: ${form.name}` },
      style: {
        width: 250,
        borderRadius: 28,
        padding: 16,
        border:
          selectedFormId === form.id
            ? "2px solid rgba(37, 99, 235, 0.9)"
            : "1px solid rgba(226, 232, 240, 1)",
        background: "rgba(255,255,255,0.96)",
        boxShadow: "0 18px 36px rgba(15, 23, 42, 0.08)",
      },
    });

    relatedActions.forEach((action, actionIndex) => {
      const actionNodeId = `action-${action.id}`;
      const isActiveAction =
        selectedFormId === form.id && selectedActionType === action.actionType;

      nodes.push({
        id: actionNodeId,
        position: { x: 390 + actionIndex * 270, y: formIndex * 240 + 60 },
        data: { label: `${action.label}\n${action.config.target}` },
        style: {
          width: 240,
          whiteSpace: "pre-line",
          borderRadius: 26,
          padding: 16,
          border: isActiveAction
            ? "2px solid rgba(37, 99, 235, 0.92)"
            : "1px solid rgba(226, 232, 240, 1)",
          background: action.enabled ? "rgba(239, 246, 255, 0.95)" : "rgba(255,255,255,0.96)",
          boxShadow: "0 18px 36px rgba(15, 23, 42, 0.08)",
        },
      });

      edges.push({
        id: `${formNodeId}-${actionNodeId}`,
        source: formNodeId,
        target: actionNodeId,
        animated: action.enabled,
        style: {
          stroke: action.enabled ? "#2563eb" : "#94a3b8",
          strokeWidth: 2.5,
        },
      });
    });
  });

  function handleToggleAction(actionType: BackendActionType) {
    if (!selectedForm) {
      return;
    }

    const exists = selectedFormActions.some(
      (action) => action.actionType === actionType,
    );

    toggleAutomationForElement(selectedForm.id, actionType);

    if (exists && selectedActionType === actionType) {
      setSelectedActionType(null);
      return;
    }

    setSelectedActionType(actionType);
  }

  return (
    <main className="builder-shell space-y-6">
      <div className="clay-panel rounded-[34px] p-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="clay-tag w-fit">No-Code Backend</p>
            <h1 className="mt-3 text-3xl font-semibold text-[color:var(--builder-ink)]">
              Visual Automation Control Room
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-7 text-[color:var(--builder-muted)]">
              Manage form actions directly here. Select a form, toggle the actions
              you want, edit the target and behavior notes, and then deploy a
              temporary live website to test the flow.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/" className="clay-button w-fit px-4">
              Dashboard
            </Link>
            <Link href="/builder" className="clay-button w-fit px-4">
              <ArrowLeft className="h-4 w-4" />
              Back to Builder
            </Link>
            {publishedUrl ? (
              <a
                href={publishedUrl}
                target="_blank"
                rel="noreferrer"
                className="clay-button clay-button-accent w-fit px-4"
              >
                <Globe className="h-4 w-4" />
                Open Live Site
              </a>
            ) : null}
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <ClayCard className="h-[780px] overflow-hidden rounded-[34px] p-4">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            className="rounded-[28px]"
            style={{
              borderRadius: 28,
              background: "linear-gradient(145deg, rgba(255,255,255,0.98), rgba(248,250,252,0.98))",
            }}
          >
            <Background gap={28} size={1} color="rgba(148, 163, 184, 0.22)" />
            <Controls />
            <MiniMap
              pannable
              style={{
                background: "rgba(255,255,255,0.92)",
                borderRadius: 20,
              }}
            />
          </ReactFlow>
        </ClayCard>

        <ClayCard className="builder-scroll h-[780px] rounded-[34px] p-5">
          <div className="space-y-5">
            <div
              className="rounded-[28px] p-5 shadow-clay-soft"
              style={{
                background: theme.variables.background,
                color: theme.variables.text,
              }}
            >
              <p className="text-[10px] font-semibold uppercase tracking-[0.32em]">
                Current Website Theme
              </p>
              <h2 className="mt-2 text-2xl font-semibold">{theme.label}</h2>
              <p className="mt-2 text-sm leading-6">{theme.tagline}</p>
              <div className="mt-4 flex flex-wrap gap-2 text-sm">
                <span className="rounded-full bg-white/70 px-3 py-1 font-medium">
                  {forms.length} form blocks
                </span>
                <span className="rounded-full bg-white/70 px-3 py-1 font-medium">
                  {backendActions.length} actions
                </span>
                {projectId ? (
                  <span className="rounded-full bg-white/70 px-3 py-1 font-medium">
                    Project #{projectId}
                  </span>
                ) : null}
              </div>
            </div>

            <section className="space-y-3">
              <div className="flex items-center gap-2">
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-600">
                  Select Form
                </p>
                <HelpHint
                  content="Each form can own a different stack of backend actions. Pick the form you want to wire up before editing targets."
                  label="Form selection help"
                />
              </div>

              {!forms.length ? (
                <div className="rounded-[24px] border border-slate-200 bg-white p-5 text-sm leading-7 text-slate-600 shadow-clay-soft">
                  No form blocks exist yet. Add a Contact Form in the builder, then
                  come back here to wire email, database, webhook, or success-message
                  actions.
                </div>
              ) : (
                <div className="grid gap-3">
                  {forms.map((form) => {
                    const page = pages.find((item) => item.id === form.pageId);
                    const actionCount = backendActions.filter(
                      (action) => action.sourceElementId === form.id,
                    ).length;

                    return (
                      <button
                        key={form.id}
                        type="button"
                        onClick={() => setSelectedFormId(form.id)}
                        className={`rounded-[24px] border px-4 py-4 text-left shadow-clay-soft transition ${
                          selectedFormId === form.id
                            ? "border-blue-300 bg-blue-50"
                            : "border-slate-200 bg-white"
                        }`}
                      >
                        <p className="text-sm font-semibold text-slate-800">
                          {form.name}
                        </p>
                        <p className="mt-1 text-sm leading-6 text-slate-600">
                          {page?.name ?? "Page"} · {actionCount} configured action
                          {actionCount === 1 ? "" : "s"}
                        </p>
                      </button>
                    );
                  })}
                </div>
              )}
            </section>

            {selectedForm ? (
              <section className="space-y-4">
                <div className="flex items-center gap-2">
                  <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-600">
                    Action Palette
                  </p>
                  <HelpHint
                    content="Toggle actions on this form directly from the backend view. Once an action is active, you can edit its label, target, and notes below."
                    label="Action palette help"
                  />
                </div>

                <div className="grid gap-3">
                  {backendActionCatalog.map((action) => {
                    const isEnabled = selectedFormActions.some(
                      (automation) => automation.actionType === action.actionType,
                    );
                    const isActive = selectedActionType === action.actionType;
                    const ActionIcon = actionIconMap[action.actionType];

                    return (
                      <Tooltip
                        key={action.actionType}
                        content={`${action.label}: ${action.description}`}
                      >
                        <button
                          type="button"
                          onClick={() => handleToggleAction(action.actionType)}
                          className={`w-full rounded-[24px] border px-4 py-4 text-left shadow-clay-soft transition ${
                            isEnabled
                              ? isActive
                                ? "border-blue-500 bg-blue-50"
                                : "border-blue-200 bg-blue-50/60"
                              : "border-slate-200 bg-white"
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            <span className="flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 bg-slate-50 text-blue-600">
                              <ActionIcon className="h-4.5 w-4.5" />
                            </span>
                            <div>
                              <p className="text-sm font-semibold text-slate-800">
                                {action.label}
                              </p>
                              <p className="mt-1 text-sm leading-6 text-slate-600">
                                {action.description}
                              </p>
                            </div>
                          </div>
                        </button>
                      </Tooltip>
                    );
                  })}
                </div>
              </section>
            ) : null}

            {activeAutomation ? (
              <section className="space-y-4 rounded-[28px] border border-slate-200 bg-white p-5 shadow-clay-soft">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-600">
                      Action Editor
                    </p>
                    <p className="mt-2 text-lg font-semibold text-slate-800">
                      {activeAutomation.label}
                    </p>
                  </div>
                  <button
                    type="button"
                    className={`rounded-full px-4 py-2 text-sm font-semibold ${
                      activeAutomation.enabled
                        ? "bg-blue-600 text-white"
                        : "border border-slate-200 bg-slate-100 text-slate-700"
                    }`}
                    onClick={() =>
                      updateAutomation(activeAutomation.id, {
                        enabled: !activeAutomation.enabled,
                      })
                    }
                  >
                    {activeAutomation.enabled ? "Enabled" : "Disabled"}
                  </button>
                </div>

                <label className="space-y-2 text-sm">
                  <span className="text-slate-600">Action Label</span>
                  <input
                    className="builder-input"
                    value={activeAutomation.label}
                    onChange={(event) =>
                      updateAutomation(activeAutomation.id, {
                        label: event.target.value,
                      })
                    }
                    placeholder="Readable label"
                  />
                </label>

                <label className="space-y-2 text-sm">
                  <span className="text-slate-600">Target</span>
                  <input
                    className="builder-input"
                    value={activeAutomation.config.target}
                    onChange={(event) =>
                      updateAutomation(activeAutomation.id, {
                        config: { target: event.target.value },
                      })
                    }
                    placeholder="Email, database table, webhook URL, or message"
                  />
                </label>

                <label className="space-y-2 text-sm">
                  <span className="text-slate-600">Notes / Behavior</span>
                  <textarea
                    className="builder-input min-h-[110px] resize-y"
                    value={activeAutomation.config.note}
                    onChange={(event) =>
                      updateAutomation(activeAutomation.id, {
                        config: { note: event.target.value },
                      })
                    }
                    placeholder="Add operator notes or user-facing guidance"
                  />
                </label>
              </section>
            ) : null}

            <section className="space-y-3">
              <div className="flex items-center gap-2">
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-600">
                  Live Site Status
                </p>
                <HelpHint
                  content="Deploy from the builder top bar, then use this link to test how the current saved template behaves as a temporary public site."
                  label="Live site help"
                />
              </div>

              <div className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-clay-soft">
                <p className="text-sm leading-6 text-slate-600">
                  {publishedUrl
                    ? "A temporary deployed site is ready."
                    : "No temporary deployed site yet. Use Deploy Temp Site in the builder top bar to create one from the latest template."}
                </p>
                {publishedUrl ? (
                  <a
                    href={publishedUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-4 inline-flex items-center gap-2 font-semibold text-blue-700 underline underline-offset-4"
                  >
                    <ExternalLink className="h-4 w-4" />
                    {publishedUrl}
                  </a>
                ) : null}
              </div>
            </section>

            {backendActions.length ? (
              <section className="space-y-3">
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-600">
                  All Configured Actions
                </p>
                <div className="grid gap-3">
                  {backendActions.map((action) => {
                    const source = elements[action.sourceElementId];
                    const page = pages.find((item) => item.id === source?.pageId);
                    const ActionIcon = actionIconMap[action.actionType];

                    return (
                      <button
                        key={action.id}
                        type="button"
                        onClick={() => {
                          setSelectedFormId(action.sourceElementId);
                          setSelectedActionType(action.actionType);
                        }}
                        className={`rounded-[24px] border p-4 text-left shadow-clay-soft transition ${
                          selectedFormId === action.sourceElementId &&
                          selectedActionType === action.actionType
                            ? "border-blue-300 bg-blue-50"
                            : "border-slate-200 bg-white"
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <span className="flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 bg-slate-50 text-blue-600">
                            <ActionIcon className="h-4.5 w-4.5" />
                          </span>
                          <div>
                            <p className="text-sm font-semibold text-slate-800">
                              {action.label}
                            </p>
                            <p className="mt-1 text-sm leading-6 text-slate-600">
                              Source: {page?.name} / {source?.name}
                            </p>
                            <p className="mt-1 text-sm leading-6 text-slate-600">
                              Target: {action.config.target}
                            </p>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </section>
            ) : null}
          </div>
        </ClayCard>
      </div>
    </main>
  );
}
