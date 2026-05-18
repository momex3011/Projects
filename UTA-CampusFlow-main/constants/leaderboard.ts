export type LeaderboardMetric = "points" | "submissions";
export type LeaderboardWindow = "weekly" | "monthly" | "annual";

export const LEADERBOARD_DISPLAY_LIMIT = 15;

export const LEADERBOARD_METRICS: {
  id: LeaderboardMetric;
  label: string;
  shortLabel: string;
  description: string;
}[] = [
  {
    id: "points",
    label: "Points",
    shortLabel: "MavPoints",
    description: "Most points earned from valid survey reports.",
  },
  {
    id: "submissions",
    label: "Submissions",
    shortLabel: "Reports",
    description: "Most valid campus reports submitted.",
  },
];

export const LEADERBOARD_WINDOWS: {
  id: LeaderboardWindow;
  label: string;
  days: number;
  description: string;
}[] = [
  {
    id: "weekly",
    label: "Weekly",
    days: 7,
    description: "Last 7 days",
  },
  {
    id: "monthly",
    label: "Monthly",
    days: 30,
    description: "Last 30 days",
  },
  {
    id: "annual",
    label: "Annual",
    days: 365,
    description: "Last 365 days",
  },
];

export function getLeaderboardWindowMeta(window: LeaderboardWindow) {
  return LEADERBOARD_WINDOWS.find((item) => item.id === window) ?? LEADERBOARD_WINDOWS[0];
}

export function formatLeaderboardRank(rank: number) {
  const mod100 = rank % 100;
  if (mod100 >= 11 && mod100 <= 13) return `${rank}th`;

  const mod10 = rank % 10;
  if (mod10 === 1) return `${rank}st`;
  if (mod10 === 2) return `${rank}nd`;
  if (mod10 === 3) return `${rank}rd`;
  return `${rank}th`;
}
