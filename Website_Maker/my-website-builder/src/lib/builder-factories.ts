import { nanoid } from "nanoid";

import {
  type BuilderAutomation,
  type BuilderElement,
  type BuilderElementContent,
  type BuilderElementLayout,
  type BuilderElementStyle,
  type BuilderElementType,
  type BuilderPage,
  backendActionCatalog,
  elementLabels,
} from "@/lib/builder-types";

type ElementOverrides = {
  name?: string;
  locked?: boolean;
  layout?: Partial<BuilderElementLayout>;
  style?: Partial<BuilderElementStyle>;
  content?: Partial<BuilderElementContent>;
};

export interface ProjectSeed {
  projectName: string;
  themeId:
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
  currentPageId: string;
  selectedElementId: string | null;
  pages: BuilderPage[];
  elements: Record<string, BuilderElement>;
  backendActions: BuilderAutomation[];
  hasHydrated: boolean;
}

const defaultFields = [
  {
    id: nanoid(),
    label: "Name",
    type: "text" as const,
    placeholder: "Your full name",
    required: true,
  },
  {
    id: nanoid(),
    label: "Email",
    type: "email" as const,
    placeholder: "you@company.com",
    required: true,
  },
  {
    id: nanoid(),
    label: "Message",
    type: "textarea" as const,
    placeholder: "Tell us about your project...",
    required: true,
  },
];

const baseStyle: BuilderElementStyle = {
  padding: 24,
  gap: 16,
  borderRadius: 28,
  textAlign: "left",
  opacity: 1,
};

const baseContent: BuilderElementContent = {
  text: "Add your story here.",
  eyebrow: "",
  headingLevel: "h2",
  src: "https://images.unsplash.com/photo-1522542550221-31fd19575a2d?auto=format&fit=crop&w=1200&q=80",
  alt: "Placeholder image",
  caption: "",
  title: "Let's build something memorable",
  intro: "Collect leads, questions, and project requests without touching code.",
  submitLabel: "Send message",
  fields: defaultFields,
};

const defaultLayoutByType: Record<BuilderElementType, BuilderElementLayout> = {
  container: { x: 40, y: 40, width: 520, height: 320, zIndex: 1 },
  text: { x: 40, y: 40, width: 360, height: 220, zIndex: 2 },
  image: { x: 440, y: 60, width: 360, height: 280, zIndex: 2 },
  form: { x: 120, y: 120, width: 420, height: 440, zIndex: 2 },
};

export function createElementTemplate(
  type: BuilderElementType,
  pageId: string,
  parentId: string | null,
  overrides: ElementOverrides = {},
) {
  const id = nanoid();

  return {
    id,
    pageId,
    parentId,
    childrenIds: [],
    type,
    name: overrides.name ?? elementLabels[type],
    locked: overrides.locked,
    layout: {
      ...defaultLayoutByType[type],
      ...overrides.layout,
    },
    style: {
      ...baseStyle,
      ...overrides.style,
    },
    content: {
      ...baseContent,
      ...overrides.content,
    },
  } satisfies BuilderElement;
}

function linkChild(
  elements: Record<string, BuilderElement>,
  parentId: string,
  childId: string,
) {
  elements[parentId]?.childrenIds.push(childId);
}

export function createBlankPage(name: string, index: number) {
  const pageId = nanoid();
  const root = createElementTemplate("container", pageId, null, {
    name: `${name} Root`,
    locked: true,
    layout: { x: 0, y: 0, width: 1160, height: 760, zIndex: 0 },
    style: {
      padding: 0,
      borderRadius: 36,
    },
    content: {
      title: `${name} canvas`,
    },
  });

  const intro = createElementTemplate("text", pageId, root.id, {
    name: `${name} Intro`,
    layout: { x: 48, y: 48, width: 420, height: 200, zIndex: 2 },
    content: {
      eyebrow: "New Page",
      headingLevel: "h2",
      text: `${name}\nStart with a hero section, add supporting content, and nest containers for structure.`,
    },
  });

  const elements: Record<string, BuilderElement> = {
    [root.id]: root,
    [intro.id]: intro,
  };

  linkChild(elements, root.id, intro.id);

  return {
    page: {
      id: pageId,
      name,
      description: `Fresh page ${index + 1} for your website.`,
      rootId: root.id,
    } satisfies BuilderPage,
    elements,
    focusElementId: intro.id,
  };
}

export function buildInitialProject(): ProjectSeed {
  const pages: BuilderPage[] = [];
  const elements: Record<string, BuilderElement> = {};
  const backendActions: BuilderAutomation[] = [];

  const homePageId = nanoid();
  const homeRoot = createElementTemplate("container", homePageId, null, {
    name: "Home Root",
    locked: true,
    layout: { x: 0, y: 0, width: 1160, height: 760, zIndex: 0 },
    style: { padding: 0, borderRadius: 36 },
  });

  const heroText = createElementTemplate("text", homePageId, homeRoot.id, {
    name: "Hero Copy",
    layout: { x: 52, y: 52, width: 468, height: 250, zIndex: 2 },
    content: {
      eyebrow: "Website Builder",
      headingLevel: "h1",
      text: "Design airy multi-page sites.\nDrag blocks in, nest them inside containers, and ship polished informational pages without writing a line of frontend code.",
    },
  });

  const heroImage = createElementTemplate("image", homePageId, homeRoot.id, {
    name: "Hero Image",
    layout: { x: 584, y: 54, width: 514, height: 278, zIndex: 2 },
    content: {
      src: "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1200&q=80",
      alt: "Designer working on a soft colorful interface",
      caption: "Preview how your finished site feels across pages.",
    },
    style: {
      borderRadius: 30,
    },
  });

  const highlights = createElementTemplate("container", homePageId, homeRoot.id, {
    name: "Highlights",
    layout: { x: 52, y: 348, width: 1048, height: 300, zIndex: 1 },
    content: {
      title: "Highlights",
    },
    style: {
      padding: 20,
      borderRadius: 32,
    },
  });

  const highlightA = createElementTemplate("text", homePageId, highlights.id, {
    name: "Nested Card A",
    layout: { x: 18, y: 58, width: 300, height: 190, zIndex: 2 },
    content: {
      eyebrow: "Preset Themes",
      headingLevel: "h3",
      text: "Ten ready-to-go visual systems.\nSwap between Minimalist, Cyberpunk, Elegant Serif, and more in one click.",
    },
  });

  const highlightB = createElementTemplate("text", homePageId, highlights.id, {
    name: "Nested Card B",
    layout: { x: 356, y: 58, width: 300, height: 190, zIndex: 2 },
    content: {
      eyebrow: "Nested Layouts",
      headingLevel: "h3",
      text: "Place boxes inside boxes.\nContainers behave like reusable sections that can hold text, media, and forms.",
    },
  });

  const highlightC = createElementTemplate("text", homePageId, highlights.id, {
    name: "Nested Card C",
    layout: { x: 694, y: 58, width: 320, height: 190, zIndex: 2 },
    content: {
      eyebrow: "Simple Automations",
      headingLevel: "h3",
      text: "Connect forms to actions.\nUse the backend view to send emails, store data, or trigger webhooks visually.",
    },
  });

  pages.push({
    id: homePageId,
    name: "Home",
    description: "Hero section and nested highlights grid.",
    rootId: homeRoot.id,
  });

  Object.assign(elements, {
    [homeRoot.id]: homeRoot,
    [heroText.id]: heroText,
    [heroImage.id]: heroImage,
    [highlights.id]: highlights,
    [highlightA.id]: highlightA,
    [highlightB.id]: highlightB,
    [highlightC.id]: highlightC,
  });

  linkChild(elements, homeRoot.id, heroText.id);
  linkChild(elements, homeRoot.id, heroImage.id);
  linkChild(elements, homeRoot.id, highlights.id);
  linkChild(elements, highlights.id, highlightA.id);
  linkChild(elements, highlights.id, highlightB.id);
  linkChild(elements, highlights.id, highlightC.id);

  const aboutPageId = nanoid();
  const aboutRoot = createElementTemplate("container", aboutPageId, null, {
    name: "About Root",
    locked: true,
    layout: { x: 0, y: 0, width: 1160, height: 760, zIndex: 0 },
    style: { padding: 0, borderRadius: 36 },
  });

  const aboutStory = createElementTemplate("text", aboutPageId, aboutRoot.id, {
    name: "Story",
    layout: { x: 56, y: 64, width: 480, height: 230, zIndex: 2 },
    content: {
      eyebrow: "About",
      headingLevel: "h1",
      text: "Tell a stronger story.\nUse this page for your mission, process, studio values, or service breakdown.",
    },
  });

  const values = createElementTemplate("container", aboutPageId, aboutRoot.id, {
    name: "Values Section",
    layout: { x: 56, y: 324, width: 1046, height: 290, zIndex: 1 },
    style: { padding: 18, borderRadius: 32 },
  });

  const valuesA = createElementTemplate("text", aboutPageId, values.id, {
    name: "Value One",
    layout: { x: 24, y: 60, width: 290, height: 176, zIndex: 2 },
    content: {
      eyebrow: "01",
      headingLevel: "h3",
      text: "Clarity first.\nShape complicated ideas into page structures that people can scan in seconds.",
    },
  });

  const valuesB = createElementTemplate("text", aboutPageId, values.id, {
    name: "Value Two",
    layout: { x: 356, y: 60, width: 290, height: 176, zIndex: 2 },
    content: {
      eyebrow: "02",
      headingLevel: "h3",
      text: "Soft builder UI.\nCreate inside a claymorphism workspace that feels tactile and playful instead of sterile.",
    },
  });

  const valuesC = createElementTemplate("image", aboutPageId, values.id, {
    name: "Studio Image",
    layout: { x: 688, y: 42, width: 320, height: 208, zIndex: 2 },
    content: {
      src: "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1200&q=80",
      alt: "Creative studio interior",
      caption: "Mix editorial layouts with no-code page composition.",
    },
  });

  pages.push({
    id: aboutPageId,
    name: "About",
    description: "Brand story plus a nested values section.",
    rootId: aboutRoot.id,
  });

  Object.assign(elements, {
    [aboutRoot.id]: aboutRoot,
    [aboutStory.id]: aboutStory,
    [values.id]: values,
    [valuesA.id]: valuesA,
    [valuesB.id]: valuesB,
    [valuesC.id]: valuesC,
  });

  linkChild(elements, aboutRoot.id, aboutStory.id);
  linkChild(elements, aboutRoot.id, values.id);
  linkChild(elements, values.id, valuesA.id);
  linkChild(elements, values.id, valuesB.id);
  linkChild(elements, values.id, valuesC.id);

  const contactPageId = nanoid();
  const contactRoot = createElementTemplate("container", contactPageId, null, {
    name: "Contact Root",
    locked: true,
    layout: { x: 0, y: 0, width: 1160, height: 760, zIndex: 0 },
    style: { padding: 0, borderRadius: 36 },
  });

  const contactLead = createElementTemplate("text", contactPageId, contactRoot.id, {
    name: "Contact Intro",
    layout: { x: 74, y: 108, width: 410, height: 220, zIndex: 2 },
    content: {
      eyebrow: "Contact",
      headingLevel: "h1",
      text: "Turn your contact page into a system.\nWire form submissions to email, a database, or a webhook without surfacing backend complexity to the client.",
    },
  });

  const contactForm = createElementTemplate("form", contactPageId, contactRoot.id, {
    name: "Primary Contact Form",
    layout: { x: 594, y: 84, width: 420, height: 480, zIndex: 2 },
    content: {
      title: "Start a project",
      intro:
        "Share the kind of website you are building and how soon you want to launch.",
      submitLabel: "Request a proposal",
      fields: [
        {
          id: nanoid(),
          label: "Name",
          type: "text",
          placeholder: "Alex Morgan",
          required: true,
        },
        {
          id: nanoid(),
          label: "Email",
          type: "email",
          placeholder: "alex@company.com",
          required: true,
        },
        {
          id: nanoid(),
          label: "Timeline",
          type: "text",
          placeholder: "2-4 weeks",
        },
        {
          id: nanoid(),
          label: "Project Brief",
          type: "textarea",
          placeholder: "Tell us what you want the website to communicate.",
          required: true,
        },
      ],
    },
    style: {
      borderRadius: 32,
    },
  });

  pages.push({
    id: contactPageId,
    name: "Contact",
    description: "Lead capture form with backend actions attached.",
    rootId: contactRoot.id,
  });

  Object.assign(elements, {
    [contactRoot.id]: contactRoot,
    [contactLead.id]: contactLead,
    [contactForm.id]: contactForm,
  });

  linkChild(elements, contactRoot.id, contactLead.id);
  linkChild(elements, contactRoot.id, contactForm.id);

  backendActions.push(
    {
      id: nanoid(),
      sourceElementId: contactForm.id,
      actionType: "email",
      label: backendActionCatalog[0].label,
      enabled: true,
      config: {
        target: "hello@nimbusstudio.dev",
        note: "Primary owner notification",
      },
    },
    {
      id: nanoid(),
      sourceElementId: contactForm.id,
      actionType: "database",
      label: backendActionCatalog[1].label,
      enabled: true,
      config: {
        target: "crm.incoming_leads",
        note: "Archive each submission for the sales team",
      },
    },
  );

  return {
    projectName: "Nimbus Studio Builder",
    themeId: "glassmorphism",
    currentPageId: homePageId,
    selectedElementId: heroText.id,
    pages,
    elements,
    backendActions,
    hasHydrated: false,
  };
}
