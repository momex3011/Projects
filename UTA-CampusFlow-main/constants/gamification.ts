import { UTA } from "./theme";

export type IdentityTier = "starter" | "basic" | "premium" | "achievement";
export type IdentityKind = "badge" | "title" | "frame";

export type CollectibleArtSpec = {
  icon: string;
  gradientColors: [string, string];
  iconColor: string;
  rimColor: string;
  sparkleColor: string;
};

type IdentityItemBase = {
  id: string;
  kind: IdentityKind;
  name: string;
  previewLabel: string;
  description: string;
  tier: IdentityTier;
  price: number;
  purchasable: boolean;
  art: CollectibleArtSpec;
};

export type BadgeItem = IdentityItemBase & {
  kind: "badge";
  shortLabel: string;
  backgroundColor: string;
  textColor: string;
  accentColor: string;
};

export type TitleItem = IdentityItemBase & {
  kind: "title";
  accentColor: string;
  textColor: string;
  backgroundColor: string;
};

export type FrameItem = IdentityItemBase & {
  kind: "frame";
  borderColors: [string, string];
  glowColor: string;
  plateColor: string;
};

export type AchievementDefinition = {
  id: string;
  name: string;
  previewLabel: string;
  description: string;
  requirementLabel: string;
  type: "submissions" | "streak";
  target: number;
  art: CollectibleArtSpec;
  reward?: {
    kind: IdentityKind;
    itemId: string;
  };
};

export type IdentityItem = BadgeItem | TitleItem | FrameItem;

export const DEFAULT_BADGE_ID = "mav-starter";
export const DEFAULT_TITLE_ID = "campus-helper";
export const DEFAULT_FRAME_ID = "classic-blue";

export const BADGE_ITEMS: BadgeItem[] = [
  {
    id: DEFAULT_BADGE_ID,
    kind: "badge",
    name: "Mav Starter",
    previewLabel: "Start",
    shortLabel: "Starter",
    description: "Default badge for every new Maverick reporter.",
    tier: "starter",
    price: 0,
    purchasable: false,
    backgroundColor: "#E8F1FA",
    textColor: UTA.royalBlue,
    accentColor: UTA.royalBlue,
    art: {
      icon: "star-four-points-circle",
      gradientColors: ["#F6F2FF", "#DDEAFF"],
      iconColor: UTA.royalBlue,
      rimColor: "#D7C7FF",
      sparkleColor: "#FFFFFF",
    },
  },
  {
    id: "top-reporter",
    kind: "badge",
    name: "Top Reporter",
    previewLabel: "Top",
    shortLabel: "Top",
    description: "Achievement badge for consistent report volume.",
    tier: "achievement",
    price: 0,
    purchasable: false,
    backgroundColor: "#FFF2D9",
    textColor: "#8A5A00",
    accentColor: UTA.gold,
    art: {
      icon: "trophy-award",
      gradientColors: ["#FFF7D6", "#FFD18A"],
      iconColor: "#8A5A00",
      rimColor: "#F4B13D",
      sparkleColor: "#FFF5C0",
    },
  },
  {
    id: "night-owl",
    kind: "badge",
    name: "Night Owl",
    previewLabel: "Night",
    shortLabel: "Night",
    description: "For late-night grinders who still keep the campus map fresh.",
    tier: "basic",
    price: 180,
    purchasable: true,
    backgroundColor: "#261D46",
    textColor: "#F3EBFF",
    accentColor: "#9B8CFF",
    art: {
      icon: "weather-night",
      gradientColors: ["#151231", "#6C4ED9"],
      iconColor: "#F3EBFF",
      rimColor: "#9B8CFF",
      sparkleColor: "#D7CCFF",
    },
  },
  {
    id: "trend-tracker",
    kind: "badge",
    name: "Trend Tracker",
    previewLabel: "Trend",
    shortLabel: "Trend",
    description: "Signals that you keep campus patterns updated often.",
    tier: "premium",
    price: 260,
    purchasable: true,
    backgroundColor: "#E8F8F1",
    textColor: "#146E4B",
    accentColor: "#1EB980",
    art: {
      icon: "chart-line-variant",
      gradientColors: ["#DAFFF0", "#79D9B1"],
      iconColor: "#146E4B",
      rimColor: "#1EB980",
      sparkleColor: "#F5FFF9",
    },
  },
  {
    id: "library-scout",
    kind: "badge",
    name: "Library Scout",
    previewLabel: "Scout",
    shortLabel: "Scout",
    description: "Perfect for users who care about study spaces and quiet corners.",
    tier: "basic",
    price: 150,
    purchasable: true,
    backgroundColor: "#F4EFE1",
    textColor: "#6C5521",
    accentColor: "#B98A2E",
    art: {
      icon: "bookshelf",
      gradientColors: ["#FFF8E6", "#D9C089"],
      iconColor: "#6C5521",
      rimColor: "#B98A2E",
      sparkleColor: "#FFF9F0",
    },
  },
];

export const TITLE_ITEMS: TitleItem[] = [
  {
    id: DEFAULT_TITLE_ID,
    kind: "title",
    name: "Campus Helper",
    previewLabel: "Helper",
    description: "Friendly default title for active contributors.",
    tier: "starter",
    price: 0,
    purchasable: false,
    accentColor: UTA.royalBlue,
    textColor: "#FFFFFF",
    backgroundColor: UTA.royalBlue,
    art: {
      icon: "hand-heart",
      gradientColors: ["#E9F3FF", "#88C4FF"],
      iconColor: UTA.royalBlue,
      rimColor: "#8FB9F3",
      sparkleColor: "#FFFFFF",
    },
  },
  {
    id: "mav-scout",
    kind: "title",
    name: "Mav Scout",
    previewLabel: "Scout",
    description: "Unlocked by keeping a short contribution streak alive.",
    tier: "achievement",
    price: 0,
    purchasable: false,
    accentColor: UTA.blazeOrange,
    textColor: "#FFFFFF",
    backgroundColor: UTA.blazeOrange,
    art: {
      icon: "compass-rose",
      gradientColors: ["#FFF0E2", "#FFB873"],
      iconColor: "#A14B00",
      rimColor: UTA.blazeOrange,
      sparkleColor: "#FFF5EB",
    },
  },
  {
    id: "crowd-whisperer",
    kind: "title",
    name: "Crowd Whisperer",
    previewLabel: "Crowd",
    description: "A premium title for users who love reading campus flow.",
    tier: "premium",
    price: 280,
    purchasable: true,
    accentColor: "#8E44AD",
    textColor: "#FFFFFF",
    backgroundColor: "#8E44AD",
    art: {
      icon: "radar",
      gradientColors: ["#F3E7FF", "#AE73E6"],
      iconColor: "#5E2B80",
      rimColor: "#8E44AD",
      sparkleColor: "#F6ECFF",
    },
  },
  {
    id: "route-runner",
    kind: "title",
    name: "Route Runner",
    previewLabel: "Route",
    description: "A clean title for users tracking daily movement and timing.",
    tier: "basic",
    price: 170,
    purchasable: true,
    accentColor: "#1E90FF",
    textColor: "#FFFFFF",
    backgroundColor: "#1E90FF",
    art: {
      icon: "routes-clock",
      gradientColors: ["#E4F2FF", "#7DBBFF"],
      iconColor: "#125EAA",
      rimColor: "#1E90FF",
      sparkleColor: "#F2F9FF",
    },
  },
  {
    id: "trend-setter",
    kind: "title",
    name: "Trend Setter",
    previewLabel: "Trend",
    description: "Signals that your reports help define what campus feels like.",
    tier: "premium",
    price: 320,
    purchasable: true,
    accentColor: "#0F766E",
    textColor: "#FFFFFF",
    backgroundColor: "#0F766E",
    art: {
      icon: "chart-timeline-variant",
      gradientColors: ["#DCFDF7", "#4BC2B3"],
      iconColor: "#0F766E",
      rimColor: "#12A594",
      sparkleColor: "#F3FFFC",
    },
  },
];

export const FRAME_ITEMS: FrameItem[] = [
  {
    id: DEFAULT_FRAME_ID,
    kind: "frame",
    name: "Classic Blue",
    previewLabel: "Blue",
    description: "Default UTA-style profile frame.",
    tier: "starter",
    price: 0,
    purchasable: false,
    borderColors: [UTA.royalBlue, "#9DC8E8"],
    glowColor: "rgba(0, 100, 177, 0.18)",
    plateColor: "#E8F1FA",
    art: {
      icon: "shield-account",
      gradientColors: ["#E5F1FF", "#84B7EA"],
      iconColor: UTA.royalBlue,
      rimColor: "#6CA3DD",
      sparkleColor: "#F7FBFF",
    },
  },
  {
    id: "blaze-outline",
    kind: "frame",
    name: "Blaze Outline",
    previewLabel: "Blaze",
    description: "Warm UTA orange edges with a bold profile presence.",
    tier: "basic",
    price: 210,
    purchasable: true,
    borderColors: [UTA.blazeOrange, "#FFD2A8"],
    glowColor: "rgba(245, 128, 37, 0.18)",
    plateColor: "#FFF1E3",
    art: {
      icon: "fire-circle",
      gradientColors: ["#FFF0E3", "#FFA75B"],
      iconColor: "#A84B00",
      rimColor: UTA.blazeOrange,
      sparkleColor: "#FFF7F0",
    },
  },
  {
    id: "midnight-glow",
    kind: "frame",
    name: "Midnight Glow",
    previewLabel: "Night",
    description: "Dark prestige frame with soft violet highlights.",
    tier: "premium",
    price: 360,
    purchasable: true,
    borderColors: ["#2C1A47", "#8B80F9"],
    glowColor: "rgba(139, 128, 249, 0.22)",
    plateColor: "#EEE9FF",
    art: {
      icon: "moon-waning-crescent",
      gradientColors: ["#1C1736", "#725DDA"],
      iconColor: "#EFE9FF",
      rimColor: "#8B80F9",
      sparkleColor: "#D8D0FF",
    },
  },
  {
    id: "crown-glow",
    kind: "frame",
    name: "Crown Glow",
    previewLabel: "Crown",
    description: "Achievement frame for users who keep a longer streak alive.",
    tier: "achievement",
    price: 0,
    purchasable: false,
    borderColors: [UTA.gold, "#FFF3B0"],
    glowColor: "rgba(245, 166, 35, 0.26)",
    plateColor: "#FFF6DB",
    art: {
      icon: "shield-crown",
      gradientColors: ["#FFF7D9", "#FFC15A"],
      iconColor: "#955900",
      rimColor: UTA.gold,
      sparkleColor: "#FFF7E6",
    },
  },
];

export const ACHIEVEMENTS: AchievementDefinition[] = [
  {
    id: "first-check-in",
    name: "First Check-In",
    previewLabel: "Start",
    description: "Submit your first valid campus report.",
    requirementLabel: "1 valid report",
    type: "submissions",
    target: 1,
    art: {
      icon: "map-marker-check",
      gradientColors: ["#EAF7FF", "#9FD6FF"],
      iconColor: UTA.royalBlue,
      rimColor: "#7BAFE6",
      sparkleColor: "#FFFFFF",
    },
  },
  {
    id: "top-reporter-achievement",
    name: "Top Reporter",
    previewLabel: "10x",
    description: "Submit 10 valid campus reports.",
    requirementLabel: "10 valid reports",
    type: "submissions",
    target: 10,
    art: {
      icon: "trophy-award",
      gradientColors: ["#FFF7D6", "#FFD18A"],
      iconColor: "#8A5A00",
      rimColor: "#F4B13D",
      sparkleColor: "#FFF5C0",
    },
    reward: {
      kind: "badge",
      itemId: "top-reporter",
    },
  },
  {
    id: "consistency-club",
    name: "Consistency Club",
    previewLabel: "3D",
    description: "Reach a 3-day contribution streak.",
    requirementLabel: "3-day streak",
    type: "streak",
    target: 3,
    art: {
      icon: "calendar-check",
      gradientColors: ["#FFF0E4", "#FFBC85"],
      iconColor: "#A14B00",
      rimColor: UTA.blazeOrange,
      sparkleColor: "#FFF8EF",
    },
    reward: {
      kind: "title",
      itemId: "mav-scout",
    },
  },
  {
    id: "crown-streak",
    name: "Crown Streak",
    previewLabel: "7D",
    description: "Hold a 7-day contribution streak.",
    requirementLabel: "7-day streak",
    type: "streak",
    target: 7,
    art: {
      icon: "crown-outline",
      gradientColors: ["#FFF6DB", "#F7C65F"],
      iconColor: "#8F5D00",
      rimColor: UTA.gold,
      sparkleColor: "#FFF9EA",
    },
    reward: {
      kind: "frame",
      itemId: "crown-glow",
    },
  },
  {
    id: "semester-radar",
    name: "Semester Radar",
    previewLabel: "25x",
    description: "Submit 25 valid campus reports.",
    requirementLabel: "25 valid reports",
    type: "submissions",
    target: 25,
    art: {
      icon: "radar",
      gradientColors: ["#EAFDFB", "#6FD8C6"],
      iconColor: "#0F766E",
      rimColor: "#18AA99",
      sparkleColor: "#F5FFFD",
    },
  },
];

export function getBadgeById(id: string | null | undefined) {
  if (!id) return BADGE_ITEMS[0];
  return BADGE_ITEMS.find((item) => item.id === id) ?? BADGE_ITEMS[0];
}

export function getTitleById(id: string | null | undefined) {
  if (!id) return TITLE_ITEMS[0];
  return TITLE_ITEMS.find((item) => item.id === id) ?? TITLE_ITEMS[0];
}

export function getFrameById(id: string | null | undefined) {
  if (!id) return FRAME_ITEMS[0];
  return FRAME_ITEMS.find((item) => item.id === id) ?? FRAME_ITEMS[0];
}

export function getAchievementById(id: string | null | undefined) {
  if (!id) return null;
  return ACHIEVEMENTS.find((item) => item.id === id) ?? null;
}

export function getIdentityItem(kind: IdentityKind, id: string | null | undefined): IdentityItem | null {
  if (!id) return null;

  if (kind === "badge") {
    return BADGE_ITEMS.find((item) => item.id === id) ?? null;
  }

  if (kind === "title") {
    return TITLE_ITEMS.find((item) => item.id === id) ?? null;
  }

  return FRAME_ITEMS.find((item) => item.id === id) ?? null;
}

export function getIdentityTierLabel(tier: IdentityTier) {
  switch (tier) {
    case "starter":
      return "Starter";
    case "basic":
      return "Basic";
    case "premium":
      return "Premium";
    case "achievement":
      return "Achievement";
    default:
      return "Unlock";
  }
}

export function evaluateUnlockedAchievements({
  totalSurveySubmissions,
  currentContributionStreak,
}: {
  totalSurveySubmissions: number;
  currentContributionStreak: number;
}) {
  return ACHIEVEMENTS.filter((achievement) => {
    if (achievement.type === "submissions") {
      return totalSurveySubmissions >= achievement.target;
    }

    return currentContributionStreak >= achievement.target;
  }).map((achievement) => achievement.id);
}
