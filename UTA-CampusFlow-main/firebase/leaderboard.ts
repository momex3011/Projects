import { CAMPUS_SURVEY_REWARD_POINTS } from "@/constants/campus-survey";
import {
  getBadgeById,
  getFrameById,
  getTitleById,
} from "@/constants/gamification";
import {
  getLeaderboardWindowMeta,
  LEADERBOARD_DISPLAY_LIMIT,
  type LeaderboardMetric,
  type LeaderboardWindow,
} from "@/constants/leaderboard";
import { db } from "@/firebase/firebase";
import { resolveLeaderboardLabel } from "@/firebase/user-profile";
import {
  collection,
  documentId,
  getDocs,
  orderBy,
  query,
  where,
} from "firebase/firestore";

type AuthViewer = {
  uid?: string | null;
  email?: string | null;
};

type LeaderboardAggregate = {
  userId: string;
  pointsEarned: number;
  submissionCount: number;
  lastSubmittedAt: Date | null;
};

type LeaderboardDecoration = {
  label: string;
  badgeId: string;
  badgeName: string;
  badgeShortLabel: string;
  badgeBackgroundColor: string;
  badgeTextColor: string;
  badgeAccentColor: string;
  titleId: string;
  titleName: string;
  titleBackgroundColor: string;
  titleTextColor: string;
  titleAccentColor: string;
  frameId: string;
  frameBorderColors: [string, string];
  frameGlowColor: string;
  framePlateColor: string;
  currentContributionStreak: number;
  achievementCount: number;
};

export type LeaderboardEntry = {
  userId: string;
  label: string;
  pointsEarned: number;
  submissionCount: number;
  rank: number;
  score: number;
  latestSubmissionAt: Date | null;
  isCurrentUser: boolean;
  badgeId: string;
  badgeName: string;
  badgeShortLabel: string;
  badgeBackgroundColor: string;
  badgeTextColor: string;
  badgeAccentColor: string;
  titleId: string;
  titleName: string;
  titleBackgroundColor: string;
  titleTextColor: string;
  titleAccentColor: string;
  frameId: string;
  frameBorderColors: [string, string];
  frameGlowColor: string;
  framePlateColor: string;
  currentContributionStreak: number;
  achievementCount: number;
};

export type LeaderboardDataset = {
  window: LeaderboardWindow;
  startsAt: Date;
  generatedAt: Date;
  contributorCount: number;
  pointsEntries: LeaderboardEntry[];
  submissionEntries: LeaderboardEntry[];
  visiblePointsEntries: LeaderboardEntry[];
  visibleSubmissionEntries: LeaderboardEntry[];
  currentUserPointsEntry: LeaderboardEntry | null;
  currentUserSubmissionEntry: LeaderboardEntry | null;
};

export async function fetchLeaderboardDataset(
  window: LeaderboardWindow,
  viewer?: AuthViewer
): Promise<LeaderboardDataset> {
  const startsAt = getWindowStartDate(window);
  const reportQuery = query(
    collection(db, "campusReports"),
    where("createdAt", ">=", startsAt),
    orderBy("createdAt", "desc")
  );

  const snapshot = await getDocs(reportQuery);
  const aggregates = new Map<string, LeaderboardAggregate>();

  snapshot.forEach((docSnap) => {
    const data = docSnap.data();
    const userId = typeof data.userId === "string" ? data.userId : null;
    if (!userId) return;

    const existing = aggregates.get(userId) ?? {
      userId,
      pointsEarned: 0,
      submissionCount: 0,
      lastSubmittedAt: null,
    };

    existing.submissionCount += 1;
    existing.pointsEarned +=
      typeof data.pointsAwarded === "number" ? data.pointsAwarded : CAMPUS_SURVEY_REWARD_POINTS;

    const submittedAt =
      typeof data.createdAt?.toDate === "function" ? data.createdAt.toDate() : null;
    if (!existing.lastSubmittedAt || (submittedAt && submittedAt > existing.lastSubmittedAt)) {
      existing.lastSubmittedAt = submittedAt;
    }

    aggregates.set(userId, existing);
  });

  const aggregateList = Array.from(aggregates.values());
  const pointsRanked = rankAggregates(aggregateList, "points", viewer?.uid ?? null);
  const submissionRanked = rankAggregates(aggregateList, "submissions", viewer?.uid ?? null);

  const idsToFetch = Array.from(
    new Set([
      ...pointsRanked.slice(0, LEADERBOARD_DISPLAY_LIMIT).map((entry) => entry.userId),
      ...submissionRanked.slice(0, LEADERBOARD_DISPLAY_LIMIT).map((entry) => entry.userId),
      viewer?.uid ?? "",
    ].filter(Boolean))
  );

  const decorationMap = await fetchLeaderboardDecorations(idsToFetch);

  const decorate = (entries: RankedAggregate[]): LeaderboardEntry[] =>
    entries.map((entry) => {
      const decoration = decorationMap.get(entry.userId) ?? buildFallbackDecoration(entry.userId);
      return {
        userId: entry.userId,
        pointsEarned: entry.pointsEarned,
        submissionCount: entry.submissionCount,
        rank: entry.rank,
        score: entry.score,
        latestSubmissionAt: entry.lastSubmittedAt,
        isCurrentUser: entry.isCurrentUser,
        ...decoration,
        label:
          entry.isCurrentUser && viewer?.uid === entry.userId ? "You" : decoration.label,
      };
    });

  const pointsEntries = decorate(pointsRanked);
  const submissionEntries = decorate(submissionRanked);

  return {
    window,
    startsAt,
    generatedAt: new Date(),
    contributorCount: aggregateList.length,
    pointsEntries,
    submissionEntries,
    visiblePointsEntries: pointsEntries.slice(0, LEADERBOARD_DISPLAY_LIMIT),
    visibleSubmissionEntries: submissionEntries.slice(0, LEADERBOARD_DISPLAY_LIMIT),
    currentUserPointsEntry: pointsEntries.find((entry) => entry.userId === viewer?.uid) ?? null,
    currentUserSubmissionEntry:
      submissionEntries.find((entry) => entry.userId === viewer?.uid) ?? null,
  };
}

type RankedAggregate = LeaderboardAggregate & {
  rank: number;
  score: number;
  isCurrentUser: boolean;
};

function rankAggregates(
  aggregates: LeaderboardAggregate[],
  metric: LeaderboardMetric,
  currentUserId: string | null
) {
  const sorted = [...aggregates].sort((left, right) => {
    const scoreDelta = getMetricScore(right, metric) - getMetricScore(left, metric);
    if (scoreDelta !== 0) return scoreDelta;

    const secondaryDelta = right.pointsEarned - left.pointsEarned;
    if (metric === "submissions" && secondaryDelta !== 0) return secondaryDelta;

    const latestRight = right.lastSubmittedAt?.getTime() ?? 0;
    const latestLeft = left.lastSubmittedAt?.getTime() ?? 0;
    return latestRight - latestLeft;
  });

  let previousScore: number | null = null;
  let previousRank = 0;

  return sorted.map((entry, index) => {
    const score = getMetricScore(entry, metric);
    const rank = previousScore === score ? previousRank : index + 1;
    previousScore = score;
    previousRank = rank;

    return {
      ...entry,
      rank,
      score,
      isCurrentUser: currentUserId === entry.userId,
    };
  });
}

async function fetchLeaderboardDecorations(userIds: string[]) {
  const result = new Map<string, LeaderboardDecoration>();
  if (userIds.length === 0) return result;

  const batches = chunk(userIds, 10);

  for (const batch of batches) {
    const userQuery = query(collection(db, "users"), where(documentId(), "in", batch));
    const snapshot = await getDocs(userQuery);

    snapshot.forEach((docSnap) => {
      const data = docSnap.data();
      const badge = getBadgeById(typeof data.selectedBadge === "string" ? data.selectedBadge : null);
      const title = getTitleById(typeof data.selectedTitle === "string" ? data.selectedTitle : null);
      const frame = getFrameById(typeof data.selectedFrame === "string" ? data.selectedFrame : null);

      result.set(docSnap.id, {
        label: resolveLeaderboardLabel(data, docSnap.id),
        badgeId: badge.id,
        badgeName: badge.name,
        badgeShortLabel: badge.shortLabel,
        badgeBackgroundColor: badge.backgroundColor,
        badgeTextColor: badge.textColor,
        badgeAccentColor: badge.accentColor,
        titleId: title.id,
        titleName: title.name,
        titleBackgroundColor: title.backgroundColor,
        titleTextColor: title.textColor,
        titleAccentColor: title.accentColor,
        frameId: frame.id,
        frameBorderColors: frame.borderColors,
        frameGlowColor: frame.glowColor,
        framePlateColor: frame.plateColor,
        currentContributionStreak:
          typeof data.currentContributionStreak === "number" ? data.currentContributionStreak : 0,
        achievementCount: Array.isArray(data.unlockedAchievements)
          ? data.unlockedAchievements.length
          : 0,
      });
    });
  }

  return result;
}

function buildFallbackDecoration(userId: string): LeaderboardDecoration {
  const badge = getBadgeById(null);
  const title = getTitleById(null);
  const frame = getFrameById(null);

  return {
    label: fallbackLabel(userId),
    badgeId: badge.id,
    badgeName: badge.name,
    badgeShortLabel: badge.shortLabel,
    badgeBackgroundColor: badge.backgroundColor,
    badgeTextColor: badge.textColor,
    badgeAccentColor: badge.accentColor,
    titleId: title.id,
    titleName: title.name,
    titleBackgroundColor: title.backgroundColor,
    titleTextColor: title.textColor,
    titleAccentColor: title.accentColor,
    frameId: frame.id,
    frameBorderColors: frame.borderColors,
    frameGlowColor: frame.glowColor,
    framePlateColor: frame.plateColor,
    currentContributionStreak: 0,
    achievementCount: 0,
  };
}

function getMetricScore(entry: LeaderboardAggregate, metric: LeaderboardMetric) {
  return metric === "points" ? entry.pointsEarned : entry.submissionCount;
}

function getWindowStartDate(window: LeaderboardWindow) {
  const now = new Date();
  const startsAt = new Date(now);
  startsAt.setDate(now.getDate() - getLeaderboardWindowMeta(window).days);
  return startsAt;
}

function fallbackLabel(userId: string) {
  return `Mav ${userId.slice(-4).toUpperCase()}`;
}

function chunk<T>(items: T[], size: number) {
  const result: T[][] = [];
  for (let index = 0; index < items.length; index += size) {
    result.push(items.slice(index, index + size));
  }
  return result;
}
