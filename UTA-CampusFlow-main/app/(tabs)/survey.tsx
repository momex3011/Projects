import { AppBackground } from "@/components/app-background";
import { useAppTheme } from "@/components/app-theme-provider";
import {
  CAMPUS_SURVEY_COOLDOWN_MINUTES,
  CAMPUS_SURVEY_DUPLICATE_WINDOW_MINUTES,
  CAMPUS_SURVEY_LOCATION_SECTIONS,
  CAMPUS_SURVEY_REWARD_POINTS,
  CROWD_LEVEL_OPTIONS,
  type CrowdLevelId,
  formatCampusLocationLabel,
  getCampusLocationById,
  getCrowdOptionById,
  getNoiseOptionById,
  NOISE_LEVEL_OPTIONS,
  type NoiseLevelId,
} from "@/constants/campus-survey";
import { submitCampusSurveyReport } from "@/firebase/campus-surveys";
import { auth } from "@/firebase/firebase";
import * as Haptics from "expo-haptics";
import React, { useMemo, useState } from "react";
import {
  ActivityIndicator,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

type FeedbackTone = "success" | "info" | "warning";

type FeedbackState = {
  tone: FeedbackTone;
  title: string;
  message: string;
} | null;

export default function SurveyScreen() {
  const { palette } = useAppTheme();
  const [locationId, setLocationId] = useState<string | null>(null);
  const [floor, setFloor] = useState<number | null>(null);
  const [crowdLevel, setCrowdLevel] = useState<CrowdLevelId | null>(null);
  const [noiseLevel, setNoiseLevel] = useState<NoiseLevelId | null>(null);
  const [locationModalVisible, setLocationModalVisible] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackState>(null);

  const user = auth.currentUser;
  const isGuest = user?.isAnonymous;

  const selectedLocation = useMemo(
    () => getCampusLocationById(locationId),
    [locationId]
  );
  const selectedCrowd = useMemo(
    () => (crowdLevel ? getCrowdOptionById(crowdLevel) : null),
    [crowdLevel]
  );
  const selectedNoise = useMemo(
    () => (noiseLevel ? getNoiseOptionById(noiseLevel) : null),
    [noiseLevel]
  );

  const canSubmit = Boolean(locationId && crowdLevel && noiseLevel && !isGuest);
  const selectedLocationLabel =
    locationId && selectedLocation
      ? formatCampusLocationLabel(locationId, selectedLocation.floors?.length ? floor : null)
      : "Choose a campus spot";

  const clearFeedback = () => setFeedback(null);

  const handleLocationSelect = (nextLocationId: string) => {
    const nextLocation = getCampusLocationById(nextLocationId);
    setLocationId(nextLocationId);
    setFloor(nextLocation?.floors?.[0] ?? null);
    setLocationModalVisible(false);
    clearFeedback();
    void Haptics.selectionAsync();
  };

  const handleCrowdSelect = (value: CrowdLevelId) => {
    setCrowdLevel(value);
    clearFeedback();
    void Haptics.selectionAsync();
  };

  const handleNoiseSelect = (value: NoiseLevelId) => {
    setNoiseLevel(value);
    clearFeedback();
    void Haptics.selectionAsync();
  };

  const handleSubmit = async () => {
    if (!user || isGuest) {
      setFeedback({
        tone: "warning",
        title: "Sign in required",
        message: "Registered users can submit reports and earn MavPoints.",
      });
      return;
    }

    if (!locationId || !crowdLevel || !noiseLevel) {
      setFeedback({
        tone: "warning",
        title: "Finish the quick check-in",
        message: "Choose a location, crowd level, and noise level before submitting.",
      });
      return;
    }

    setIsSubmitting(true);
    clearFeedback();

    try {
      const result = await submitCampusSurveyReport({
        userId: user.uid,
        locationId,
        floor,
        crowdLevel,
        noiseLevel,
      });

      if (result.status === "success") {
        setLocationId(null);
        setFloor(null);
        setCrowdLevel(null);
        setNoiseLevel(null);
        setFeedback({
          tone: "success",
          title: "Report saved",
          message: `${result.locationLabel} was updated and you earned ${result.pointsAwarded} MavPoints.`,
        });
        void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        return;
      }

      if (result.status === "duplicate") {
        setFeedback({
          tone: "info",
          title: "Recent report already counted",
          message: `We already have your recent check-in for ${result.locationLabel}. Try again if the space changes.`,
        });
        void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
        return;
      }

      setFeedback({
        tone: "warning",
        title: "Cooldown still active",
        message: `You can submit another campus report in about ${result.minutesLeft} minute${
          result.minutesLeft === 1 ? "" : "s"
        }.`,
      });
      void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
    } catch (error) {
      console.error("Error submitting campus report:", error);
      setFeedback({
        tone: "warning",
        title: "Could not submit report",
        message: "Please try again in a moment.",
      });
      void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const feedbackColors =
    feedback?.tone === "success"
      ? {
          backgroundColor: palette.surfaceAlt,
          borderColor: palette.accent,
          titleColor: palette.text,
          bodyColor: palette.mutedText,
        }
      : feedback?.tone === "info"
        ? {
            backgroundColor: palette.surface,
            borderColor: palette.border,
            titleColor: palette.text,
            bodyColor: palette.mutedText,
          }
        : {
            backgroundColor: palette.surface,
            borderColor: palette.accentStrong,
            titleColor: palette.text,
            bodyColor: palette.mutedText,
          };

  return (
    <AppBackground>
      <SafeAreaView style={styles.safeArea}>
        <ScrollView
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}>
          <View style={[styles.heroCard, { backgroundColor: palette.surface }]}>
            <Text style={[styles.heroEyebrow, { color: palette.accentStrong }]}>
              Campus Report
            </Text>
            <Text style={[styles.title, { color: palette.text }]}>Quick campus check-in</Text>
            <Text style={[styles.subtitle, { color: palette.mutedText }]}>
              Share what the space feels like in a few taps. Valid reports still earn{" "}
              {CAMPUS_SURVEY_REWARD_POINTS} MavPoints.
            </Text>

            <View style={styles.statRow}>
              <View style={[styles.statPill, { backgroundColor: palette.surfaceAlt }]}>
                <Text style={[styles.statValue, { color: palette.accent }]}>
                  +{CAMPUS_SURVEY_REWARD_POINTS}
                </Text>
                <Text style={[styles.statLabel, { color: palette.mutedText }]}>per report</Text>
              </View>
              <View style={[styles.statPill, { backgroundColor: palette.surfaceAlt }]}>
                <Text style={[styles.statValue, { color: palette.text }]}>
                  {CAMPUS_SURVEY_COOLDOWN_MINUTES}m
                </Text>
                <Text style={[styles.statLabel, { color: palette.mutedText }]}>cooldown</Text>
              </View>
              <View style={[styles.statPill, { backgroundColor: palette.surfaceAlt }]}>
                <Text style={[styles.statValue, { color: palette.text }]}>
                  {CAMPUS_SURVEY_DUPLICATE_WINDOW_MINUTES}m
                </Text>
                <Text style={[styles.statLabel, { color: palette.mutedText }]}>duplicate check</Text>
              </View>
            </View>
          </View>

          {feedback && (
            <View
              style={[
                styles.feedbackCard,
                {
                  backgroundColor: feedbackColors.backgroundColor,
                  borderColor: feedbackColors.borderColor,
                },
              ]}>
              <Text style={[styles.feedbackTitle, { color: feedbackColors.titleColor }]}>
                {feedback.title}
              </Text>
              <Text style={[styles.feedbackMessage, { color: feedbackColors.bodyColor }]}>
                {feedback.message}
              </Text>
            </View>
          )}

          {isGuest && (
            <View
              style={[
                styles.feedbackCard,
                {
                  backgroundColor: palette.surface,
                  borderColor: palette.border,
                },
              ]}>
              <Text style={[styles.feedbackTitle, { color: palette.text }]}>Guest view only</Text>
              <Text style={[styles.feedbackMessage, { color: palette.mutedText }]}>
                Sign in with your student account to submit reports and collect MavPoints.
              </Text>
            </View>
          )}

          <View style={[styles.sectionCard, { backgroundColor: palette.surface }]}>
            <Text style={[styles.sectionStep, { color: palette.accentStrong }]}>1. Location</Text>
            <Text style={[styles.sectionTitle, { color: palette.text }]}>Where are you right now?</Text>
            <Text style={[styles.sectionDescription, { color: palette.mutedText }]}>
              Locations are grouped by campus area so they are easier to scan.
            </Text>

            <TouchableOpacity
              style={[
                styles.locationButton,
                {
                  backgroundColor: palette.inputBackground,
                  borderColor: palette.border,
                },
              ]}
              onPress={() => setLocationModalVisible(true)}
              activeOpacity={0.86}>
              <View style={styles.locationButtonText}>
                <Text style={[styles.locationButtonLabel, { color: palette.text }]}>
                  {selectedLocationLabel}
                </Text>
                <Text style={[styles.locationButtonHint, { color: palette.mutedText }]}>
                  {selectedLocation ? "Tap to change location" : "Tap to browse campus spots"}
                </Text>
              </View>
              <View style={[styles.locationBadge, { backgroundColor: palette.surfaceAlt }]}>
                <Text style={[styles.locationBadgeText, { color: palette.accent }]}>
                  {selectedLocation?.short ?? "Pick"}
                </Text>
              </View>
            </TouchableOpacity>

            {selectedLocation?.floors?.length && (
              <View style={styles.floorWrap}>
                {selectedLocation.floors.map((level) => {
                  const isActive = floor === level;
                  return (
                    <TouchableOpacity
                      key={level}
                      style={[
                        styles.floorChip,
                        {
                          backgroundColor: isActive ? palette.accent : palette.surfaceAlt,
                          borderColor: isActive ? palette.accent : palette.border,
                        },
                      ]}
                      onPress={() => {
                        setFloor(level);
                        clearFeedback();
                        void Haptics.selectionAsync();
                      }}
                      activeOpacity={0.88}>
                      <Text
                        style={[
                          styles.floorChipText,
                          { color: isActive ? palette.accentText : palette.text },
                        ]}>
                        Floor {level}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            )}
          </View>

          <View style={[styles.sectionCard, { backgroundColor: palette.surface }]}>
            <Text style={[styles.sectionStep, { color: palette.accentStrong }]}>2. Crowd</Text>
            <Text style={[styles.sectionTitle, { color: palette.text }]}>
              How crowded does it feel?
            </Text>
            <Text style={[styles.sectionDescription, { color: palette.mutedText }]}>
              Pick the option that best matches the space right now.
            </Text>

            <View style={styles.choiceList}>
              {CROWD_LEVEL_OPTIONS.map((option) => {
                const isActive = crowdLevel === option.id;
                return (
                  <TouchableOpacity
                    key={option.id}
                    style={[
                      styles.choiceCard,
                      {
                        backgroundColor: isActive ? palette.surfaceAlt : palette.inputBackground,
                        borderColor: isActive ? option.color : palette.border,
                      },
                    ]}
                    onPress={() => handleCrowdSelect(option.id)}
                    activeOpacity={0.9}>
                    <View style={[styles.choiceDot, { backgroundColor: option.color }]} />
                    <View style={styles.choiceCopy}>
                      <Text style={[styles.choiceTitle, { color: palette.text }]}>
                        {option.label}
                      </Text>
                      <Text style={[styles.choiceDescription, { color: palette.mutedText }]}>
                        {option.description}
                      </Text>
                    </View>
                    <Text style={[styles.choiceShortLabel, { color: palette.mutedText }]}>
                      {option.shortLabel}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>

          <View style={[styles.sectionCard, { backgroundColor: palette.surface }]}>
            <Text style={[styles.sectionStep, { color: palette.accentStrong }]}>3. Noise</Text>
            <Text style={[styles.sectionTitle, { color: palette.text }]}>How loud is it?</Text>
            <Text style={[styles.sectionDescription, { color: palette.mutedText }]}>
              Keep it simple and student-friendly. No need to overthink it.
            </Text>

            <View style={styles.choiceList}>
              {NOISE_LEVEL_OPTIONS.map((option) => {
                const isActive = noiseLevel === option.id;
                return (
                  <TouchableOpacity
                    key={option.id}
                    style={[
                      styles.choiceCard,
                      {
                        backgroundColor: isActive ? palette.surfaceAlt : palette.inputBackground,
                        borderColor: isActive ? option.color : palette.border,
                      },
                    ]}
                    onPress={() => handleNoiseSelect(option.id)}
                    activeOpacity={0.9}>
                    <View style={[styles.choiceDot, { backgroundColor: option.color }]} />
                    <View style={styles.choiceCopy}>
                      <Text style={[styles.choiceTitle, { color: palette.text }]}>
                        {option.label}
                      </Text>
                      <Text style={[styles.choiceDescription, { color: palette.mutedText }]}>
                        {option.description}
                      </Text>
                    </View>
                    <Text style={[styles.choiceShortLabel, { color: palette.mutedText }]}>
                      {option.shortLabel}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>

          <View style={[styles.summaryCard, { backgroundColor: palette.surface }]}>
            <Text style={[styles.sectionTitle, { color: palette.text }]}>Submission preview</Text>
            <View style={styles.summaryRow}>
              <Text style={[styles.summaryKey, { color: palette.mutedText }]}>Location</Text>
              <Text style={[styles.summaryValue, { color: palette.text }]}>{selectedLocationLabel}</Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={[styles.summaryKey, { color: palette.mutedText }]}>Crowd</Text>
              <Text style={[styles.summaryValue, { color: palette.text }]}>
                {selectedCrowd?.label ?? "Not selected"}
              </Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={[styles.summaryKey, { color: palette.mutedText }]}>Noise</Text>
              <Text style={[styles.summaryValue, { color: palette.text }]}>
                {selectedNoise?.label ?? "Not selected"}
              </Text>
            </View>
            <Text style={[styles.summaryHint, { color: palette.mutedText }]}>
              Identical reports from the same user inside {CAMPUS_SURVEY_DUPLICATE_WINDOW_MINUTES}{" "}
              minutes are skipped automatically so the data stays cleaner.
            </Text>
          </View>

          <TouchableOpacity
            style={[
              styles.submitButton,
              {
                backgroundColor: canSubmit ? palette.accent : palette.surfaceAlt,
                opacity: isSubmitting ? 0.85 : 1,
              },
            ]}
            onPress={handleSubmit}
            disabled={isSubmitting}
            activeOpacity={0.9}>
            {isSubmitting ? (
              <ActivityIndicator color={palette.accentText} />
            ) : (
              <Text
                style={[
                  styles.submitButtonText,
                  { color: canSubmit ? palette.accentText : palette.mutedText },
                ]}>
                {isGuest
                  ? "Sign in to submit reports"
                  : canSubmit
                    ? `Submit report +${CAMPUS_SURVEY_REWARD_POINTS}`
                    : "Complete the quick check-in"}
              </Text>
            )}
          </TouchableOpacity>
        </ScrollView>

        <Modal
          visible={locationModalVisible}
          transparent
          animationType="slide"
          onRequestClose={() => setLocationModalVisible(false)}>
          <View style={styles.modalOverlay}>
            <Pressable
              style={StyleSheet.absoluteFill}
              onPress={() => setLocationModalVisible(false)}
            />
            <View style={[styles.modalSheet, { backgroundColor: palette.surface }]}>
              <View style={[styles.sheetHandle, { backgroundColor: palette.border }]} />
              <Text style={[styles.modalTitle, { color: palette.text }]}>Choose a location</Text>
              <Text style={[styles.modalSubtitle, { color: palette.mutedText }]}>
                Pick the campus spot you are reporting on.
              </Text>

              <ScrollView
                style={styles.modalScroll}
                contentContainerStyle={styles.modalScrollContent}
                showsVerticalScrollIndicator={false}>
                {CAMPUS_SURVEY_LOCATION_SECTIONS.map((section) => (
                  <View key={section.title} style={styles.modalSection}>
                    <Text style={[styles.modalSectionTitle, { color: palette.text }]}>
                      {section.title}
                    </Text>
                    <Text style={[styles.modalSectionDescription, { color: palette.mutedText }]}>
                      {section.description}
                    </Text>

                    {section.data.map((location) => {
                      const isActive = location.id === locationId;
                      return (
                        <TouchableOpacity
                          key={location.id}
                          style={[
                            styles.modalLocationRow,
                            {
                              backgroundColor: isActive
                                ? palette.surfaceAlt
                                : palette.inputBackground,
                              borderColor: isActive ? palette.accent : palette.border,
                            },
                          ]}
                          onPress={() => handleLocationSelect(location.id)}
                          activeOpacity={0.9}>
                          <View style={[styles.modalLocationBadge, { backgroundColor: palette.surface }]}>
                            <Text style={[styles.modalLocationBadgeText, { color: palette.accent }]}>
                              {location.short}
                            </Text>
                          </View>
                          <View style={styles.modalLocationCopy}>
                            <Text style={[styles.modalLocationName, { color: palette.text }]}>
                              {location.label}
                            </Text>
                            <Text style={[styles.modalLocationMeta, { color: palette.mutedText }]}>
                              {location.floors?.length
                                ? `${location.floors.length} floor options`
                                : "Single location report"}
                            </Text>
                          </View>
                          <Text style={[styles.modalLocationState, { color: palette.mutedText }]}>
                            {isActive ? "Selected" : "Choose"}
                          </Text>
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                ))}
              </ScrollView>
            </View>
          </View>
        </Modal>
      </SafeAreaView>
    </AppBackground>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 18,
    paddingTop: 54,
    paddingBottom: 32,
    gap: 14,
  },
  heroCard: {
    borderRadius: 24,
    padding: 20,
    shadowColor: "#000",
    shadowOpacity: 0.08,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 10,
    elevation: 3,
  },
  heroEyebrow: {
    fontSize: 12,
    fontWeight: "700",
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
  statRow: {
    flexDirection: "row",
    gap: 10,
    marginTop: 18,
  },
  statPill: {
    flex: 1,
    borderRadius: 16,
    paddingVertical: 12,
    paddingHorizontal: 10,
    alignItems: "center",
  },
  statValue: {
    fontSize: 18,
    fontWeight: "800",
  },
  statLabel: {
    fontSize: 11,
    marginTop: 2,
  },
  feedbackCard: {
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
  },
  feedbackTitle: {
    fontSize: 15,
    fontWeight: "700",
    marginBottom: 4,
  },
  feedbackMessage: {
    fontSize: 13,
    lineHeight: 20,
  },
  sectionCard: {
    borderRadius: 22,
    padding: 18,
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 8,
    elevation: 2,
  },
  sectionStep: {
    fontSize: 12,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 0.6,
    marginBottom: 6,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "800",
    marginBottom: 6,
  },
  sectionDescription: {
    fontSize: 13,
    lineHeight: 19,
    marginBottom: 14,
  },
  locationButton: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  locationButtonText: {
    flex: 1,
    paddingRight: 12,
  },
  locationButtonLabel: {
    fontSize: 16,
    fontWeight: "700",
    marginBottom: 4,
  },
  locationButtonHint: {
    fontSize: 12,
  },
  locationBadge: {
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 8,
    minWidth: 58,
    alignItems: "center",
  },
  locationBadgeText: {
    fontSize: 12,
    fontWeight: "800",
  },
  floorWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 14,
  },
  floorChip: {
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 9,
  },
  floorChipText: {
    fontSize: 13,
    fontWeight: "700",
  },
  choiceList: {
    gap: 10,
  },
  choiceCard: {
    borderRadius: 18,
    borderWidth: 1,
    padding: 14,
    flexDirection: "row",
    alignItems: "center",
  },
  choiceDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  choiceCopy: {
    flex: 1,
  },
  choiceTitle: {
    fontSize: 15,
    fontWeight: "700",
    marginBottom: 4,
  },
  choiceDescription: {
    fontSize: 12,
    lineHeight: 18,
  },
  choiceShortLabel: {
    fontSize: 12,
    fontWeight: "700",
    marginLeft: 10,
  },
  summaryCard: {
    borderRadius: 22,
    padding: 18,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 8,
    elevation: 2,
  },
  summaryRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 12,
    marginTop: 10,
  },
  summaryKey: {
    fontSize: 12,
    textTransform: "uppercase",
    letterSpacing: 0.4,
  },
  summaryValue: {
    flex: 1,
    textAlign: "right",
    fontSize: 14,
    fontWeight: "700",
  },
  summaryHint: {
    marginTop: 14,
    fontSize: 12,
    lineHeight: 18,
  },
  submitButton: {
    minHeight: 56,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 18,
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: "800",
  },
  modalOverlay: {
    flex: 1,
    justifyContent: "flex-end",
    backgroundColor: "rgba(0, 0, 0, 0.32)",
  },
  modalSheet: {
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingTop: 12,
    paddingHorizontal: 18,
    paddingBottom: 24,
    minHeight: "70%",
    maxHeight: "88%",
  },
  sheetHandle: {
    alignSelf: "center",
    width: 48,
    height: 5,
    borderRadius: 999,
    marginBottom: 14,
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: "800",
    marginBottom: 4,
  },
  modalSubtitle: {
    fontSize: 13,
    lineHeight: 19,
    marginBottom: 14,
  },
  modalScroll: {
    flex: 1,
  },
  modalScrollContent: {
    paddingBottom: 18,
  },
  modalSection: {
    marginBottom: 18,
  },
  modalSectionTitle: {
    fontSize: 15,
    fontWeight: "800",
    marginBottom: 4,
  },
  modalSectionDescription: {
    fontSize: 12,
    marginBottom: 10,
  },
  modalLocationRow: {
    borderRadius: 18,
    borderWidth: 1,
    padding: 14,
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
  },
  modalLocationBadge: {
    width: 48,
    height: 48,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },
  modalLocationBadgeText: {
    fontSize: 13,
    fontWeight: "800",
  },
  modalLocationCopy: {
    flex: 1,
  },
  modalLocationName: {
    fontSize: 15,
    fontWeight: "700",
    marginBottom: 4,
  },
  modalLocationMeta: {
    fontSize: 12,
  },
  modalLocationState: {
    fontSize: 12,
    fontWeight: "700",
    marginLeft: 8,
  },
});
