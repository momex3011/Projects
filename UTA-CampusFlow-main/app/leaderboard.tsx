import { AppBackground } from "@/components/app-background";
import { useAppTheme } from "@/components/app-theme-provider";
import { ACHIEVEMENTS } from "@/constants/gamification";
import {
  formatLeaderboardRank,
  LEADERBOARD_METRICS,
  LEADERBOARD_WINDOWS,
  type LeaderboardMetric,
  type LeaderboardWindow,
} from "@/constants/leaderboard";
import {
  fetchLeaderboardDataset,
  type LeaderboardDataset,
  type LeaderboardEntry,
} from "@/firebase/leaderboard";
import { auth } from "@/firebase/firebase";
import { LinearGradient } from "expo-linear-gradient";
import { useRouter } from "expo-router";
import { onAuthStateChanged } from "firebase/auth";
import React, { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { UTA } from "../constants/theme";

const TOP_RANK_COLORS: Record<number, string> = {
  1: UTA.gold,
  2: "#C9D2DF",
  3: UTA.blazeOrange,
};

export default function LeaderboardScreen() {
  const router = useRouter();
  const { palette } = useAppTheme();
  const [metric, setMetric] = useState<LeaderboardMetric>("points");
  const [window, setWindow] = useState<LeaderboardWindow>("weekly");
  const [user, setUser] = useState(auth.currentUser);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataset, setDataset] = useState<LeaderboardDataset | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (nextUser) => setUser(nextUser));
    return unsubscribe;
  }, []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    fetchLeaderboardDataset(window, {
      uid: user?.uid,
      email: user?.email,
    })
      .then((nextDataset) => {
        if (!active) return;
        setDataset(nextDataset);
      })
      .catch((nextError) => {
        console.error("Failed to load leaderboard:", nextError);
        if (!active) return;
        setError("Unable to load the leaderboard right now.");
      })
      .finally(() => {
        if (!active) return;
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [window, user?.email, user?.uid]);

  const metricMeta = LEADERBOARD_METRICS.find((item) => item.id === metric) ?? LEADERBOARD_METRICS[0];
  const windowMeta = LEADERBOARD_WINDOWS.find((item) => item.id === window) ?? LEADERBOARD_WINDOWS[0];

  const entries =
    metric === "points"
      ? dataset?.visiblePointsEntries ?? []
      : dataset?.visibleSubmissionEntries ?? [];
  const currentUserEntry =
    metric === "points"
      ? dataset?.currentUserPointsEntry ?? null
      : dataset?.currentUserSubmissionEntry ?? null;

  const topEntries = entries.slice(0, 3);
  const podiumEntries = useMemo(
    () => [topEntries[1], topEntries[0], topEntries[2]].filter(Boolean) as LeaderboardEntry[],
    [topEntries]
  );
  const shouldShowPinnedCurrentUser =
    currentUserEntry !== null && !entries.some((entry) => entry.userId === currentUserEntry.userId);
  const unlockedAchievementCount = currentUserEntry?.achievementCount ?? 0;

  return (
    <AppBackground>
      <SafeAreaView style={styles.safeArea}>
        <ScrollView
          contentContainerStyle={styles.container}
          showsVerticalScrollIndicator={false}>
          <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
            <Text style={[styles.backText, { color: palette.accent }]}>Back</Text>
          </TouchableOpacity>

          <View style={[styles.heroCard, { backgroundColor: palette.surface }]}>
            <Text style={[styles.heroEyebrow, { color: palette.accentStrong }]}>Leaderboard</Text>
            <Text style={[styles.title, { color: palette.text }]}>Top campus contributors</Text>
            <Text style={[styles.subtitle, { color: palette.mutedText }]}>
              Prestige comes from real campus help: points, valid reports, streaks, and unlocked identity flair.
            </Text>

            <View style={styles.heroStats}>
              <View style={[styles.heroStatCard, { backgroundColor: palette.surfaceAlt }]}>
                <Text style={[styles.heroStatValue, { color: palette.accent }]}>
                  {dataset?.contributorCount ?? 0}
                </Text>
                <Text style={[styles.heroStatLabel, { color: palette.mutedText }]}>contributors</Text>
              </View>
              <View style={[styles.heroStatCard, { backgroundColor: palette.surfaceAlt }]}>
                <Text style={[styles.heroStatValue, { color: palette.text }]}>
                  {windowMeta.label}
                </Text>
                <Text style={[styles.heroStatLabel, { color: palette.mutedText }]}>
                  {windowMeta.description}
                </Text>
              </View>
            </View>
          </View>

          <View style={[styles.segmentCard, { backgroundColor: palette.surface }]}>
            <Text style={[styles.segmentTitle, { color: palette.text }]}>Leaderboard type</Text>
            <Text style={[styles.segmentSubtitle, { color: palette.mutedText }]}>
              {metricMeta.description}
            </Text>
            <View style={styles.segmentRow}>
              {LEADERBOARD_METRICS.map((item) => {
                const isActive = item.id === metric;
                return (
                  <TouchableOpacity
                    key={item.id}
                    style={[
                      styles.segmentButton,
                      { backgroundColor: isActive ? palette.accent : palette.surfaceAlt },
                    ]}
                    onPress={() => setMetric(item.id)}
                    activeOpacity={0.9}>
                    <Text
                      style={[
                        styles.segmentButtonText,
                        { color: isActive ? palette.accentText : palette.text },
                      ]}>
                      {item.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>

          <View style={[styles.segmentCard, { backgroundColor: palette.surface }]}>
            <Text style={[styles.segmentTitle, { color: palette.text }]}>Time range</Text>
            <Text style={[styles.segmentSubtitle, { color: palette.mutedText }]}>
              Weekly, monthly, and annual leaderboards all use the same simple ranking rules.
            </Text>
            <View style={styles.segmentRow}>
              {LEADERBOARD_WINDOWS.map((item) => {
                const isActive = item.id === window;
                return (
                  <TouchableOpacity
                    key={item.id}
                    style={[
                      styles.segmentButton,
                      {
                        backgroundColor: isActive ? palette.accentStrong : palette.surfaceAlt,
                      },
                    ]}
                    onPress={() => setWindow(item.id)}
                    activeOpacity={0.9}>
                    <Text
                      style={[
                        styles.segmentButtonText,
                        { color: isActive ? "#FFFFFF" : palette.text },
                      ]}>
                      {item.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>

          {loading ? (
            <View style={[styles.stateCard, { backgroundColor: palette.surface }]}>
              <ActivityIndicator color={palette.accent} />
              <Text style={[styles.stateText, { color: palette.mutedText }]}>
                Loading leaderboard...
              </Text>
            </View>
          ) : error ? (
            <View style={[styles.stateCard, { backgroundColor: palette.surface }]}>
              <Text style={[styles.stateTitle, { color: palette.text }]}>Leaderboard unavailable</Text>
              <Text style={[styles.stateText, { color: palette.mutedText }]}>{error}</Text>
            </View>
          ) : entries.length === 0 ? (
            <View style={[styles.stateCard, { backgroundColor: palette.surface }]}>
              <Text style={[styles.stateTitle, { color: palette.text }]}>No reports yet</Text>
              <Text style={[styles.stateText, { color: palette.mutedText }]}>
                Rankings will appear once valid campus reports start coming in.
              </Text>
            </View>
          ) : (
            <>
              <View style={[styles.podiumCard, { backgroundColor: palette.surface }]}>
                <Text style={[styles.sectionTitle, { color: palette.text }]}>
                  Top 3 this {windowMeta.label.toLowerCase()}
                </Text>
                <View style={styles.podiumRow}>
                  {podiumEntries.map((entry) => {
                    const rankColor = TOP_RANK_COLORS[entry.rank] ?? palette.accent;
                    const isChampion = entry.rank === 1;
                    return (
                      <LinearGradient
                        key={entry.userId}
                        colors={entry.frameBorderColors}
                        start={{ x: 0, y: 0 }}
                        end={{ x: 1, y: 1 }}
                        style={[
                          styles.podiumShell,
                          {
                            minHeight: isChampion ? 184 : 160,
                            marginTop: isChampion ? 0 : 20,
                            shadowColor: entry.frameGlowColor,
                          },
                        ]}>
                        <View
                          style={[
                            styles.podiumInner,
                            {
                              backgroundColor: isChampion
                                ? palette.surfaceAlt
                                : palette.inputBackground,
                            },
                          ]}>
                          <View style={[styles.rankPlate, { backgroundColor: rankColor }]}>
                            <Text style={styles.rankPlateText}>{formatLeaderboardRank(entry.rank)}</Text>
                          </View>
                          <Text style={[styles.podiumName, { color: palette.text }]} numberOfLines={1}>
                            {entry.label}
                          </Text>
                          <View
                            style={[
                              styles.titlePill,
                              { backgroundColor: entry.titleBackgroundColor },
                            ]}>
                            <Text
                              style={[
                                styles.titlePillText,
                                { color: entry.titleTextColor },
                              ]}>
                              {entry.titleName}
                            </Text>
                          </View>
                          <View
                            style={[
                              styles.badgePill,
                              { backgroundColor: entry.badgeBackgroundColor },
                            ]}>
                            <Text
                              style={[
                                styles.badgePillText,
                                { color: entry.badgeTextColor },
                              ]}>
                              {entry.badgeName}
                            </Text>
                          </View>
                          <Text style={[styles.podiumScore, { color: rankColor }]}>
                            {formatEntryScore(entry, metric)}
                          </Text>
                          <Text style={[styles.podiumMeta, { color: palette.mutedText }]}>
                            {formatEntrySecondary(entry, metric)}
                          </Text>
                        </View>
                      </LinearGradient>
                    );
                  })}
                </View>
              </View>

              <View style={[styles.progressCard, { backgroundColor: palette.surface }]}>
                <Text style={[styles.sectionTitle, { color: palette.text }]}>Your gamification progress</Text>
                <View style={styles.progressGrid}>
                  <View style={[styles.progressItem, { backgroundColor: palette.surfaceAlt }]}>
                    <Text style={[styles.progressValue, { color: palette.accent }]}>
                      {currentUserEntry?.currentContributionStreak ?? 0}
                    </Text>
                    <Text style={[styles.progressLabel, { color: palette.mutedText }]}>
                      day streak
                    </Text>
                  </View>
                  <View style={[styles.progressItem, { backgroundColor: palette.surfaceAlt }]}>
                    <Text style={[styles.progressValue, { color: palette.text }]}>
                      {unlockedAchievementCount}/{ACHIEVEMENTS.length}
                    </Text>
                    <Text style={[styles.progressLabel, { color: palette.mutedText }]}>
                      achievements
                    </Text>
                  </View>
                </View>
                <Text style={[styles.progressHint, { color: palette.mutedText }]}>
                  Streaks and achievements now feed identity rewards like titles, badges, and special frames.
                </Text>
              </View>

              <View style={[styles.listCard, { backgroundColor: palette.surface }]}>
                <Text style={[styles.sectionTitle, { color: palette.text }]}>Ranking list</Text>
                <Text style={[styles.segmentSubtitle, { color: palette.mutedText }]}>
                  High scores rank first. Ties share the same visible rank.
                </Text>

                <View style={styles.listWrap}>
                  {entries.map((entry) => (
                    <LinearGradient
                      key={entry.userId}
                      colors={entry.frameBorderColors}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 1 }}
                      style={[
                        styles.rowShell,
                        { shadowColor: entry.frameGlowColor },
                      ]}>
                      <View
                        style={[
                          styles.rowCard,
                          {
                            backgroundColor: entry.isCurrentUser
                              ? palette.surfaceAlt
                              : palette.inputBackground,
                            borderColor: entry.isCurrentUser ? palette.accent : "transparent",
                          },
                        ]}>
                        <View style={styles.rankBlock}>
                          <View style={[styles.rankPlateSmall, { backgroundColor: entry.framePlateColor }]}>
                            <Text style={[styles.rankValue, { color: palette.accent }]}>
                              {formatLeaderboardRank(entry.rank)}
                            </Text>
                          </View>
                        </View>

                        <View style={styles.rowCopy}>
                          <View style={styles.rowNameLine}>
                            <Text style={[styles.rowName, { color: palette.text }]} numberOfLines={1}>
                              {entry.label}
                            </Text>
                            {entry.isCurrentUser && (
                              <View style={[styles.youBadge, { backgroundColor: palette.accent }]}>
                                <Text style={styles.youBadgeText}>You</Text>
                              </View>
                            )}
                          </View>

                          <View style={styles.identityRow}>
                            <View
                              style={[
                                styles.inlineTitle,
                                { backgroundColor: entry.titleBackgroundColor },
                              ]}>
                              <Text
                                style={[
                                  styles.inlineTitleText,
                                  { color: entry.titleTextColor },
                                ]}>
                                {entry.titleName}
                              </Text>
                            </View>
                            <View
                              style={[
                                styles.inlineBadge,
                                { backgroundColor: entry.badgeBackgroundColor },
                              ]}>
                              <Text
                                style={[
                                  styles.inlineBadgeText,
                                  { color: entry.badgeTextColor },
                                ]}>
                                {entry.badgeShortLabel}
                              </Text>
                            </View>
                          </View>

                          <Text style={[styles.rowMeta, { color: palette.mutedText }]}>
                            {formatEntrySecondary(entry, metric)} • {entry.currentContributionStreak} day streak •{" "}
                            {entry.achievementCount} achievements
                          </Text>
                        </View>

                        <View style={[styles.scorePill, { backgroundColor: palette.surface }]}>
                          <Text style={[styles.scorePillText, { color: palette.text }]}>
                            {formatEntryScore(entry, metric)}
                          </Text>
                        </View>
                      </View>
                    </LinearGradient>
                  ))}
                </View>
              </View>

              {shouldShowPinnedCurrentUser && currentUserEntry && (
                <View style={[styles.currentUserCard, { backgroundColor: palette.surface }]}>
                  <Text style={[styles.sectionTitle, { color: palette.text }]}>Your position</Text>
                  <LinearGradient
                    colors={currentUserEntry.frameBorderColors}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 1 }}
                    style={styles.rowShell}>
                    <View
                      style={[
                        styles.rowCard,
                        {
                          backgroundColor: palette.surfaceAlt,
                          borderColor: palette.accent,
                        },
                      ]}>
                      <View style={styles.rankBlock}>
                        <View style={[styles.rankPlateSmall, { backgroundColor: currentUserEntry.framePlateColor }]}>
                          <Text style={[styles.rankValue, { color: palette.accent }]}>
                            {formatLeaderboardRank(currentUserEntry.rank)}
                          </Text>
                        </View>
                      </View>

                      <View style={styles.rowCopy}>
                        <View style={styles.rowNameLine}>
                          <Text style={[styles.rowName, { color: palette.text }]}>You</Text>
                          <View style={[styles.youBadge, { backgroundColor: palette.accent }]}>
                            <Text style={styles.youBadgeText}>Current</Text>
                          </View>
                        </View>
                        <View style={styles.identityRow}>
                          <View
                            style={[
                              styles.inlineTitle,
                              { backgroundColor: currentUserEntry.titleBackgroundColor },
                            ]}>
                            <Text
                              style={[
                                styles.inlineTitleText,
                                { color: currentUserEntry.titleTextColor },
                              ]}>
                              {currentUserEntry.titleName}
                            </Text>
                          </View>
                          <View
                            style={[
                              styles.inlineBadge,
                              { backgroundColor: currentUserEntry.badgeBackgroundColor },
                            ]}>
                            <Text
                              style={[
                                styles.inlineBadgeText,
                                { color: currentUserEntry.badgeTextColor },
                              ]}>
                              {currentUserEntry.badgeShortLabel}
                            </Text>
                          </View>
                        </View>
                        <Text style={[styles.rowMeta, { color: palette.mutedText }]}>
                          {formatEntrySecondary(currentUserEntry, metric)} • {currentUserEntry.currentContributionStreak} day streak
                        </Text>
                      </View>

                      <View style={[styles.scorePill, { backgroundColor: palette.surface }]}>
                        <Text style={[styles.scorePillText, { color: palette.text }]}>
                          {formatEntryScore(currentUserEntry, metric)}
                        </Text>
                      </View>
                    </View>
                  </LinearGradient>
                </View>
              )}
            </>
          )}
        </ScrollView>
      </SafeAreaView>
    </AppBackground>
  );
}

function formatEntryScore(entry: LeaderboardEntry, metric: LeaderboardMetric) {
  return metric === "points" ? `${entry.pointsEarned} pts` : `${entry.submissionCount} reports`;
}

function formatEntrySecondary(entry: LeaderboardEntry, metric: LeaderboardMetric) {
  return metric === "points"
    ? `${entry.submissionCount} valid reports`
    : `${entry.pointsEarned} MavPoints earned`;
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  container: {
    paddingHorizontal: 18,
    paddingTop: 56,
    paddingBottom: 32,
    gap: 14,
  },
  backBtn: {
    marginBottom: 2,
  },
  backText: {
    fontSize: 16,
    fontWeight: "700",
  },
  heroCard: {
    borderRadius: 24,
    padding: 20,
  },
  heroEyebrow: {
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 0.8,
    textTransform: "uppercase",
    marginBottom: 8,
  },
  title: {
    fontSize: 28,
    fontWeight: "800",
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    lineHeight: 21,
  },
  heroStats: {
    flexDirection: "row",
    gap: 10,
    marginTop: 18,
  },
  heroStatCard: {
    flex: 1,
    borderRadius: 16,
    paddingVertical: 12,
    paddingHorizontal: 10,
    alignItems: "center",
  },
  heroStatValue: {
    fontSize: 19,
    fontWeight: "800",
  },
  heroStatLabel: {
    fontSize: 11,
    marginTop: 3,
  },
  segmentCard: {
    borderRadius: 20,
    padding: 16,
  },
  segmentTitle: {
    fontSize: 16,
    fontWeight: "800",
    marginBottom: 4,
  },
  segmentSubtitle: {
    fontSize: 12,
    lineHeight: 18,
    marginBottom: 12,
  },
  segmentRow: {
    flexDirection: "row",
    gap: 8,
  },
  segmentButton: {
    flex: 1,
    borderRadius: 14,
    paddingVertical: 11,
    paddingHorizontal: 10,
    alignItems: "center",
  },
  segmentButtonText: {
    fontSize: 13,
    fontWeight: "800",
  },
  stateCard: {
    borderRadius: 20,
    padding: 20,
    alignItems: "center",
  },
  stateTitle: {
    fontSize: 18,
    fontWeight: "800",
    marginBottom: 6,
  },
  stateText: {
    fontSize: 13,
    lineHeight: 20,
    textAlign: "center",
    marginTop: 10,
  },
  podiumCard: {
    borderRadius: 22,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "800",
    marginBottom: 12,
  },
  podiumRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 10,
  },
  podiumShell: {
    flex: 1,
    borderRadius: 20,
    padding: 1.5,
    shadowOpacity: 0.18,
    shadowOffset: { width: 0, height: 8 },
    shadowRadius: 12,
    elevation: 5,
  },
  podiumInner: {
    flex: 1,
    borderRadius: 19,
    paddingHorizontal: 12,
    paddingVertical: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  rankPlate: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 5,
    marginBottom: 10,
  },
  rankPlateText: {
    color: "#FFFFFF",
    fontSize: 11,
    fontWeight: "800",
  },
  podiumName: {
    fontSize: 15,
    fontWeight: "800",
    marginBottom: 8,
  },
  titlePill: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
    marginBottom: 6,
  },
  titlePillText: {
    fontSize: 11,
    fontWeight: "800",
  },
  badgePill: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
    marginBottom: 10,
  },
  badgePillText: {
    fontSize: 11,
    fontWeight: "800",
  },
  podiumScore: {
    fontSize: 18,
    fontWeight: "800",
    marginBottom: 4,
  },
  podiumMeta: {
    fontSize: 11,
    textAlign: "center",
    lineHeight: 16,
  },
  progressCard: {
    borderRadius: 22,
    padding: 16,
  },
  progressGrid: {
    flexDirection: "row",
    gap: 10,
  },
  progressItem: {
    flex: 1,
    borderRadius: 16,
    paddingVertical: 14,
    alignItems: "center",
  },
  progressValue: {
    fontSize: 22,
    fontWeight: "800",
  },
  progressLabel: {
    fontSize: 12,
    marginTop: 3,
  },
  progressHint: {
    marginTop: 10,
    fontSize: 12,
    lineHeight: 18,
  },
  listCard: {
    borderRadius: 22,
    padding: 16,
  },
  listWrap: {
    gap: 10,
  },
  rowShell: {
    borderRadius: 19,
    padding: 1.25,
    shadowOpacity: 0.12,
    shadowOffset: { width: 0, height: 6 },
    shadowRadius: 10,
    elevation: 3,
  },
  rowCard: {
    borderRadius: 18,
    borderWidth: 1,
    paddingVertical: 14,
    paddingHorizontal: 14,
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  rankBlock: {
    width: 58,
  },
  rankPlateSmall: {
    borderRadius: 14,
    paddingVertical: 10,
    paddingHorizontal: 8,
    alignItems: "center",
  },
  rankValue: {
    fontSize: 14,
    fontWeight: "800",
  },
  rowCopy: {
    flex: 1,
  },
  rowNameLine: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 4,
  },
  rowName: {
    flexShrink: 1,
    fontSize: 15,
    fontWeight: "800",
  },
  identityRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    marginBottom: 6,
  },
  inlineTitle: {
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  inlineTitleText: {
    fontSize: 10,
    fontWeight: "800",
  },
  inlineBadge: {
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  inlineBadgeText: {
    fontSize: 10,
    fontWeight: "800",
  },
  rowMeta: {
    fontSize: 12,
    lineHeight: 18,
  },
  scorePill: {
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  scorePillText: {
    fontSize: 12,
    fontWeight: "800",
  },
  youBadge: {
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  youBadgeText: {
    color: "#FFFFFF",
    fontSize: 10,
    fontWeight: "800",
  },
  currentUserCard: {
    borderRadius: 22,
    padding: 16,
  },
});
