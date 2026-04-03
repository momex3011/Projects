export type ThemePresetId =
  | "minimalist"
  | "brutalism"
  | "neumorphism"
  | "glassmorphism"
  | "material"
  | "cyberpunk"
  | "corporate-flat"
  | "retro-90s"
  | "high-contrast"
  | "elegant-serif";

export type BuilderElementType = "container" | "text" | "image" | "form";

export type TextAlignment = "left" | "center" | "right";

export type FormFieldType = "text" | "email" | "tel" | "textarea";

export interface FormFieldDefinition {
  id: string;
  label: string;
  type: FormFieldType;
  placeholder: string;
  required?: boolean;
}

export interface BuilderElementLayout {
  x: number;
  y: number;
  width: number;
  height: number;
  zIndex: number;
}

export interface BuilderElementStyle {
  padding: number;
  gap: number;
  borderRadius: number;
  textAlign: TextAlignment;
  opacity: number;
  background?: string;
  color?: string;
  accentColor?: string;
}

export interface BuilderElementContent {
  text: string;
  eyebrow: string;
  headingLevel: "h1" | "h2" | "h3" | "p";
  src: string;
  alt: string;
  caption: string;
  title: string;
  intro: string;
  submitLabel: string;
  fields: FormFieldDefinition[];
}

export interface BuilderElement {
  id: string;
  pageId: string;
  parentId: string | null;
  childrenIds: string[];
  type: BuilderElementType;
  name: string;
  locked?: boolean;
  layout: BuilderElementLayout;
  style: BuilderElementStyle;
  content: BuilderElementContent;
}

export interface BuilderPage {
  id: string;
  name: string;
  description: string;
  rootId: string;
}

export type BackendActionType =
  | "email"
  | "database"
  | "webhook"
  | "success-message";

export interface BuilderAutomation {
  id: string;
  sourceElementId: string;
  actionType: BackendActionType;
  label: string;
  enabled: boolean;
  config: {
    target: string;
    note: string;
  };
}

export const elementLabels: Record<BuilderElementType, string> = {
  container: "Container",
  text: "Text",
  image: "Image",
  form: "Contact Form",
};

export const backendActionCatalog: Array<{
  actionType: BackendActionType;
  label: string;
  description: string;
  defaultTarget: string;
}> = [
  {
    actionType: "email",
    label: "Email Me",
    description: "Deliver submissions to an inbox.",
    defaultTarget: "hello@example.com",
  },
  {
    actionType: "database",
    label: "Save to Database",
    description: "Store submissions for later review.",
    defaultTarget: "leads.contacts",
  },
  {
    actionType: "webhook",
    label: "Trigger Webhook",
    description: "Forward structured payloads to another system.",
    defaultTarget: "https://api.example.com/hooks/contact",
  },
  {
    actionType: "success-message",
    label: "Show Success Message",
    description: "Display a friendly follow-up note in the UI.",
    defaultTarget: "Thanks! We will get back to you shortly.",
  },
];
