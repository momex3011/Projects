import { UTA } from "./theme";

export type ThemeTier = "basic" | "premium" | "event";
export type ThemeAppearance = "light" | "dark";

export type ThemeGradient = {
  colors: [string, string, string];
  start: { x: number; y: number };
  end: { x: number; y: number };
  angleLabel: string;
  intensity: number;
};

export type ThemePalette = {
  background: string;
  surface: string;
  surfaceAlt: string;
  text: string;
  mutedText: string;
  accent: string;
  accentStrong: string;
  accentText: string;
  border: string;
  tabBarBackground: string;
  tabBarBorder: string;
  overlay: string;
  glowPrimary: string;
  glowSecondary: string;
  inputBackground: string;
  isDark: boolean;
};

export type BackgroundTheme = {
  id: string;
  name: string;
  tier: ThemeTier;
  appearance: ThemeAppearance;
  price: number;
  description: string;
  vibe: string;
  preview: [string, string, string];
  gradient: ThemeGradient;
  palette: ThemePalette;
};

const DIAGONAL_SOFT: Pick<ThemeGradient, "start" | "end"> = {
  start: { x: 0, y: 0 },
  end: { x: 1, y: 1 },
};

const DIAGONAL_SHARP: Pick<ThemeGradient, "start" | "end"> = {
  start: { x: 0.05, y: 0.15 },
  end: { x: 1, y: 0.85 },
};

export const DEFAULT_THEME_ID = "light-mode";

export const BACKGROUND_THEMES: BackgroundTheme[] = [
  {
    id: "light-mode",
    name: "Light Mode",
    tier: "basic",
    appearance: "light",
    price: 0,
    description: "The default clean campus look with a soft pastel wash.",
    vibe: "Bright campus dashboard",
    preview: ["#F8EFFF", "#EEF3FF", "#FFF2E3"],
    gradient: {
      colors: ["#F8EFFF", "#EEF3FF", "#FFF2E3"],
      ...DIAGONAL_SOFT,
      angleLabel: "135 deg",
      intensity: 34,
    },
    palette: {
      background: UTA.offWhite,
      surface: "#FFFFFF",
      surfaceAlt: "#F0E9FD",
      text: UTA.gray800,
      mutedText: UTA.gray500,
      accent: UTA.royalBlue,
      accentStrong: UTA.blazeOrange,
      accentText: "#FFFFFF",
      border: "#E4E2F4",
      tabBarBackground: "#FFFFFF",
      tabBarBorder: UTA.gray100,
      overlay: "rgba(26, 28, 42, 0.42)",
      glowPrimary: "rgba(201, 174, 255, 0.28)",
      glowSecondary: "rgba(255, 196, 144, 0.2)",
      inputBackground: "#FFFFFF",
      isDark: false,
    },
  },
  {
    id: "dark-mode",
    name: "Dark Mode",
    tier: "basic",
    appearance: "dark",
    price: 100,
    description: "Dark surfaces with muted plum undertones for late-night sessions.",
    vibe: "Quiet after-hours",
    preview: ["#2A1A29", "#1B1727", "#252F3C"],
    gradient: {
      colors: ["#2A1A29", "#1B1727", "#252F3C"],
      ...DIAGONAL_SOFT,
      angleLabel: "180 deg",
      intensity: 46,
    },
    palette: {
      background: "#18121B",
      surface: "#241B28",
      surfaceAlt: "#302235",
      text: "#F9F5FF",
      mutedText: "#D4C6DA",
      accent: "#8B80F9",
      accentStrong: "#C084FC",
      accentText: "#FFFFFF",
      border: "#3D2C44",
      tabBarBackground: "#1A141E",
      tabBarBorder: "#2B1E31",
      overlay: "rgba(4, 3, 8, 0.72)",
      glowPrimary: "rgba(131, 105, 255, 0.2)",
      glowSecondary: "rgba(255, 123, 172, 0.14)",
      inputBackground: "#2A1D31",
      isDark: true,
    },
  },
  {
    id: "soft-blue",
    name: "Soft Blue",
    tier: "basic",
    appearance: "light",
    price: 125,
    description: "A calm pastel blend of blue, mint, and lavender.",
    vibe: "Airy and relaxed",
    preview: ["#A8DBFF", "#C8D8FF", "#D8F0E2"],
    gradient: {
      colors: ["#A8DBFF", "#C8D8FF", "#D8F0E2"],
      ...DIAGONAL_SOFT,
      angleLabel: "145 deg",
      intensity: 51,
    },
    palette: {
      background: "#EAF4FF",
      surface: "#FFFFFF",
      surfaceAlt: "#DDECFF",
      text: "#18385A",
      mutedText: "#617A96",
      accent: "#4F7DFF",
      accentStrong: "#5CC6B1",
      accentText: "#FFFFFF",
      border: "#CCDAF2",
      tabBarBackground: "#F6FAFF",
      tabBarBorder: "#DDE8F8",
      overlay: "rgba(15, 31, 48, 0.36)",
      glowPrimary: "rgba(86, 156, 255, 0.22)",
      glowSecondary: "rgba(140, 227, 205, 0.18)",
      inputBackground: "#FFFFFF",
      isDark: false,
    },
  },
  {
    id: "campus-orange",
    name: "Campus Orange",
    tier: "basic",
    appearance: "light",
    price: 150,
    description: "A warmer UTA-inspired blend with peach and tangerine energy.",
    vibe: "Game day momentum",
    preview: ["#FFBE7B", "#FFDAB8", "#FF955A"],
    gradient: {
      colors: ["#FFBE7B", "#FFDAB8", "#FF955A"],
      ...DIAGONAL_SHARP,
      angleLabel: "160 deg",
      intensity: 62,
    },
    palette: {
      background: "#FFF3E8",
      surface: "#FFFFFF",
      surfaceAlt: "#FFE4CF",
      text: "#553118",
      mutedText: "#896246",
      accent: "#F58025",
      accentStrong: "#EB5F28",
      accentText: "#FFFFFF",
      border: "#FFD8BE",
      tabBarBackground: "#FFF8F1",
      tabBarBorder: "#FFE6D2",
      overlay: "rgba(63, 34, 18, 0.34)",
      glowPrimary: "rgba(245, 128, 37, 0.2)",
      glowSecondary: "rgba(255, 177, 112, 0.18)",
      inputBackground: "#FFFFFF",
      isDark: false,
    },
  },
  {
    id: "library-mode",
    name: "Library Mode",
    tier: "premium",
    appearance: "dark",
    price: 275,
    description: "Dim, low-contrast sepia tones designed for focused study sessions.",
    vibe: "Quiet stacks at midnight",
    preview: ["#40382D", "#2A241D", "#685D49"],
    gradient: {
      colors: ["#40382D", "#2A241D", "#685D49"],
      ...DIAGONAL_SOFT,
      angleLabel: "170 deg",
      intensity: 39,
    },
    palette: {
      background: "#221D18",
      surface: "#302820",
      surfaceAlt: "#3C342A",
      text: "#F4EBDD",
      mutedText: "#CFC1AE",
      accent: "#B69B74",
      accentStrong: "#E1C287",
      accentText: "#241B12",
      border: "#4A4034",
      tabBarBackground: "#251F19",
      tabBarBorder: "#3A3127",
      overlay: "rgba(8, 6, 4, 0.76)",
      glowPrimary: "rgba(180, 152, 108, 0.14)",
      glowSecondary: "rgba(113, 94, 67, 0.18)",
      inputBackground: "#382F25",
      isDark: true,
    },
  },
  {
    id: "neon-purple",
    name: "Neon Purple",
    tier: "premium",
    appearance: "dark",
    price: 325,
    description: "A vivid electric mix of violet, cobalt, and magenta.",
    vibe: "Arcade neon",
    preview: ["#7C3AED", "#2563EB", "#EC4899"],
    gradient: {
      colors: ["#7C3AED", "#2563EB", "#EC4899"],
      ...DIAGONAL_SHARP,
      angleLabel: "125 deg",
      intensity: 88,
    },
    palette: {
      background: "#1A1130",
      surface: "#251744",
      surfaceAlt: "#331F59",
      text: "#FAF5FF",
      mutedText: "#D8C6F6",
      accent: "#C084FC",
      accentStrong: "#EC4899",
      accentText: "#FFFFFF",
      border: "#4A2D74",
      tabBarBackground: "#170F2B",
      tabBarBorder: "#2B1B45",
      overlay: "rgba(6, 3, 13, 0.76)",
      glowPrimary: "rgba(124, 58, 237, 0.26)",
      glowSecondary: "rgba(59, 130, 246, 0.22)",
      inputBackground: "#2A1A4C",
      isDark: true,
    },
  },
  {
    id: "gradient-sunset",
    name: "Gradient Sunset",
    tier: "premium",
    appearance: "light",
    price: 375,
    description: "A colorful orange-to-pink sunset blend with more motion.",
    vibe: "Golden hour on campus",
    preview: ["#FFBE6B", "#FF8FB1", "#FF6B6B"],
    gradient: {
      colors: ["#FFBE6B", "#FF8FB1", "#FF6B6B"],
      ...DIAGONAL_SHARP,
      angleLabel: "140 deg",
      intensity: 82,
    },
    palette: {
      background: "#FFF0F1",
      surface: "#FFFFFF",
      surfaceAlt: "#FFE0E8",
      text: "#5E2036",
      mutedText: "#946075",
      accent: "#FF5C8A",
      accentStrong: "#FF7A45",
      accentText: "#FFFFFF",
      border: "#FFD0DB",
      tabBarBackground: "#FFF7F8",
      tabBarBorder: "#FFE0E5",
      overlay: "rgba(70, 24, 38, 0.32)",
      glowPrimary: "rgba(255, 122, 69, 0.18)",
      glowSecondary: "rgba(255, 92, 138, 0.18)",
      inputBackground: "#FFFFFF",
      isDark: false,
    },
  },
  {
    id: "midnight-glow",
    name: "Midnight Black + Accent Glow",
    tier: "premium",
    appearance: "dark",
    price: 450,
    description: "A black-blue base with electric cyan and indigo highlights.",
    vibe: "Tech noir",
    preview: ["#060814", "#1F2A5A", "#00C2FF"],
    gradient: {
      colors: ["#060814", "#1F2A5A", "#00C2FF"],
      ...DIAGONAL_SHARP,
      angleLabel: "205 deg",
      intensity: 73,
    },
    palette: {
      background: "#060814",
      surface: "#10182F",
      surfaceAlt: "#162247",
      text: "#F4FAFF",
      mutedText: "#C6D3E8",
      accent: "#5AD7FF",
      accentStrong: "#7C8CFF",
      accentText: "#08111E",
      border: "#24325A",
      tabBarBackground: "#050914",
      tabBarBorder: "#162344",
      overlay: "rgba(1, 3, 10, 0.8)",
      glowPrimary: "rgba(0, 194, 255, 0.18)",
      glowSecondary: "rgba(124, 140, 255, 0.2)",
      inputBackground: "#111B34",
      isDark: true,
    },
  },
  {
    id: "aurora-mint",
    name: "Aurora Mint",
    tier: "premium",
    appearance: "dark",
    price: 400,
    description: "A deep teal-to-green gradient that feels like an aurora over glass.",
    vibe: "Cool atmospheric glow",
    preview: ["#0F3B46", "#1F7A73", "#77E6B6"],
    gradient: {
      colors: ["#0F3B46", "#1F7A73", "#77E6B6"],
      ...DIAGONAL_SOFT,
      angleLabel: "150 deg",
      intensity: 67,
    },
    palette: {
      background: "#0C2128",
      surface: "#133039",
      surfaceAlt: "#19424C",
      text: "#EEFFF9",
      mutedText: "#B9D9D1",
      accent: "#5CE0C5",
      accentStrong: "#9CF871",
      accentText: "#07231D",
      border: "#24515A",
      tabBarBackground: "#0E262D",
      tabBarBorder: "#1B434A",
      overlay: "rgba(1, 8, 8, 0.74)",
      glowPrimary: "rgba(92, 224, 197, 0.18)",
      glowSecondary: "rgba(156, 248, 113, 0.14)",
      inputBackground: "#183842",
      isDark: true,
    },
  },
  {
    id: "finals-week",
    name: "Finals Week Theme",
    tier: "event",
    appearance: "dark",
    price: 350,
    description: "Focused violet and hot pink energy with a little urgency built in.",
    vibe: "Crunch mode",
    preview: ["#5936C1", "#D946EF", "#F59E0B"],
    gradient: {
      colors: ["#5936C1", "#D946EF", "#F59E0B"],
      ...DIAGONAL_SHARP,
      angleLabel: "145 deg",
      intensity: 79,
    },
    palette: {
      background: "#251543",
      surface: "#311B58",
      surfaceAlt: "#44257B",
      text: "#FAF5FF",
      mutedText: "#DECFFC",
      accent: "#C084FC",
      accentStrong: "#F59E0B",
      accentText: "#24163D",
      border: "#55328A",
      tabBarBackground: "#241540",
      tabBarBorder: "#3A2462",
      overlay: "rgba(7, 4, 17, 0.76)",
      glowPrimary: "rgba(217, 70, 239, 0.2)",
      glowSecondary: "rgba(245, 158, 11, 0.16)",
      inputBackground: "#39205F",
      isDark: true,
    },
  },
  {
    id: "holiday-cheer",
    name: "Holiday Theme",
    tier: "event",
    appearance: "dark",
    price: 375,
    description: "Deep green with festive gold and cranberry highlights.",
    vibe: "Seasonal night lights",
    preview: ["#0F5132", "#1F9D55", "#B91C1C"],
    gradient: {
      colors: ["#0F5132", "#1F9D55", "#B91C1C"],
      ...DIAGONAL_SHARP,
      angleLabel: "155 deg",
      intensity: 71,
    },
    palette: {
      background: "#10261C",
      surface: "#18382B",
      surfaceAlt: "#214B38",
      text: "#F6FFF9",
      mutedText: "#CAE3D4",
      accent: "#39D98A",
      accentStrong: "#F87171",
      accentText: "#092116",
      border: "#2D5A46",
      tabBarBackground: "#112A1F",
      tabBarBorder: "#244734",
      overlay: "rgba(2, 9, 6, 0.78)",
      glowPrimary: "rgba(57, 217, 138, 0.14)",
      glowSecondary: "rgba(248, 113, 113, 0.16)",
      inputBackground: "#214034",
      isDark: true,
    },
  },
  {
    id: "uta-spirit",
    name: "UTA Spirit Theme",
    tier: "event",
    appearance: "dark",
    price: 425,
    description: "A bold blue-and-orange campus spirit blend with strong contrast.",
    vibe: "Maverick pride",
    preview: ["#0064B1", "#3B82F6", "#F58025"],
    gradient: {
      colors: ["#0064B1", "#3B82F6", "#F58025"],
      ...DIAGONAL_SHARP,
      angleLabel: "135 deg",
      intensity: 84,
    },
    palette: {
      background: "#07203A",
      surface: "#0C2D4E",
      surfaceAlt: "#123C67",
      text: "#F6FBFF",
      mutedText: "#C9D8EB",
      accent: "#6CB8FF",
      accentStrong: "#F58025",
      accentText: "#FFFFFF",
      border: "#22517D",
      tabBarBackground: "#081F37",
      tabBarBorder: "#173C60",
      overlay: "rgba(3, 7, 14, 0.78)",
      glowPrimary: "rgba(0, 100, 177, 0.24)",
      glowSecondary: "rgba(245, 128, 37, 0.18)",
      inputBackground: "#14375C",
      isDark: true,
    },
  },
];

export function getBackgroundTheme(themeId?: string): BackgroundTheme {
  return BACKGROUND_THEMES.find((theme) => theme.id === themeId) ?? BACKGROUND_THEMES[0];
}

export function groupThemesByTier() {
  return {
    basic: BACKGROUND_THEMES.filter((theme) => theme.tier === "basic"),
    premium: BACKGROUND_THEMES.filter((theme) => theme.tier === "premium"),
    event: BACKGROUND_THEMES.filter((theme) => theme.tier === "event"),
  };
}
