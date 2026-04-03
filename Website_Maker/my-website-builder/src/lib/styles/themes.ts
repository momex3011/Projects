import type { CSSProperties } from "react";

import type { ThemePresetId } from "@/lib/builder-types";

export interface ThemePreset {
  id: ThemePresetId;
  label: string;
  tagline: string;
  surfaceTreatment: "minimal" | "soft" | "glass" | "hard" | "neon";
  variables: {
    background: string;
    surface: string;
    surfaceAlt: string;
    text: string;
    muted: string;
    accent: string;
    border: string;
    shadow: string;
    radius: string;
    borderWidth: string;
    borderStyle: string;
    headingFont: string;
    bodyFont: string;
    ambient: string;
  };
}

export const siteThemes: ThemePreset[] = [
  {
    id: "minimalist",
    label: "Minimalist",
    tagline: "Quiet whitespace and editorial restraint.",
    surfaceTreatment: "minimal",
    variables: {
      background: "#fcfcfb",
      surface: "rgba(255,255,255,0.9)",
      surfaceAlt: "rgba(247,247,246,0.95)",
      text: "#171717",
      muted: "#666666",
      accent: "#0f766e",
      border: "rgba(23,23,23,0.08)",
      shadow: "0 18px 40px rgba(17,24,39,0.06)",
      radius: "24px",
      borderWidth: "1px",
      borderStyle: "solid",
      headingFont: "var(--font-space-grotesk)",
      bodyFont: "var(--font-manrope)",
      ambient:
        "radial-gradient(circle at 12% 16%, rgba(255,255,255,0.7), transparent 20%), radial-gradient(circle at 100% 0%, rgba(15,118,110,0.08), transparent 24%)",
    },
  },
  {
    id: "brutalism",
    label: "Brutalism",
    tagline: "Loud color blocks and unapologetic borders.",
    surfaceTreatment: "hard",
    variables: {
      background: "#ffef5c",
      surface: "#fffdf6",
      surfaceAlt: "#ffd8f6",
      text: "#111111",
      muted: "#222222",
      accent: "#ff0054",
      border: "#111111",
      shadow: "10px 10px 0 #111111",
      radius: "8px",
      borderWidth: "4px",
      borderStyle: "solid",
      headingFont: "var(--font-space-grotesk)",
      bodyFont: "var(--font-ibm-plex-mono)",
      ambient:
        "linear-gradient(45deg, rgba(255,255,255,0.4) 0%, transparent 30%), radial-gradient(circle at 92% 10%, rgba(255,0,84,0.12), transparent 16%)",
    },
  },
  {
    id: "neumorphism",
    label: "Neumorphism",
    tagline: "Soft depth with sculpted surfaces.",
    surfaceTreatment: "soft",
    variables: {
      background: "#e7ecf3",
      surface: "#eaf0f6",
      surfaceAlt: "#eef3f8",
      text: "#304251",
      muted: "#607386",
      accent: "#7b5cff",
      border: "rgba(255,255,255,0.75)",
      shadow:
        "16px 16px 34px rgba(163,177,198,0.48), -16px -16px 32px rgba(255,255,255,0.9)",
      radius: "30px",
      borderWidth: "1px",
      borderStyle: "solid",
      headingFont: "var(--font-space-grotesk)",
      bodyFont: "var(--font-manrope)",
      ambient:
        "radial-gradient(circle at 15% 15%, rgba(255,255,255,0.72), transparent 20%), radial-gradient(circle at 85% 85%, rgba(123,92,255,0.16), transparent 20%)",
    },
  },
  {
    id: "glassmorphism",
    label: "Glassmorphism",
    tagline: "Luminous layers with frosted surfaces.",
    surfaceTreatment: "glass",
    variables: {
      background:
        "linear-gradient(145deg, #daf1ff 0%, #f7d7ff 52%, #fff7ef 100%)",
      surface: "rgba(255,255,255,0.28)",
      surfaceAlt: "rgba(255,255,255,0.18)",
      text: "#12243c",
      muted: "#35506d",
      accent: "#8e46ff",
      border: "rgba(255,255,255,0.34)",
      shadow: "0 24px 54px rgba(60,73,110,0.18)",
      radius: "30px",
      borderWidth: "1px",
      borderStyle: "solid",
      headingFont: "var(--font-space-grotesk)",
      bodyFont: "var(--font-manrope)",
      ambient:
        "radial-gradient(circle at 14% 20%, rgba(255,255,255,0.75), transparent 18%), radial-gradient(circle at 100% 0%, rgba(142,70,255,0.2), transparent 22%), radial-gradient(circle at 82% 90%, rgba(123,223,242,0.25), transparent 24%)",
    },
  },
  {
    id: "material",
    label: "Material Design",
    tagline: "Balanced hierarchy with purposeful shadows.",
    surfaceTreatment: "soft",
    variables: {
      background: "#f4f7fb",
      surface: "#ffffff",
      surfaceAlt: "#eef3f9",
      text: "#102a43",
      muted: "#486581",
      accent: "#2563eb",
      border: "rgba(37,99,235,0.12)",
      shadow: "0 18px 36px rgba(37,99,235,0.14)",
      radius: "22px",
      borderWidth: "1px",
      borderStyle: "solid",
      headingFont: "var(--font-space-grotesk)",
      bodyFont: "var(--font-manrope)",
      ambient:
        "radial-gradient(circle at 15% 12%, rgba(255,255,255,0.8), transparent 22%), radial-gradient(circle at 100% 0%, rgba(37,99,235,0.14), transparent 18%)",
    },
  },
  {
    id: "cyberpunk",
    label: "Cyberpunk",
    tagline: "Neon glow, dark chrome, and electric edges.",
    surfaceTreatment: "neon",
    variables: {
      background: "#0d0221",
      surface: "rgba(18, 7, 36, 0.92)",
      surfaceAlt: "rgba(22, 10, 44, 0.96)",
      text: "#f9f7ff",
      muted: "#b9a9ff",
      accent: "#08f7fe",
      border: "rgba(255,0,255,0.48)",
      shadow:
        "0 0 0 1px rgba(255,0,255,0.24), 0 24px 54px rgba(8,247,254,0.18)",
      radius: "16px",
      borderWidth: "1px",
      borderStyle: "solid",
      headingFont: "var(--font-space-grotesk)",
      bodyFont: "var(--font-ibm-plex-mono)",
      ambient:
        "radial-gradient(circle at 12% 16%, rgba(8,247,254,0.18), transparent 16%), radial-gradient(circle at 88% 10%, rgba(255,0,255,0.2), transparent 16%), linear-gradient(180deg, rgba(255,255,255,0.02), transparent 22%)",
    },
  },
  {
    id: "corporate-flat",
    label: "Corporate Flat",
    tagline: "Clean enterprise visuals with steady confidence.",
    surfaceTreatment: "minimal",
    variables: {
      background: "#eef3f8",
      surface: "#ffffff",
      surfaceAlt: "#f7fafd",
      text: "#11324d",
      muted: "#5b7c99",
      accent: "#0ea5e9",
      border: "rgba(17,50,77,0.08)",
      shadow: "0 12px 24px rgba(17,50,77,0.08)",
      radius: "18px",
      borderWidth: "1px",
      borderStyle: "solid",
      headingFont: "var(--font-space-grotesk)",
      bodyFont: "var(--font-manrope)",
      ambient:
        "radial-gradient(circle at 100% 0%, rgba(14,165,233,0.1), transparent 18%), radial-gradient(circle at 0% 100%, rgba(15,118,110,0.08), transparent 20%)",
    },
  },
  {
    id: "retro-90s",
    label: "Retro 90s",
    tagline: "Punchy gradients and nostalgic poster energy.",
    surfaceTreatment: "hard",
    variables: {
      background: "linear-gradient(145deg, #fff2b2 0%, #ffd1dc 48%, #d2d2ff 100%)",
      surface: "#fff9f2",
      surfaceAlt: "#eaf5ff",
      text: "#2f1443",
      muted: "#6e4f89",
      accent: "#ff6b6b",
      border: "#2f1443",
      shadow: "8px 8px 0 rgba(47,20,67,0.95)",
      radius: "20px",
      borderWidth: "3px",
      borderStyle: "solid",
      headingFont: "var(--font-space-grotesk)",
      bodyFont: "var(--font-manrope)",
      ambient:
        "radial-gradient(circle at 12% 18%, rgba(255,255,255,0.5), transparent 18%), radial-gradient(circle at 90% 12%, rgba(255,107,107,0.18), transparent 16%), radial-gradient(circle at 82% 88%, rgba(114,9,183,0.16), transparent 16%)",
    },
  },
  {
    id: "high-contrast",
    label: "High-Contrast",
    tagline: "Accessible punch with stark visual contrast.",
    surfaceTreatment: "hard",
    variables: {
      background: "#ffffff",
      surface: "#ffffff",
      surfaceAlt: "#f3f4f6",
      text: "#000000",
      muted: "#1f2937",
      accent: "#ffb703",
      border: "#000000",
      shadow: "0 0 0 3px rgba(0,0,0,1)",
      radius: "12px",
      borderWidth: "3px",
      borderStyle: "solid",
      headingFont: "var(--font-space-grotesk)",
      bodyFont: "var(--font-manrope)",
      ambient:
        "radial-gradient(circle at 100% 0%, rgba(255,183,3,0.18), transparent 18%), linear-gradient(180deg, rgba(0,0,0,0.01), transparent 18%)",
    },
  },
  {
    id: "elegant-serif",
    label: "Elegant Serif",
    tagline: "Quiet luxury with formal typography.",
    surfaceTreatment: "minimal",
    variables: {
      background: "#f9f4ec",
      surface: "rgba(255,249,242,0.92)",
      surfaceAlt: "rgba(247,239,229,0.94)",
      text: "#2f1d1b",
      muted: "#6c544f",
      accent: "#8c5e58",
      border: "rgba(47,29,27,0.12)",
      shadow: "0 18px 38px rgba(77,54,45,0.1)",
      radius: "28px",
      borderWidth: "1px",
      borderStyle: "solid",
      headingFont: "var(--font-cormorant)",
      bodyFont: "var(--font-manrope)",
      ambient:
        "radial-gradient(circle at 15% 12%, rgba(255,255,255,0.7), transparent 20%), radial-gradient(circle at 100% 0%, rgba(140,94,88,0.12), transparent 18%)",
    },
  },
];

export const siteThemeMap = Object.fromEntries(
  siteThemes.map((theme) => [theme.id, theme]),
) as Record<ThemePresetId, ThemePreset>;

export function getSiteThemeStyle(themeId: ThemePresetId) {
  const theme = siteThemeMap[themeId];

  return {
    "--site-bg": theme.variables.background,
    "--site-surface": theme.variables.surface,
    "--site-surface-alt": theme.variables.surfaceAlt,
    "--site-text": theme.variables.text,
    "--site-muted": theme.variables.muted,
    "--site-accent": theme.variables.accent,
    "--site-border": theme.variables.border,
    "--site-shadow": theme.variables.shadow,
    "--site-radius": theme.variables.radius,
    "--site-border-width": theme.variables.borderWidth,
    "--site-border-style": theme.variables.borderStyle,
    "--site-font-heading": theme.variables.headingFont,
    "--site-font-body": theme.variables.bodyFont,
    "--site-ambient": theme.variables.ambient,
  } as CSSProperties;
}
