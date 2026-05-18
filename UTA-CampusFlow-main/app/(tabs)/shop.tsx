import { AppBackground } from "@/components/app-background";
import { CollectiblePreview } from "@/components/collectible-preview";
import { useAppTheme } from "@/components/app-theme-provider";
import {
  BACKGROUND_THEMES,
  type BackgroundTheme,
  getBackgroundTheme,
} from "@/constants/background-themes";
import {
  ACHIEVEMENTS,
  BADGE_ITEMS,
  FRAME_ITEMS,
  getBadgeById,
  getFrameById,
  getIdentityItem,
  getIdentityTierLabel,
  getTitleById,
  TITLE_ITEMS,
  type IdentityItem,
  type IdentityKind,
} from "@/constants/gamification";
import { auth, db } from "@/firebase/firebase";
import {
  applyIdentitySelection,
  applySelectedTheme,
  buildDefaultUserProfile,
  buildLeaderboardName,
  ensureUserProfile,
  normalizeUnlockedAchievements,
  normalizeUnlockedBadges,
  normalizeUnlockedFrames,
  normalizeUnlockedThemes,
  normalizeUnlockedTitles,
  unlockIdentityItemForUser,
  unlockThemeForUser,
  type UserProfileShape,
} from "@/firebase/user-profile";
import { LinearGradient } from "expo-linear-gradient";
import { useFocusEffect } from "expo-router";
import { onAuthStateChanged } from "firebase/auth";
import { doc, onSnapshot } from "firebase/firestore";
import React, { useEffect, useMemo, useState } from "react";
import { Alert, Dimensions, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";

const { width } = Dimensions.get("window");
const SWATCH_SIZE = (width - 64) / 4;

type ShopMode = "themes" | "identity";

export default function ShopScreen() {
  const { palette, currentTheme, selectedThemeId, unlockedThemes, setPreviewThemeId, isPreviewing } =
    useAppTheme();
  const [user, setUser] = useState(auth.currentUser);
  const [mode, setMode] = useState<ShopMode>("themes");
  const [mavPoints, setMavPoints] = useState(0);
  const [highlightedThemeId, setHighlightedThemeId] = useState(selectedThemeId);
  const [workingKey, setWorkingKey] = useState<string | null>(null);
  const [profile, setProfile] = useState<UserProfileShape>(buildDefaultUserProfile());

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (nextUser) => setUser(nextUser));
    return unsubscribe;
  }, []);

  useEffect(() => {
    return () => setPreviewThemeId(null);
  }, [setPreviewThemeId]);

  useFocusEffect(
    React.useCallback(() => {
      return () => {
        setPreviewThemeId(null);
        setHighlightedThemeId(selectedThemeId);
      };
    }, [selectedThemeId, setPreviewThemeId])
  );

  useEffect(() => {
    if (!user || user.isAnonymous) {
      setMavPoints(0);
      setProfile(buildDefaultUserProfile());
      return;
    }

    ensureUserProfile(user.uid).catch((error) => console.error("Failed to initialize user profile:", error));

    const unsubscribe = onSnapshot(doc(db, "users", user.uid), (snapshot) => {
      const raw = (snapshot.data() ?? {}) as UserProfileShape;
      setMavPoints(typeof raw.points === "number" ? raw.points : 0);
      setProfile({
        ...buildDefaultUserProfile(),
        ...raw,
        unlockedThemes: normalizeUnlockedThemes(raw.unlockedThemes),
        unlockedBadges: normalizeUnlockedBadges(raw.unlockedBadges),
        unlockedTitles: normalizeUnlockedTitles(raw.unlockedTitles),
        unlockedFrames: normalizeUnlockedFrames(raw.unlockedFrames),
        unlockedAchievements: normalizeUnlockedAchievements(raw.unlockedAchievements),
      });
    });

    return unsubscribe;
  }, [user]);

  const isGuest = user?.isAnonymous;
  const highlightedTheme = useMemo(() => getBackgroundTheme(highlightedThemeId), [highlightedThemeId]);
  const unlockedBadges = normalizeUnlockedBadges(profile.unlockedBadges);
  const unlockedTitles = normalizeUnlockedTitles(profile.unlockedTitles);
  const unlockedFrames = normalizeUnlockedFrames(profile.unlockedFrames);
  const unlockedAchievements = normalizeUnlockedAchievements(profile.unlockedAchievements);
  const selectedBadge = getBadgeById(typeof profile.selectedBadge === "string" ? profile.selectedBadge : null);
  const selectedTitle = getTitleById(typeof profile.selectedTitle === "string" ? profile.selectedTitle : null);
  const selectedFrame = getFrameById(typeof profile.selectedFrame === "string" ? profile.selectedFrame : null);
  const ownedBadgeItems = BADGE_ITEMS.filter((item) => unlockedBadges.includes(item.id));
  const ownedTitleItems = TITLE_ITEMS.filter((item) => unlockedTitles.includes(item.id));
  const ownedFrameItems = FRAME_ITEMS.filter((item) => unlockedFrames.includes(item.id));
  const displayName =
    typeof profile.leaderboardName === "string" && profile.leaderboardName.trim()
      ? profile.leaderboardName
      : buildLeaderboardName(user?.email, user?.uid);

  const startPreview = (theme: BackgroundTheme) => {
    setHighlightedThemeId(theme.id);
    setPreviewThemeId(theme.id);
  };

  const stopPreview = () => {
    setPreviewThemeId(null);
    setHighlightedThemeId(selectedThemeId);
  };

  const handleApplyTheme = async (themeId: string) => {
    if (!user || isGuest) return Alert.alert("Sign In Required", "Sign in to save theme unlocks.");
    try {
      setWorkingKey(`theme:${themeId}`);
      await applySelectedTheme(user.uid, themeId);
      setPreviewThemeId(null);
      setHighlightedThemeId(themeId);
    } catch (error: any) {
      Alert.alert("Theme Update Failed", error?.message || "Please try again.");
    } finally {
      setWorkingKey(null);
    }
  };

  const handleUnlockTheme = async (theme: BackgroundTheme) => {
    if (!user || isGuest) return Alert.alert("Sign In Required", "Sign in to unlock themes.");
    try {
      setWorkingKey(`theme:${theme.id}`);
      await unlockThemeForUser(user.uid, theme.id, theme.price);
      setPreviewThemeId(null);
      setHighlightedThemeId(theme.id);
    } catch (error: any) {
      Alert.alert("Unlock Failed", error?.message || "Please try again.");
    } finally {
      setWorkingKey(null);
    }
  };

  const handleIdentity = async (kind: IdentityKind, item: IdentityItem, owned: boolean) => {
    if (!user || isGuest) return Alert.alert("Sign In Required", "Sign in to save identity unlocks.");
    if (!item.purchasable && !owned) {
      return Alert.alert("Achievement Unlock", "This item is unlocked through streaks or achievements.");
    }
    try {
      setWorkingKey(`${kind}:${item.id}`);
      if (owned) await applyIdentitySelection(user.uid, kind, item.id);
      else await unlockIdentityItemForUser(user.uid, kind, item.id, item.price);
    } catch (error: any) {
      Alert.alert("Update Failed", error?.message || "Please try again.");
    } finally {
      setWorkingKey(null);
    }
  };

  const renderThemeSwatch = (theme: BackgroundTheme) => {
    const selected = highlightedThemeId === theme.id;
    const owned = unlockedThemes.includes(theme.id);
    return (
      <TouchableOpacity key={theme.id} activeOpacity={0.88} onPress={() => startPreview(theme)}>
        <LinearGradient
          colors={theme.gradient.colors}
          start={theme.gradient.start}
          end={theme.gradient.end}
          style={[styles.swatch, { width: SWATCH_SIZE, borderColor: selected ? "#FFFFFF" : theme.palette.border }]}>
          <Text style={styles.swatchText}>{selectedThemeId === theme.id ? "Applied" : owned ? "Owned" : `${theme.price}`}</Text>
        </LinearGradient>
      </TouchableOpacity>
    );
  };

  const renderIdentityCard = (kind: IdentityKind, item: IdentityItem, selectedId: string, unlocked: string[]) => {
    const owned = unlocked.includes(item.id);
    const applied = selectedId === item.id;
    const busy = workingKey === `${kind}:${item.id}`;
    const disabled = applied || (!owned && (!item.purchasable || mavPoints < item.price));
    return (
      <View key={item.id} style={[styles.itemCard, { backgroundColor: palette.inputBackground, borderColor: palette.border }]}>
        <View style={styles.itemHead}>
          <View style={styles.itemCopy}>
            <Text style={[styles.itemTitle, { color: palette.text }]}>{item.name}</Text>
            <Text style={[styles.itemDesc, { color: palette.mutedText }]}>{item.description}</Text>
          </View>
          <View style={styles.previewColumn}>
            <CollectiblePreview art={item.art} kind={kind} label={item.previewLabel} size={82} />
            <View style={[styles.previewMetaPill, { backgroundColor: palette.surfaceAlt }]}>
              <Text style={[styles.previewMetaText, { color: palette.accentStrong }]}>
                {item.price === 0 ? getIdentityTierLabel(item.tier) : `${item.price} pts`}
              </Text>
            </View>
          </View>
        </View>
        <TouchableOpacity
          style={[styles.actionBtn, { backgroundColor: disabled ? palette.mutedText : palette.accent }]}
          disabled={disabled || busy}
          onPress={() => handleIdentity(kind, item, owned)}>
          <Text style={styles.actionBtnText}>
            {applied ? "Applied" : busy ? "Saving..." : owned ? "Apply" : item.purchasable ? `Unlock for ${item.price}` : "Unlock via achievement"}
          </Text>
        </TouchableOpacity>
      </View>
    );
  };

  const renderAchievementCard = (achievement: (typeof ACHIEVEMENTS)[number]) => {
    const unlocked = unlockedAchievements.includes(achievement.id);
    const rewardItem = achievement.reward
      ? getIdentityItem(achievement.reward.kind, achievement.reward.itemId)
      : null;

    return (
      <View
        key={achievement.id}
        style={[
          styles.itemCard,
          {
            backgroundColor: unlocked ? palette.surfaceAlt : palette.inputBackground,
            borderColor: unlocked ? palette.accent : palette.border,
          },
        ]}>
        <View style={styles.itemHead}>
          <View style={styles.itemCopy}>
            <Text style={[styles.itemTitle, { color: palette.text }]}>{achievement.name}</Text>
            <Text style={[styles.itemDesc, { color: palette.mutedText }]}>{achievement.description}</Text>
            <Text style={[styles.achievementText, { color: palette.mutedText }]}>
              {unlocked ? "Unlocked" : achievement.requirementLabel}
            </Text>
          </View>
          <View style={styles.previewColumn}>
            <CollectiblePreview
              art={achievement.art}
              kind="achievement"
              label={achievement.previewLabel}
              size={82}
            />
            <View style={[styles.previewMetaPill, { backgroundColor: palette.surfaceAlt }]}>
              <Text
                style={[
                  styles.previewMetaText,
                  { color: unlocked ? palette.accent : palette.accentStrong },
                ]}>
                {unlocked ? "Done" : achievement.requirementLabel}
              </Text>
            </View>
          </View>
        </View>

        {rewardItem && (
          <View style={[styles.rewardRow, { backgroundColor: palette.surfaceAlt }]}>
            <CollectiblePreview
              art={rewardItem.art}
              kind={rewardItem.kind}
              label={rewardItem.previewLabel}
              size={42}
            />
            <View style={styles.rewardCopy}>
              <Text style={[styles.rewardTitle, { color: palette.text }]}>Reward</Text>
              <Text style={[styles.rewardMeta, { color: palette.mutedText }]}>{rewardItem.name}</Text>
            </View>
          </View>
        )}
      </View>
    );
  };

  const renderInventoryGroup = (
    label: string,
    kind: IdentityKind,
    items: IdentityItem[],
    selectedId: string
  ) => (
    <View style={styles.inventoryGroup}>
      <View style={styles.inventoryHeader}>
        <Text style={[styles.inventoryTitle, { color: palette.text }]}>{label}</Text>
        <Text style={[styles.inventoryCount, { color: palette.mutedText }]}>{items.length} owned</Text>
      </View>
      <View style={styles.inventoryGrid}>
        {items.map((item) => {
          const equipped = item.id === selectedId;
          const busy = workingKey === `${kind}:${item.id}`;

          return (
            <TouchableOpacity
              key={`${kind}:${item.id}`}
              style={[
                styles.inventoryCard,
                {
                  backgroundColor: equipped ? palette.surfaceAlt : palette.inputBackground,
                  borderColor: equipped ? palette.accent : palette.border,
                },
              ]}
              activeOpacity={0.88}
              disabled={equipped || busy}
              onPress={() => handleIdentity(kind, item, true)}>
              <CollectiblePreview art={item.art} kind={kind} label={item.previewLabel} size={60} />
              <Text style={[styles.inventoryName, { color: palette.text }]} numberOfLines={2}>
                {item.name}
              </Text>
              <View
                style={[
                  styles.inventoryStatusPill,
                  { backgroundColor: equipped ? palette.accent : palette.surfaceAlt },
                ]}>
                <Text
                  style={[
                    styles.inventoryStatusText,
                    { color: equipped ? palette.accentText : palette.text },
                  ]}>
                  {busy ? "Saving..." : equipped ? "Equipped" : "Owned"}
                </Text>
              </View>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );

  const themeOwned = unlockedThemes.includes(highlightedTheme.id);
  const themeApplied = selectedThemeId === highlightedTheme.id;
  const themeBusy = workingKey === `theme:${highlightedTheme.id}`;

  return (
    <AppBackground>
      <ScrollView contentContainerStyle={[styles.container, { paddingTop: 84 }]} showsVerticalScrollIndicator={false}>
        <Text style={[styles.title, { color: palette.text }]}>Gamification Shop</Text>
        <Text style={[styles.subtitle, { color: palette.mutedText }]}>Themes change the app mood. Identity items change how you show up on the leaderboard.</Text>

        <View style={[styles.segment, { backgroundColor: palette.surface, borderColor: palette.border }]}>
          {(["themes", "identity"] as const).map((value) => (
            <TouchableOpacity key={value} style={[styles.segmentBtn, { backgroundColor: mode === value ? palette.accent : palette.surfaceAlt }]} onPress={() => setMode(value)}>
              <Text style={[styles.segmentBtnText, { color: mode === value ? palette.accentText : palette.text }]}>{value === "themes" ? "Themes" : "Identity"}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <View style={[styles.hero, { backgroundColor: palette.surface, borderColor: palette.border }]}>
          <View style={styles.headerRow}>
            <View>
              <Text style={[styles.eyebrow, { color: palette.mutedText }]}>{mode === "themes" ? "Current Theme" : "Profile Identity"}</Text>
              <Text style={[styles.heroTitle, { color: palette.text }]}>{mode === "themes" ? currentTheme.name : displayName}</Text>
              <Text style={[styles.heroSub, { color: palette.mutedText }]}>{mode === "themes" ? currentTheme.vibe : `${selectedTitle.name} • ${selectedBadge.name}`}</Text>
            </View>
            <View style={[styles.pill, { backgroundColor: palette.surfaceAlt }]}><Text style={[styles.pillText, { color: palette.accentStrong }]}>{mavPoints} pts</Text></View>
          </View>

          {mode === "themes" ? (
            <>
              <LinearGradient colors={currentTheme.gradient.colors} start={currentTheme.gradient.start} end={currentTheme.gradient.end} style={styles.preview} />
              {isPreviewing && (
                <TouchableOpacity style={[styles.secondaryBtn, { backgroundColor: palette.surfaceAlt }]} onPress={stopPreview}>
                  <Text style={[styles.secondaryBtnText, { color: palette.text }]}>End preview</Text>
                </TouchableOpacity>
              )}
            </>
          ) : (
            <LinearGradient colors={selectedFrame.borderColors} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.identityShell}>
              <View style={[styles.identityInner, { backgroundColor: palette.inputBackground }]}>
                <Text style={[styles.identityName, { color: palette.text }]}>{displayName}</Text>
                <View style={styles.heroCollectibles}>
                  <CollectiblePreview art={selectedBadge.art} kind="badge" label={selectedBadge.previewLabel} size={68} />
                  <CollectiblePreview art={selectedTitle.art} kind="title" label={selectedTitle.previewLabel} size={68} />
                  <CollectiblePreview art={selectedFrame.art} kind="frame" label={selectedFrame.previewLabel} size={68} />
                </View>
                <View style={styles.inlineRow}>
                  <View style={[styles.inlineChip, { backgroundColor: selectedTitle.backgroundColor }]}><Text style={[styles.inlineChipText, { color: selectedTitle.textColor }]}>{selectedTitle.name}</Text></View>
                  <View style={[styles.inlineChip, { backgroundColor: selectedBadge.backgroundColor }]}><Text style={[styles.inlineChipText, { color: selectedBadge.textColor }]}>{selectedBadge.name}</Text></View>
                </View>
                <View style={styles.statsRow}>
                  <View style={[styles.stat, { backgroundColor: palette.surfaceAlt }]}><Text style={[styles.statValue, { color: palette.accent }]}>{typeof profile.currentContributionStreak === "number" ? profile.currentContributionStreak : 0}</Text><Text style={[styles.statLabel, { color: palette.mutedText }]}>day streak</Text></View>
                  <View style={[styles.stat, { backgroundColor: palette.surfaceAlt }]}><Text style={[styles.statValue, { color: palette.text }]}>{typeof profile.totalSurveySubmissions === "number" ? profile.totalSurveySubmissions : 0}</Text><Text style={[styles.statLabel, { color: palette.mutedText }]}>reports</Text></View>
                  <View style={[styles.stat, { backgroundColor: palette.surfaceAlt }]}><Text style={[styles.statValue, { color: palette.text }]}>{unlockedAchievements.length}</Text><Text style={[styles.statLabel, { color: palette.mutedText }]}>achievements</Text></View>
                </View>
              </View>
            </LinearGradient>
          )}
        </View>

        {mode === "identity" && (
          <View style={[styles.section, { backgroundColor: palette.surface, borderColor: palette.border }]}>
            <Text style={[styles.sectionTitle, { color: palette.text }]}>Your inventory</Text>
            <Text style={[styles.inventoryHint, { color: palette.mutedText }]}>
              Owned identity items live here. Equipped items are marked, and you can tap owned ones to switch fast.
            </Text>
            {renderInventoryGroup("Badges", "badge", ownedBadgeItems, selectedBadge.id)}
            {renderInventoryGroup("Titles", "title", ownedTitleItems, selectedTitle.id)}
            {renderInventoryGroup("Frames", "frame", ownedFrameItems, selectedFrame.id)}
          </View>
        )}

        {mode === "themes" ? (
          <>
            <View style={[styles.section, { backgroundColor: palette.surface, borderColor: palette.border }]}>
              <Text style={[styles.sectionTitle, { color: palette.text }]}>Theme palette</Text>
              <View style={styles.swatchGrid}>{BACKGROUND_THEMES.map(renderThemeSwatch)}</View>
            </View>
            <View style={[styles.section, { backgroundColor: palette.surface, borderColor: palette.border }]}>
              <Text style={[styles.sectionTitle, { color: palette.text }]}>{highlightedTheme.name}</Text>
              <Text style={[styles.itemDesc, { color: palette.mutedText }]}>{highlightedTheme.description}</Text>
              <View style={styles.row}>
                <TouchableOpacity style={[styles.secondaryBtn, { backgroundColor: palette.surfaceAlt }]} onPress={() => startPreview(highlightedTheme)}>
                  <Text style={[styles.secondaryBtnText, { color: palette.text }]}>Preview</Text>
                </TouchableOpacity>
                {themeApplied ? (
                  <View style={[styles.actionBtn, { backgroundColor: palette.accent }]}><Text style={styles.actionBtnText}>Applied</Text></View>
                ) : themeOwned ? (
                  <TouchableOpacity style={[styles.actionBtn, { backgroundColor: palette.accent }]} disabled={themeBusy} onPress={() => handleApplyTheme(highlightedTheme.id)}>
                    <Text style={styles.actionBtnText}>{themeBusy ? "Applying..." : "Apply"}</Text>
                  </TouchableOpacity>
                ) : (
                  <TouchableOpacity style={[styles.actionBtn, { backgroundColor: mavPoints >= highlightedTheme.price ? palette.accent : palette.mutedText }]} disabled={themeBusy || mavPoints < highlightedTheme.price} onPress={() => handleUnlockTheme(highlightedTheme)}>
                    <Text style={styles.actionBtnText}>{themeBusy ? "Unlocking..." : `Unlock for ${highlightedTheme.price}`}</Text>
                  </TouchableOpacity>
                )}
              </View>
            </View>
          </>
        ) : (
          <>
            <View style={[styles.section, { backgroundColor: palette.surface, borderColor: palette.border }]}><Text style={[styles.sectionTitle, { color: palette.text }]}>Badges</Text>{BADGE_ITEMS.map((item) => renderIdentityCard("badge", item, selectedBadge.id, unlockedBadges))}</View>
            <View style={[styles.section, { backgroundColor: palette.surface, borderColor: palette.border }]}><Text style={[styles.sectionTitle, { color: palette.text }]}>Titles</Text>{TITLE_ITEMS.map((item) => renderIdentityCard("title", item, selectedTitle.id, unlockedTitles))}</View>
            <View style={[styles.section, { backgroundColor: palette.surface, borderColor: palette.border }]}><Text style={[styles.sectionTitle, { color: palette.text }]}>Frames</Text>{FRAME_ITEMS.map((item) => renderIdentityCard("frame", item, selectedFrame.id, unlockedFrames))}</View>
            <View style={[styles.section, { backgroundColor: palette.surface, borderColor: palette.border }]}>
              <Text style={[styles.sectionTitle, { color: palette.text }]}>Achievements & streaks</Text>
              {ACHIEVEMENTS.map(renderAchievementCard)}
            </View>
          </>
        )}
      </ScrollView>
    </AppBackground>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, paddingBottom: 40 },
  title: { fontSize: 28, fontWeight: "800", marginBottom: 4 },
  subtitle: { fontSize: 14, lineHeight: 20, marginBottom: 14 },
  segment: { borderRadius: 18, borderWidth: 1, padding: 10, marginBottom: 14, flexDirection: "row", gap: 8 },
  segmentBtn: { flex: 1, borderRadius: 14, paddingVertical: 12, alignItems: "center" },
  segmentBtnText: { fontSize: 14, fontWeight: "800" },
  hero: { borderRadius: 20, borderWidth: 1, padding: 16, marginBottom: 14 },
  headerRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", gap: 12, marginBottom: 12 },
  eyebrow: { fontSize: 12, textTransform: "uppercase", fontWeight: "600", marginBottom: 4 },
  heroTitle: { fontSize: 22, fontWeight: "800" },
  heroSub: { fontSize: 13, marginTop: 4 },
  pill: { borderRadius: 999, paddingHorizontal: 12, paddingVertical: 8 },
  pillText: { fontSize: 12, fontWeight: "800" },
  preview: { height: 150, borderRadius: 18 },
  secondaryBtn: { borderRadius: 14, alignItems: "center", justifyContent: "center", paddingVertical: 13, paddingHorizontal: 14, marginTop: 12, flex: 1 },
  secondaryBtnText: { fontSize: 14, fontWeight: "700" },
  identityShell: { borderRadius: 20, padding: 1.5 },
  identityInner: { borderRadius: 19, padding: 14 },
  identityName: { fontSize: 21, fontWeight: "800", marginBottom: 8 },
  heroCollectibles: { flexDirection: "row", gap: 8, marginBottom: 12 },
  inlineRow: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginBottom: 12 },
  inlineChip: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 6 },
  inlineChipText: { fontSize: 11, fontWeight: "800" },
  statsRow: { flexDirection: "row", gap: 8 },
  stat: { flex: 1, borderRadius: 16, paddingVertical: 12, alignItems: "center" },
  statValue: { fontSize: 18, fontWeight: "800" },
  statLabel: { fontSize: 11, marginTop: 2 },
  section: { borderRadius: 20, borderWidth: 1, padding: 14, marginBottom: 14 },
  sectionTitle: { fontSize: 18, fontWeight: "800", marginBottom: 10 },
  inventoryHint: { fontSize: 12, lineHeight: 18, marginBottom: 14 },
  inventoryGroup: { marginBottom: 14 },
  inventoryHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 8 },
  inventoryTitle: { fontSize: 14, fontWeight: "800" },
  inventoryCount: { fontSize: 12, fontWeight: "700" },
  inventoryGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  inventoryCard: { width: "31%", minWidth: 96, borderRadius: 16, borderWidth: 1, paddingVertical: 12, paddingHorizontal: 8, alignItems: "center", gap: 8 },
  inventoryName: { fontSize: 11, fontWeight: "800", textAlign: "center", lineHeight: 15, minHeight: 30 },
  inventoryStatusPill: { borderRadius: 999, paddingHorizontal: 9, paddingVertical: 5 },
  inventoryStatusText: { fontSize: 10, fontWeight: "800" },
  swatchGrid: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  swatch: { height: SWATCH_SIZE * 0.85, borderRadius: 14, borderWidth: 2, justifyContent: "flex-end", padding: 8 },
  swatchText: { alignSelf: "flex-end", color: "#FFFFFF", fontSize: 11, fontWeight: "700", backgroundColor: "rgba(0,0,0,0.28)", paddingHorizontal: 8, paddingVertical: 4, borderRadius: 999 },
  row: { flexDirection: "row", gap: 10, marginTop: 12 },
  itemCard: { borderRadius: 16, borderWidth: 1, padding: 14, marginBottom: 10 },
  itemHead: { flexDirection: "row", gap: 12, marginBottom: 10, alignItems: "flex-start" },
  itemCopy: { flex: 1, minWidth: 0 },
  previewColumn: { width: 94, alignItems: "center", gap: 8 },
  previewMetaPill: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 6 },
  previewMetaText: { fontSize: 11, fontWeight: "800", textAlign: "center" },
  itemTitle: { fontSize: 15, fontWeight: "800", marginBottom: 4 },
  itemDesc: { fontSize: 12, lineHeight: 18 },
  actionBtn: { flex: 1.1, borderRadius: 14, alignItems: "center", justifyContent: "center", paddingVertical: 13, paddingHorizontal: 14 },
  actionBtnText: { color: "#FFFFFF", fontSize: 14, fontWeight: "800" },
  achievementText: { fontSize: 12, lineHeight: 18, marginTop: 8 },
  rewardRow: { marginTop: 8, borderRadius: 14, padding: 10, flexDirection: "row", alignItems: "center", gap: 10 },
  rewardCopy: { flex: 1 },
  rewardTitle: { fontSize: 12, fontWeight: "800", marginBottom: 2 },
  rewardMeta: { fontSize: 12, lineHeight: 17 },
});
