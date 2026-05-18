import type { User } from "firebase/auth";
import { doc, getDoc, runTransaction, setDoc } from "firebase/firestore";
import { DEFAULT_THEME_ID } from "../constants/background-themes";
import {
  ACHIEVEMENTS,
  DEFAULT_BADGE_ID,
  DEFAULT_FRAME_ID,
  DEFAULT_TITLE_ID,
  evaluateUnlockedAchievements,
  FRAME_ITEMS,
  BADGE_ITEMS,
  TITLE_ITEMS,
  type IdentityKind,
} from "../constants/gamification";
import { db } from "./firebase";

export type UserProfileShape = {
  points?: number;
  selectedTheme?: string;
  unlockedThemes?: string[];
  leaderboardName?: string;
  emailHandle?: string;
  selectedBadge?: string;
  unlockedBadges?: string[];
  selectedTitle?: string;
  unlockedTitles?: string[];
  selectedFrame?: string;
  unlockedFrames?: string[];
  totalSurveySubmissions?: number;
  currentContributionStreak?: number;
  longestContributionStreak?: number;
  lastContributionDateKey?: string | null;
  unlockedAchievements?: string[];
  [key: string]: unknown;
};

const BADGE_IDS = new Set(BADGE_ITEMS.map((item) => item.id));
const TITLE_IDS = new Set(TITLE_ITEMS.map((item) => item.id));
const FRAME_IDS = new Set(FRAME_ITEMS.map((item) => item.id));

type IdentitySelectionConfig = {
  defaultId: string;
  selectedField: "selectedBadge" | "selectedTitle" | "selectedFrame";
  unlockedField: "unlockedBadges" | "unlockedTitles" | "unlockedFrames";
  validIds: Set<string>;
};

const IDENTITY_CONFIG: Record<IdentityKind, IdentitySelectionConfig> = {
  badge: {
    defaultId: DEFAULT_BADGE_ID,
    selectedField: "selectedBadge",
    unlockedField: "unlockedBadges",
    validIds: BADGE_IDS,
  },
  title: {
    defaultId: DEFAULT_TITLE_ID,
    selectedField: "selectedTitle",
    unlockedField: "unlockedTitles",
    validIds: TITLE_IDS,
  },
  frame: {
    defaultId: DEFAULT_FRAME_ID,
    selectedField: "selectedFrame",
    unlockedField: "unlockedFrames",
    validIds: FRAME_IDS,
  },
};

export function buildDefaultUserProfile(overrides: UserProfileShape = {}) {
  return {
    points: 0,
    selectedTheme: DEFAULT_THEME_ID,
    unlockedThemes: [DEFAULT_THEME_ID],
    selectedBadge: DEFAULT_BADGE_ID,
    unlockedBadges: [DEFAULT_BADGE_ID],
    selectedTitle: DEFAULT_TITLE_ID,
    unlockedTitles: [DEFAULT_TITLE_ID],
    selectedFrame: DEFAULT_FRAME_ID,
    unlockedFrames: [DEFAULT_FRAME_ID],
    totalSurveySubmissions: 0,
    currentContributionStreak: 0,
    longestContributionStreak: 0,
    lastContributionDateKey: null,
    unlockedAchievements: [],
    ...overrides,
  };
}

export function buildLeaderboardName(email?: string | null, userId?: string) {
  const handle = email?.split("@")[0]?.trim();
  if (handle) {
    const cleaned = handle.replace(/[^a-zA-Z0-9]+/g, " ").trim();
    const primary = cleaned.split(/\s+/)[0];
    if (primary) {
      return primary.charAt(0).toUpperCase() + primary.slice(1, 12);
    }
  }

  return `Mav ${userId?.slice(-4).toUpperCase() ?? "User"}`;
}

export function resolveLeaderboardLabel(
  profile: Record<string, unknown> | undefined,
  userId: string
) {
  if (typeof profile?.leaderboardName === "string" && profile.leaderboardName.trim()) {
    return profile.leaderboardName.trim();
  }

  if (typeof profile?.emailHandle === "string" && profile.emailHandle.trim()) {
    return buildLeaderboardName(`${profile.emailHandle}@mavs.uta.edu`, userId);
  }

  return buildLeaderboardName(undefined, userId);
}

export function normalizeUnlockedThemes(raw: unknown): string[] {
  return normalizeUnlockedCollection(raw, DEFAULT_THEME_ID);
}

export function normalizeUnlockedBadges(raw: unknown): string[] {
  return normalizeIdentityCollection(raw, "badge");
}

export function normalizeUnlockedTitles(raw: unknown): string[] {
  return normalizeIdentityCollection(raw, "title");
}

export function normalizeUnlockedFrames(raw: unknown): string[] {
  return normalizeIdentityCollection(raw, "frame");
}

export function normalizeUnlockedAchievements(raw: unknown): string[] {
  const values = Array.isArray(raw)
    ? raw.filter((value): value is string => typeof value === "string")
    : [];
  return Array.from(new Set(values));
}

export async function ensureUserProfile(userId: string) {
  const userRef = doc(db, "users", userId);
  const snapshot = await getDoc(userRef);

  if (!snapshot.exists()) {
    const data = buildDefaultUserProfile();
    await setDoc(userRef, data, { merge: true });
    return { ref: userRef, data };
  }

  const existing = snapshot.data() as UserProfileShape;
  const normalized = normalizeUserProfile(existing);
  const updates: UserProfileShape = {};

  if (typeof existing.points !== "number") updates.points = 0;
  if (!arraysMatch(existing.unlockedThemes, normalized.unlockedThemes)) {
    updates.unlockedThemes = normalized.unlockedThemes;
  }
  if (!arraysMatch(existing.unlockedBadges, normalized.unlockedBadges)) {
    updates.unlockedBadges = normalized.unlockedBadges;
  }
  if (!arraysMatch(existing.unlockedTitles, normalized.unlockedTitles)) {
    updates.unlockedTitles = normalized.unlockedTitles;
  }
  if (!arraysMatch(existing.unlockedFrames, normalized.unlockedFrames)) {
    updates.unlockedFrames = normalized.unlockedFrames;
  }
  if (!arraysMatch(existing.unlockedAchievements, normalized.unlockedAchievements)) {
    updates.unlockedAchievements = normalized.unlockedAchievements;
  }
  if (existing.selectedTheme !== normalized.selectedTheme) {
    updates.selectedTheme = normalized.selectedTheme;
  }
  if (existing.selectedBadge !== normalized.selectedBadge) {
    updates.selectedBadge = normalized.selectedBadge;
  }
  if (existing.selectedTitle !== normalized.selectedTitle) {
    updates.selectedTitle = normalized.selectedTitle;
  }
  if (existing.selectedFrame !== normalized.selectedFrame) {
    updates.selectedFrame = normalized.selectedFrame;
  }
  if (typeof existing.totalSurveySubmissions !== "number") updates.totalSurveySubmissions = 0;
  if (typeof existing.currentContributionStreak !== "number") {
    updates.currentContributionStreak = 0;
  }
  if (typeof existing.longestContributionStreak !== "number") {
    updates.longestContributionStreak = 0;
  }
  if (
    existing.lastContributionDateKey !== null &&
    typeof existing.lastContributionDateKey !== "string"
  ) {
    updates.lastContributionDateKey = null;
  }

  if (Object.keys(updates).length > 0) {
    await setDoc(userRef, updates, { merge: true });
  }

  return {
    ref: userRef,
    data: {
      ...buildDefaultUserProfile(),
      ...existing,
      ...updates,
      ...normalized,
    },
  };
}

export async function syncUserProfileIdentity(user: Pick<User, "uid" | "email" | "isAnonymous">) {
  if (user.isAnonymous) return;

  const emailHandle = user.email?.split("@")[0]?.trim() ?? null;

  await setDoc(
    doc(db, "users", user.uid),
    {
      emailHandle,
      leaderboardName: buildLeaderboardName(user.email, user.uid),
    },
    { merge: true }
  );
}

export async function applySelectedTheme(userId: string, themeId: string) {
  const { ref, data } = await ensureUserProfile(userId);
  const unlockedThemes = normalizeUnlockedThemes(data.unlockedThemes);

  if (!unlockedThemes.includes(themeId)) {
    throw new Error("Unlock this theme before applying it.");
  }

  await setDoc(
    ref,
    {
      selectedTheme: themeId,
      unlockedThemes,
    },
    { merge: true }
  );
}

export async function unlockThemeForUser(userId: string, themeId: string, price: number) {
  const userRef = doc(db, "users", userId);

  await runTransaction(db, async (transaction) => {
    const snapshot = await transaction.get(userRef);
    const existing = normalizeUserProfile(
      (snapshot.exists() ? snapshot.data() : buildDefaultUserProfile()) as UserProfileShape
    );
    const points = typeof existing.points === "number" ? existing.points : 0;

    if (existing.unlockedThemes.includes(themeId)) {
      transaction.set(
        userRef,
        {
          selectedTheme: themeId,
          unlockedThemes: existing.unlockedThemes,
        },
        { merge: true }
      );
      return;
    }

    if (points < price) {
      throw new Error(`You need ${price - points} more MavPoints to unlock this theme.`);
    }

    transaction.set(
      userRef,
      {
        points: points - price,
        selectedTheme: themeId,
        unlockedThemes: [...existing.unlockedThemes, themeId],
      },
      { merge: true }
    );
  });
}

export async function applyIdentitySelection(
  userId: string,
  kind: IdentityKind,
  itemId: string
) {
  const config = IDENTITY_CONFIG[kind];
  const { ref, data } = await ensureUserProfile(userId);
  const unlocked = normalizeIdentityCollection(data[config.unlockedField], kind);

  if (!unlocked.includes(itemId)) {
    throw new Error(`Unlock this ${kind} before applying it.`);
  }

  await setDoc(
    ref,
    {
      [config.selectedField]: itemId,
      [config.unlockedField]: unlocked,
    },
    { merge: true }
  );
}

export async function unlockIdentityItemForUser(
  userId: string,
  kind: IdentityKind,
  itemId: string,
  price: number
) {
  const config = IDENTITY_CONFIG[kind];
  const userRef = doc(db, "users", userId);

  await runTransaction(db, async (transaction) => {
    const snapshot = await transaction.get(userRef);
    const existing = normalizeUserProfile(
      (snapshot.exists() ? snapshot.data() : buildDefaultUserProfile()) as UserProfileShape
    );
    const unlocked = normalizeIdentityCollection(existing[config.unlockedField], kind);
    const points = typeof existing.points === "number" ? existing.points : 0;

    if (unlocked.includes(itemId)) {
      transaction.set(
        userRef,
        {
          [config.selectedField]: itemId,
          [config.unlockedField]: unlocked,
        },
        { merge: true }
      );
      return;
    }

    if (points < price) {
      throw new Error(`You need ${price - points} more MavPoints to unlock this ${kind}.`);
    }

    transaction.set(
      userRef,
      {
        points: points - price,
        [config.selectedField]: itemId,
        [config.unlockedField]: [...unlocked, itemId],
      },
      { merge: true }
    );
  });
}

export function buildContributionProgressFields(
  existing: UserProfileShape,
  now: Date
): UserProfileShape {
  const currentKey = buildDateKey(now);
  const previousKey =
    typeof existing.lastContributionDateKey === "string" ? existing.lastContributionDateKey : null;
  const previousSubmissionCount =
    typeof existing.totalSurveySubmissions === "number" ? existing.totalSurveySubmissions : 0;
  const previousStreak =
    typeof existing.currentContributionStreak === "number" ? existing.currentContributionStreak : 0;
  const previousLongest =
    typeof existing.longestContributionStreak === "number" ? existing.longestContributionStreak : 0;

  let currentContributionStreak = previousStreak;
  if (previousKey === currentKey) {
    currentContributionStreak = Math.max(previousStreak, 1);
  } else if (previousKey && daysBetweenKeys(previousKey, currentKey) === 1) {
    currentContributionStreak = Math.max(previousStreak, 0) + 1;
  } else {
    currentContributionStreak = 1;
  }

  const totalSurveySubmissions = previousSubmissionCount + 1;
  const longestContributionStreak = Math.max(previousLongest, currentContributionStreak);
  const previouslyUnlockedAchievements = normalizeUnlockedAchievements(existing.unlockedAchievements);
  const newlyUnlockedAchievements = evaluateUnlockedAchievements({
    totalSurveySubmissions,
    currentContributionStreak,
  });
  const unlockedAchievements = Array.from(
    new Set([...previouslyUnlockedAchievements, ...newlyUnlockedAchievements])
  );

  const unlockedBadges = normalizeUnlockedBadges(existing.unlockedBadges);
  const unlockedTitles = normalizeUnlockedTitles(existing.unlockedTitles);
  const unlockedFrames = normalizeUnlockedFrames(existing.unlockedFrames);

  for (const achievementId of unlockedAchievements) {
    const achievement = evaluateRewardLookup(achievementId);
    if (!achievement) continue;

    if (achievement.kind === "badge" && !unlockedBadges.includes(achievement.itemId)) {
      unlockedBadges.push(achievement.itemId);
    }
    if (achievement.kind === "title" && !unlockedTitles.includes(achievement.itemId)) {
      unlockedTitles.push(achievement.itemId);
    }
    if (achievement.kind === "frame" && !unlockedFrames.includes(achievement.itemId)) {
      unlockedFrames.push(achievement.itemId);
    }
  }

  return {
    totalSurveySubmissions,
    currentContributionStreak,
    longestContributionStreak,
    lastContributionDateKey: currentKey,
    unlockedAchievements,
    unlockedBadges,
    unlockedTitles,
    unlockedFrames,
  };
}

function normalizeUserProfile(existing: UserProfileShape) {
  const unlockedThemes = normalizeUnlockedThemes(existing.unlockedThemes);
  const unlockedBadges = normalizeUnlockedBadges(existing.unlockedBadges);
  const unlockedTitles = normalizeUnlockedTitles(existing.unlockedTitles);
  const unlockedFrames = normalizeUnlockedFrames(existing.unlockedFrames);
  const unlockedAchievements = normalizeUnlockedAchievements(existing.unlockedAchievements);

  return {
    ...existing,
    unlockedThemes,
    unlockedBadges,
    unlockedTitles,
    unlockedFrames,
    unlockedAchievements,
    selectedTheme:
      typeof existing.selectedTheme === "string" && unlockedThemes.includes(existing.selectedTheme)
        ? existing.selectedTheme
        : DEFAULT_THEME_ID,
    selectedBadge:
      typeof existing.selectedBadge === "string" && unlockedBadges.includes(existing.selectedBadge)
        ? existing.selectedBadge
        : DEFAULT_BADGE_ID,
    selectedTitle:
      typeof existing.selectedTitle === "string" && unlockedTitles.includes(existing.selectedTitle)
        ? existing.selectedTitle
        : DEFAULT_TITLE_ID,
    selectedFrame:
      typeof existing.selectedFrame === "string" && unlockedFrames.includes(existing.selectedFrame)
        ? existing.selectedFrame
        : DEFAULT_FRAME_ID,
  };
}

function normalizeIdentityCollection(raw: unknown, kind: IdentityKind) {
  const config = IDENTITY_CONFIG[kind];
  const values = Array.isArray(raw)
    ? raw.filter((value): value is string => typeof value === "string" && config.validIds.has(value))
    : [];
  return Array.from(new Set([config.defaultId, ...values]));
}

function normalizeUnlockedCollection(raw: unknown, defaultId: string) {
  const values = Array.isArray(raw)
    ? raw.filter((value): value is string => typeof value === "string")
    : [];
  return Array.from(new Set([defaultId, ...values]));
}

function arraysMatch(left: unknown, right: string[]) {
  const normalizedLeft = Array.isArray(left)
    ? left.filter((value): value is string => typeof value === "string")
    : [];
  return (
    normalizedLeft.length === right.length &&
    normalizedLeft.every((value, index) => value === right[index])
  );
}

function buildDateKey(date: Date) {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function daysBetweenKeys(startKey: string, endKey: string) {
  const start = parseDateKey(startKey);
  const end = parseDateKey(endKey);
  return Math.round((end.getTime() - start.getTime()) / 86400000);
}

function parseDateKey(value: string) {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, (month || 1) - 1, day || 1);
}

function evaluateRewardLookup(achievementId: string) {
  return ACHIEVEMENTS.find((achievement) => achievement.id === achievementId)?.reward ?? null;
}
