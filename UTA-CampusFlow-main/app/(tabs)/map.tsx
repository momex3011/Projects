import { AppBackground } from "@/components/app-background";
import { useAppTheme } from "@/components/app-theme-provider";
import {
  CAMPUS_SURVEY_LOCATIONS,
  CAMPUS_SURVEY_REPORT_WINDOW_HOURS,
  type CampusLocationType,
  type CrowdLevelId,
  getCrowdOptionById,
} from "@/constants/campus-survey";
import {
  aggregateCampusReports,
  normalizeCampusReport,
  type AggregatedReportSummary,
} from "@/firebase/campus-surveys";
import { auth, db } from "@/firebase/firebase";
import {
  collection,
  onSnapshot,
  orderBy,
  query,
  where,
} from "firebase/firestore";
import { onAuthStateChanged } from "firebase/auth";
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Animated,
  Easing,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import MapView, { Circle, Marker, PROVIDER_GOOGLE } from "react-native-maps";
import { UTA } from "../../constants/theme";

type FilterKey = "all" | CampusLocationType;
type CrowdLevel = "unknown" | CrowdLevelId;

function crowdToColor(level: CrowdLevel): string {
  switch (level) {
    case "low":
      return UTA.green;
    case "medium":
      return UTA.yellow;
    case "high":
      return UTA.red;
    default:
      return UTA.gray200;
  }
}

function crowdToOpacity(level: CrowdLevel): number {
  switch (level) {
    case "low":
      return 0.55;
    case "medium":
      return 0.72;
    case "high":
      return 0.9;
    default:
      return 0.26;
  }
}

function crowdShortLabel(level: CrowdLevel): string {
  if (level === "unknown") return "No Data";
  return getCrowdOptionById(level).shortLabel;
}

function crowdLongLabel(level: CrowdLevel): string {
  if (level === "unknown") return "No recent reports";
  return getCrowdOptionById(level).label;
}

function toAlphaColor(color: string, alphaHex: string) {
  if (/^#[0-9a-fA-F]{6}$/.test(color)) {
    return `${color}${alphaHex}`;
  }
  return color;
}

function timeBasedEstimate(): CrowdLevelId {
  const hour = new Date().getHours();
  const day = new Date().getDay();
  if (day === 0 || day === 6) return "low";
  if (hour >= 10 && hour <= 14) return "high";
  if ((hour >= 8 && hour < 10) || (hour > 14 && hour <= 18)) return "medium";
  return "low";
}

function PulsingDot({ color }: { color: string }) {
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 4,
          duration: 900,
          easing: Easing.out(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 900,
          easing: Easing.in(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, [pulseAnim]);

  return (
    <View style={styles.pulseWrapper}>
      <Animated.View
        style={[
          styles.pulseRing,
          { backgroundColor: `${color}40`, transform: [{ scale: pulseAnim }] },
        ]}
      />
      <View style={[styles.pulseDot, { backgroundColor: color }]} />
    </View>
  );
}

export default function MapScreen() {
  const { palette } = useAppTheme();
  const [user, setUser] = useState(auth.currentUser);
  const [authReady, setAuthReady] = useState(false);
  const [crowdMap, setCrowdMap] = useState<
    Record<string, { overall: AggregatedReportSummary; floors?: Partial<Record<number, AggregatedReportSummary>> }>
  >({});
  const [selectedLocationId, setSelectedLocationId] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterKey>("all");
  const [libraryFloor, setLibraryFloor] = useState(1);
  const [showHeatmap, setShowHeatmap] = useState(false);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (nextUser) => {
      setUser(nextUser);
      setAuthReady(true);
    });

    return unsubscribe;
  }, []);

  useEffect(() => {
    if (!authReady) return;
    if (!user || user.isAnonymous) {
      setCrowdMap({});
      return;
    }

    const lookback = new Date();
    lookback.setHours(lookback.getHours() - CAMPUS_SURVEY_REPORT_WINDOW_HOURS);

    const reportQuery = query(
      collection(db, "campusReports"),
      where("createdAt", ">=", lookback),
      orderBy("createdAt", "desc")
    );

    const unsubscribe = onSnapshot(
      reportQuery,
      (snapshot) => {
        const reports = snapshot.docs
          .map((docSnap) => normalizeCampusReport(docSnap.data() as Record<string, unknown>))
          .filter((report): report is NonNullable<typeof report> => report !== null);

        setCrowdMap(aggregateCampusReports(reports));
      },
      () => {
        setCrowdMap({});
      }
    );

    return unsubscribe;
  }, [authReady, user]);

  const filteredLocations = useMemo(() => {
    if (filter === "all") return CAMPUS_SURVEY_LOCATIONS;
    return CAMPUS_SURVEY_LOCATIONS.filter((location) => location.type === filter);
  }, [filter]);

  const rows = useMemo(() => {
    const grouped: Record<number, typeof CAMPUS_SURVEY_LOCATIONS> = {};

    for (const location of filteredLocations) {
      if (!grouped[location.row]) grouped[location.row] = [];
      grouped[location.row].push(location);
    }

    return Object.entries(grouped)
      .sort(([a], [b]) => Number(a) - Number(b))
      .map(([, locations]) => locations.sort((a, b) => a.col - b.col));
  }, [filteredLocations]);

  const selectedLocation = selectedLocationId
    ? CAMPUS_SURVEY_LOCATIONS.find((location) => location.id === selectedLocationId) ?? null
    : null;
  const selectedAggregate = selectedLocationId ? crowdMap[selectedLocationId] : null;
  const selectedSummary = selectedLocation
    ? selectedLocation.floors?.length
      ? selectedAggregate?.floors?.[libraryFloor] ?? selectedAggregate?.overall ?? null
      : selectedAggregate?.overall ?? null
    : null;
  const usingFloorSpecificData = Boolean(
    selectedLocation?.floors?.length && selectedAggregate?.floors?.[libraryFloor]
  );

  return (
    <AppBackground>
      <SafeAreaView style={styles.safeArea}>
        <ScrollView
          contentContainerStyle={styles.container}
          showsVerticalScrollIndicator={false}>
          <Text style={[styles.title, { color: palette.text }]}>Campus Heat Map</Text>
          <Text style={[styles.subtitle, { color: palette.mutedText }]}>
            Recent reports are combined into one live campus view, with newer reports weighted more
            heavily.
            {user?.isAnonymous
              ? " Guest mode shows time-based estimates until you sign in."
              : ""}
          </Text>

          <View style={[styles.legend, { backgroundColor: palette.surface }]}>
            {[
              { color: UTA.gray200, label: "No Data" },
              { color: UTA.green, label: "Plenty of space" },
              { color: UTA.yellow, label: "Getting busy" },
              { color: UTA.red, label: "Packed" },
            ].map((item) => (
              <View key={item.label} style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: item.color }]} />
                <Text style={[styles.legendText, { color: palette.text }]}>{item.label}</Text>
              </View>
            ))}
          </View>

          <View style={styles.filterRow}>
            {(["all", "academic", "student", "dining"] as const).map((key) => (
              <TouchableOpacity
                key={key}
                style={[
                  styles.filterTab,
                  { backgroundColor: palette.surface },
                  filter === key && [styles.filterTabActive, { backgroundColor: palette.accent }],
                ]}
                onPress={() => setFilter(key)}>
                <Text
                  style={[
                    styles.filterText,
                    { color: filter === key ? palette.accentText : palette.text },
                  ]}>
                  {key === "all"
                    ? "All"
                    : key === "academic"
                      ? "Academic"
                      : key === "student"
                        ? "Student"
                        : "Dining"}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <View style={styles.gridContainer}>
            {rows.map((row, rowIndex) => (
              <View key={rowIndex} style={styles.gridRow}>
                {row.map((location) => {
                  const overall = crowdMap[location.id]?.overall;
                  const level = overall?.crowdLevel ?? timeBasedEstimate();
                  const color = crowdToColor(level);
                  const opacity = crowdToOpacity(level);
                  const isSelected = selectedLocationId === location.id;

                  return (
                    <TouchableOpacity
                      key={location.id}
                      style={[
                        styles.gridCell,
                        { backgroundColor: color, opacity },
                        isSelected && [styles.gridCellSelected, { borderColor: palette.accent }],
                      ]}
                      onPress={() => setSelectedLocationId(isSelected ? null : location.id)}
                      activeOpacity={0.7}>
                      {level === "high" && <PulsingDot color={UTA.red} />}
                      <Text style={styles.cellShort}>{location.short}</Text>
                      <Text style={styles.cellLabel}>{crowdShortLabel(level)}</Text>
                      {overall && (
                        <Text style={styles.cellReports}>
                          {overall.reportCount} report{overall.reportCount === 1 ? "" : "s"}
                        </Text>
                      )}
                    </TouchableOpacity>
                  );
                })}
              </View>
            ))}
          </View>

          {selectedLocation && (
            <View style={[styles.detailCard, { backgroundColor: palette.surface }]}>
              <View style={styles.detailHeader}>
                <View>
                  <Text style={[styles.detailTitle, { color: palette.text }]}>
                    {selectedLocation.label}
                  </Text>
                  <Text style={[styles.detailSubtitle, { color: palette.mutedText }]}>
                    Combined from the last {CAMPUS_SURVEY_REPORT_WINDOW_HOURS} hours of reports
                  </Text>
                </View>
                {selectedSummary && (
                  <View
                    style={[
                      styles.confidenceBadge,
                      { backgroundColor: palette.surfaceAlt, borderColor: palette.border },
                    ]}>
                    <Text style={[styles.confidenceBadgeScore, { color: palette.accent }]}>
                      {selectedSummary.confidenceScore}%
                    </Text>
                    <Text style={[styles.confidenceBadgeLabel, { color: palette.mutedText }]}>
                      {selectedSummary.confidenceLabel} confidence
                    </Text>
                  </View>
                )}
              </View>

              <View style={styles.detailRow}>
                <Text style={[styles.detailKey, { color: palette.text }]}>Crowd Level</Text>
                <Text
                  style={[
                    styles.detailValue,
                    { color: crowdToColor(selectedSummary?.crowdLevel ?? timeBasedEstimate()) },
                  ]}>
                  {crowdLongLabel(selectedSummary?.crowdLevel ?? timeBasedEstimate())}
                </Text>
              </View>

              <View style={styles.detailRow}>
                <Text style={[styles.detailKey, { color: palette.text }]}>Noise Level</Text>
                <Text style={[styles.detailValue, { color: palette.text }]}>
                  {selectedSummary?.noiseLabel ?? "No recent reports"}
                </Text>
              </View>

              <View style={styles.detailRow}>
                <Text style={[styles.detailKey, { color: palette.text }]}>Reports</Text>
                <Text style={[styles.detailValue, { color: palette.text }]}>
                  {selectedSummary?.reportCount ?? 0}
                </Text>
              </View>

              <View style={styles.detailRow}>
                <Text style={[styles.detailKey, { color: palette.text }]}>Updated</Text>
                <Text style={[styles.detailValue, { color: palette.text }]}>
                  {selectedSummary?.updatedMinutesAgo !== null &&
                  selectedSummary?.updatedMinutesAgo !== undefined
                    ? `${selectedSummary.updatedMinutesAgo} min ago`
                    : "Using time estimate"}
                </Text>
              </View>

              {selectedLocation.floors?.length && (
                <View style={styles.floorSection}>
                  <Text style={[styles.floorLabel, { color: palette.text }]}>Library floor</Text>
                  <View style={styles.floorRow}>
                    {selectedLocation.floors.map((floor) => {
                      const isActive = libraryFloor === floor;
                      return (
                        <TouchableOpacity
                          key={floor}
                          style={[
                            styles.floorBtn,
                            { backgroundColor: palette.surfaceAlt },
                            isActive && [
                              styles.floorBtnActive,
                              { backgroundColor: palette.accent },
                            ],
                          ]}
                          onPress={() => setLibraryFloor(floor)}>
                          <Text
                            style={[
                              styles.floorBtnText,
                              { color: isActive ? palette.accentText : palette.text },
                            ]}>
                            {floor}
                          </Text>
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                  <Text style={[styles.floorNote, { color: palette.mutedText }]}>
                    {usingFloorSpecificData
                      ? `Floor ${libraryFloor} is showing floor-specific reports first.`
                      : `Floor ${libraryFloor} has no recent floor-specific reports yet, so the overall library trend is shown.`}
                  </Text>
                </View>
              )}

              {!selectedSummary && (
                <Text style={[styles.detailNote, { color: palette.mutedText }]}>
                  No recent reports yet. This card is showing a time-based estimate until students
                  check in.
                </Text>
              )}
            </View>
          )}

          <TouchableOpacity
            style={[styles.heatmapToggle, { backgroundColor: palette.accent }]}
            onPress={() => setShowHeatmap((value) => !value)}>
            <Text style={styles.heatmapToggleText}>
              {showHeatmap ? "Hide Campus Heatmap" : "View Campus Heatmap"}
            </Text>
          </TouchableOpacity>

          {showHeatmap && (
            <View style={styles.fullMapContainer}>
              <MapView
                provider={PROVIDER_GOOGLE}
                style={{ flex: 1 }}
                initialRegion={{
                  latitude: 32.7303,
                  longitude: -97.114,
                  latitudeDelta: 0.01,
                  longitudeDelta: 0.01,
                }}>
                {CAMPUS_SURVEY_LOCATIONS.map((location) => {
                  const overall = crowdMap[location.id]?.overall;
                  const level = overall?.crowdLevel ?? timeBasedEstimate();
                  const baseColor = crowdToColor(level);
                  const reportBoost = overall ? overall.reportCount * 18 : 0;
                  const confidenceBoost = overall ? overall.confidenceScore * 0.45 : 0;
                  const radius = 55 + reportBoost + confidenceBoost;

                  return (
                    <Circle
                      key={`${location.id}-overlay`}
                      center={location.coordinate}
                      radius={radius}
                      fillColor={toAlphaColor(baseColor, "33")}
                      strokeColor={toAlphaColor(baseColor, "66")}
                      strokeWidth={1.2}
                    />
                  );
                })}

                {CAMPUS_SURVEY_LOCATIONS.map((location) => {
                  const overall = crowdMap[location.id]?.overall;
                  const level = overall?.crowdLevel ?? timeBasedEstimate();
                  return (
                    <Marker
                      key={location.id}
                      coordinate={location.coordinate}
                      title={location.mapTitle ?? location.label}
                      description={
                        overall
                          ? `${crowdLongLabel(level)} • ${overall.reportCount} reports • ${overall.confidenceScore}% confidence`
                          : `${crowdLongLabel(level)} • time-based estimate`
                      }
                      pinColor={crowdToColor(level)}
                    />
                  );
                })}
              </MapView>
            </View>
          )}
        </ScrollView>
      </SafeAreaView>
    </AppBackground>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  container: {
    paddingHorizontal: 20,
    paddingTop: 50,
    paddingBottom: 36,
  },
  title: {
    fontSize: 28,
    fontWeight: "800",
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    marginBottom: 16,
    lineHeight: 20,
  },
  legend: {
    borderRadius: 18,
    paddingVertical: 12,
    paddingHorizontal: 10,
    marginBottom: 16,
  },
  legendItem: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
  },
  legendDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  legendText: {
    fontSize: 12,
  },
  filterRow: {
    flexDirection: "row",
    marginBottom: 16,
    justifyContent: "space-between",
    gap: 8,
  },
  filterTab: {
    flex: 1,
    paddingVertical: 9,
    paddingHorizontal: 10,
    borderRadius: 12,
    alignItems: "center",
  },
  filterTabActive: {},
  filterText: {
    fontSize: 12,
    fontWeight: "700",
  },
  gridContainer: {
    marginBottom: 16,
  },
  gridRow: {
    flexDirection: "row",
    marginBottom: 8,
  },
  gridCell: {
    flex: 1,
    marginHorizontal: 4,
    paddingVertical: 12,
    paddingHorizontal: 6,
    borderRadius: 12,
    alignItems: "center",
    minHeight: 96,
    justifyContent: "center",
  },
  gridCellSelected: {
    borderWidth: 2,
  },
  cellShort: {
    fontWeight: "800",
    fontSize: 14,
  },
  cellLabel: {
    fontSize: 11,
    marginTop: 4,
  },
  cellReports: {
    fontSize: 10,
    color: "#333333",
    marginTop: 4,
  },
  pulseWrapper: {
    position: "absolute",
    top: 8,
    left: 8,
  },
  pulseRing: {
    width: 20,
    height: 20,
    borderRadius: 10,
    position: "absolute",
  },
  pulseDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  detailCard: {
    padding: 16,
    borderRadius: 18,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  detailHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 12,
    marginBottom: 10,
  },
  detailTitle: {
    fontSize: 20,
    fontWeight: "800",
    marginBottom: 4,
  },
  detailSubtitle: {
    fontSize: 12,
  },
  confidenceBadge: {
    minWidth: 104,
    borderRadius: 16,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 10,
    alignItems: "center",
  },
  confidenceBadgeScore: {
    fontSize: 20,
    fontWeight: "800",
  },
  confidenceBadgeLabel: {
    fontSize: 10,
    marginTop: 2,
    textAlign: "center",
  },
  detailRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 8,
    gap: 12,
  },
  detailKey: {
    fontWeight: "700",
    fontSize: 13,
  },
  detailValue: {
    fontWeight: "700",
    fontSize: 13,
    textAlign: "right",
    flex: 1,
  },
  floorSection: {
    marginTop: 14,
  },
  floorLabel: {
    fontSize: 13,
    fontWeight: "700",
    marginBottom: 8,
  },
  floorRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  floorBtn: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
  },
  floorBtnActive: {},
  floorBtnText: {
    fontSize: 12,
    fontWeight: "700",
  },
  floorNote: {
    fontSize: 11,
    marginTop: 8,
    lineHeight: 16,
  },
  detailNote: {
    fontSize: 12,
    marginTop: 12,
    lineHeight: 18,
  },
  heatmapToggle: {
    paddingVertical: 13,
    borderRadius: 14,
    alignItems: "center",
    marginVertical: 12,
  },
  heatmapToggleText: {
    color: "#FFFFFF",
    fontWeight: "800",
  },
  fullMapContainer: {
    height: 400,
    borderRadius: 16,
    overflow: "hidden",
    marginBottom: 16,
  },
});
