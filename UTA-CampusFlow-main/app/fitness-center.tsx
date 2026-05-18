import { useRouter } from "expo-router";
import { onAuthStateChanged } from "firebase/auth";
import {
    addDoc,
    collection,
    onSnapshot,
    orderBy,
    query,
    serverTimestamp,
    where,
} from "firebase/firestore";
import React, { useEffect, useState } from "react";
import {
    Alert,
    ScrollView,
    StyleSheet,
    Text,
    TouchableOpacity,
    View,
} from "react-native";
import { UTA } from "../constants/theme";
import { auth, db } from "../firebase/firebase";

// --- Gym zone definitions for the MAC ---
const gymZones = [
  { id: "weight-room", label: "Weight Room", icon: "🏋️", capacity: 60 },
  { id: "cardio-floor", label: "Cardio Floor", icon: "🏃", capacity: 45 },
  { id: "basketball-courts", label: "Basketball Courts", icon: "🏀", capacity: 30 },
  { id: "racquetball", label: "Racquetball Courts", icon: "🎾", capacity: 8 },
  { id: "indoor-track", label: "Indoor Track", icon: "🏅", capacity: 25 },
  { id: "group-fitness", label: "Group Fitness Studio", icon: "🧘", capacity: 35 },
  { id: "climbing-wall", label: "Climbing Wall", icon: "🧗", capacity: 12 },
  { id: "pool", label: "Swimming Pool", icon: "🏊", capacity: 30 },
];

// Operating hours for MAC
const operatingHours = [
  { day: "Mon-Thu", hours: "6:00 AM – 11:00 PM" },
  { day: "Fri", hours: "6:00 AM – 9:00 PM" },
  { day: "Sat", hours: "8:00 AM – 8:00 PM" },
  { day: "Sun", hours: "12:00 PM – 9:00 PM" },
];

// Typical peak patterns (hour -> busyness multiplier)
const peakPattern: Record<number, number> = {
  6: 0.2, 7: 0.3, 8: 0.4, 9: 0.45, 10: 0.5, 11: 0.55,
  12: 0.7, 13: 0.6, 14: 0.5, 15: 0.55,
  16: 0.75, 17: 0.9, 18: 1.0, 19: 0.85, 20: 0.6, 21: 0.4, 22: 0.2,
};

type CrowdLevel = "low" | "moderate" | "high" | "very-high";

interface ZoneReport {
  zoneId: string;
  crowdLevel: CrowdLevel;
  timestamp: any;
  userId: string;
}

function getCrowdColor(level: CrowdLevel): string {
  switch (level) {
    case "low": return UTA.green;
    case "moderate": return UTA.yellow;
    case "high": return UTA.blazeOrange;
    case "very-high": return UTA.red;
    default: return UTA.gray400;
  }
}

function getCrowdLabel(level: CrowdLevel): string {
  switch (level) {
    case "low": return "Low";
    case "moderate": return "Moderate";
    case "high": return "Busy";
    case "very-high": return "Very Busy";
    default: return "Unknown";
  }
}

function getOccupancyPercent(level: CrowdLevel): number {
  switch (level) {
    case "low": return 25;
    case "moderate": return 50;
    case "high": return 75;
    case "very-high": return 95;
    default: return 0;
  }
}

// Estimate current crowd level based on time-of-day pattern
function getEstimatedLevel(hour: number): CrowdLevel {
  const multiplier = peakPattern[hour] ?? 0.3;
  if (multiplier >= 0.85) return "very-high";
  if (multiplier >= 0.6) return "high";
  if (multiplier >= 0.4) return "moderate";
  return "low";
}

export default function FitnessCenterScreen() {
  const router = useRouter();
  const [user, setUser] = useState(auth.currentUser);
  const [authReady, setAuthReady] = useState(false);
  const isGuest = user?.isAnonymous;

  const [zoneLevels, setZoneLevels] = useState<Record<string, CrowdLevel>>({});
  const [selectedZone, setSelectedZone] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("--");

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (nextUser) => {
      setUser(nextUser);
      setAuthReady(true);
    });

    return unsubscribe;
  }, []);

  // Listen for real-time gym reports from last 2 hours
  useEffect(() => {
    if (!authReady) return;
    if (!user || user.isAnonymous) return;

    const twoHoursAgo = new Date();
    twoHoursAgo.setHours(twoHoursAgo.getHours() - 2);

    const q = query(
      collection(db, "gymReports"),
      where("timestamp", ">=", twoHoursAgo),
      orderBy("timestamp", "desc")
    );

    const unsubscribe = onSnapshot(
      q,
      (snapshot) => {
        const latestByZone: Record<string, CrowdLevel> = {};

        snapshot.forEach((doc) => {
          const data = doc.data() as ZoneReport;
          // Keep only the most recent report per zone
          if (!latestByZone[data.zoneId]) {
            latestByZone[data.zoneId] = data.crowdLevel;
          }
        });

        // Fill missing zones with time-based estimates
        const hour = new Date().getHours();
        for (const zone of gymZones) {
          if (!latestByZone[zone.id]) {
            latestByZone[zone.id] = getEstimatedLevel(hour);
          }
        }

        setZoneLevels(latestByZone);
        setLastUpdated(new Date().toLocaleTimeString());
      },
      () => {
        // Keep estimate-based levels when live reads are unavailable.
      }
    );

    return unsubscribe;
  }, [authReady, user]);

  // Initialize with time-based estimates if no Firestore data yet
  useEffect(() => {
    if (Object.keys(zoneLevels).length === 0) {
      const hour = new Date().getHours();
      const estimated: Record<string, CrowdLevel> = {};
      for (const zone of gymZones) {
        estimated[zone.id] = getEstimatedLevel(hour);
      }
      setZoneLevels(estimated);
      setLastUpdated(new Date().toLocaleTimeString());
    }
  }, [zoneLevels]);

  const handleReport = async (zoneId: string, level: CrowdLevel) => {
    if (isGuest || !user) {
      Alert.alert("Sign In Required", "Only registered users can report gym crowd levels.");
      return;
    }

    try {
      await addDoc(collection(db, "gymReports"), {
        zoneId,
        crowdLevel: level,
        timestamp: serverTimestamp(),
        userId: user.uid,
      });
      Alert.alert("Thanks!", "Your gym report has been submitted. 💪");
      setSelectedZone(null);
    } catch (err) {
      console.error("Error submitting gym report:", err);
      Alert.alert("Error", "Could not submit report. Try again later.");
    }
  };

  // Compute overall gym busyness
  const overallLevel = (): CrowdLevel => {
    const levels = Object.values(zoneLevels);
    if (levels.length === 0) return "low";
    const avg = levels.reduce((sum, l) => sum + getOccupancyPercent(l), 0) / levels.length;
    if (avg >= 80) return "very-high";
    if (avg >= 55) return "high";
    if (avg >= 35) return "moderate";
    return "low";
  };

  const overall = overallLevel();

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {/* Back button */}
      <TouchableOpacity style={styles.backButton} onPress={() => router.push("/")}>
        <Text style={styles.backButtonText}>← Back to Home</Text>
      </TouchableOpacity>

      <Text style={styles.title}>MAC Fitness Center</Text>
      <Text style={styles.subtitle}>Maverick Activities Center</Text>

      {/* Overall Status */}
      <View style={[styles.overallCard, { borderLeftColor: getCrowdColor(overall) }]}>
        <Text style={styles.overallLabel}>Current Gym Status</Text>
        <View style={styles.overallRow}>
          <View style={[styles.statusDot, { backgroundColor: getCrowdColor(overall) }]} />
          <Text style={[styles.overallValue, { color: getCrowdColor(overall) }]}>
            {getCrowdLabel(overall)}
          </Text>
        </View>
        <Text style={styles.updatedText}>Last updated: {lastUpdated}</Text>
      </View>

      {/* Operating Hours */}
      <View style={styles.hoursCard}>
        <Text style={styles.sectionTitle}>🕐 Operating Hours</Text>
        {operatingHours.map((h, i) => (
          <View key={i} style={styles.hoursRow}>
            <Text style={styles.hoursDay}>{h.day}</Text>
            <Text style={styles.hoursTime}>{h.hours}</Text>
          </View>
        ))}
      </View>

      {/* Peak Hours Chart */}
      <View style={styles.peakCard}>
        <Text style={styles.sectionTitle}>📊 Typical Peak Hours</Text>
        <View style={styles.chartContainer}>
          {Object.entries(peakPattern).map(([hour, val]) => (
            <View key={hour} style={styles.barWrapper}>
              <View
                style={[
                  styles.bar,
                  {
                    height: val * 80,
                    backgroundColor:
                      val >= 0.85 ? UTA.red : val >= 0.6 ? UTA.blazeOrange : val >= 0.4 ? UTA.yellow : UTA.green,
                  },
                ]}
              />
              <Text style={styles.barLabel}>
                {Number(hour) > 12 ? Number(hour) - 12 + "p" : hour + "a"}
              </Text>
            </View>
          ))}
        </View>
        <View style={styles.peakLegend}>
          <Text style={styles.peakNote}>🟢 Low  🟡 Moderate  🟠 Busy  🔴 Very Busy</Text>
        </View>
      </View>

      {/* Zone-by-Zone Tracking */}
      <Text style={styles.sectionTitle}>🏢 Zone Occupancy</Text>
      <Text style={styles.zoneSubtitle}>Tap a zone to report its crowd level</Text>

      {gymZones.map((zone) => {
        const level = zoneLevels[zone.id] || "low";
        const pct = getOccupancyPercent(level);
        const isSelected = selectedZone === zone.id;

        return (
          <View key={zone.id}>
            <TouchableOpacity
              style={styles.zoneCard}
              onPress={() => setSelectedZone(isSelected ? null : zone.id)}
              activeOpacity={0.7}
            >
              <View style={styles.zoneHeader}>
                <Text style={styles.zoneIcon}>{zone.icon}</Text>
                <View style={styles.zoneInfo}>
                  <Text style={styles.zoneName}>{zone.label}</Text>
                  <Text style={styles.zoneCapacity}>Capacity: {zone.capacity}</Text>
                </View>
                <View style={styles.zoneLevelBadge}>
                  <View style={[styles.statusDotSmall, { backgroundColor: getCrowdColor(level) }]} />
                  <Text style={[styles.zoneLevelText, { color: getCrowdColor(level) }]}>
                    {getCrowdLabel(level)}
                  </Text>
                </View>
              </View>
              {/* Occupancy bar */}
              <View style={styles.occupancyBarBg}>
                <View
                  style={[
                    styles.occupancyBarFill,
                    { width: `${pct}%`, backgroundColor: getCrowdColor(level) },
                  ]}
                />
              </View>
              <Text style={styles.occupancyText}>~{pct}% occupied</Text>
            </TouchableOpacity>

            {/* Report buttons (expanded) */}
            {isSelected && (
              <View style={styles.reportRow}>
                <Text style={styles.reportLabel}>Report crowd level:</Text>
                <View style={styles.reportButtons}>
                  {(["low", "moderate", "high", "very-high"] as CrowdLevel[]).map((lvl) => (
                    <TouchableOpacity
                      key={lvl}
                      style={[styles.reportBtn, { backgroundColor: getCrowdColor(lvl) }]}
                      onPress={() => handleReport(zone.id, lvl)}
                    >
                      <Text style={styles.reportBtnText}>{getCrowdLabel(lvl)}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            )}
          </View>
        );
      })}

      {isGuest && (
        <Text style={styles.guestNote}>
          Sign in with a UTA account to report gym crowd levels and earn MavPoints!
        </Text>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    backgroundColor: UTA.offWhite,
    paddingBottom: 60,
    paddingTop: 48,
  },
  backButton: { marginBottom: 15 },
  backButtonText: { fontSize: 16, color: UTA.royalBlue, fontWeight: "bold" },
  title: { fontSize: 28, fontWeight: "bold", textAlign: "center", color: UTA.royalBlue },
  subtitle: { fontSize: 14, color: UTA.gray500, textAlign: "center", marginBottom: 20 },
  overallCard: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 18,
    marginBottom: 16,
    borderLeftWidth: 5,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 2,
  },
  overallLabel: { fontSize: 14, color: "#666", marginBottom: 6 },
  overallRow: { flexDirection: "row", alignItems: "center", marginBottom: 4 },
  statusDot: { width: 14, height: 14, borderRadius: 7, marginRight: 8 },
  overallValue: { fontSize: 22, fontWeight: "bold" },
  updatedText: { fontSize: 12, color: "#999", marginTop: 4 },
  hoursCard: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 2,
  },
  sectionTitle: { fontSize: 18, fontWeight: "bold", marginBottom: 12 },
  hoursRow: { flexDirection: "row", justifyContent: "space-between", marginBottom: 6 },
  hoursDay: { fontSize: 15, fontWeight: "600", color: "#333" },
  hoursTime: { fontSize: 15, color: "#555" },
  peakCard: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 2,
  },
  chartContainer: {
    flexDirection: "row",
    alignItems: "flex-end",
    justifyContent: "space-around",
    height: 100,
    marginTop: 8,
  },
  barWrapper: { alignItems: "center", flex: 1 },
  bar: { width: 14, borderRadius: 4 },
  barLabel: { fontSize: 9, color: "#888", marginTop: 4 },
  peakLegend: { marginTop: 10, alignItems: "center" },
  peakNote: { fontSize: 12, color: "#666" },
  zoneSubtitle: { fontSize: 13, color: "#888", marginBottom: 12, marginTop: -6 },
  zoneCard: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowOffset: { width: 0, height: 1 },
    shadowRadius: 3,
    elevation: 1,
  },
  zoneHeader: { flexDirection: "row", alignItems: "center", marginBottom: 8 },
  zoneIcon: { fontSize: 28, marginRight: 12 },
  zoneInfo: { flex: 1 },
  zoneName: { fontSize: 16, fontWeight: "bold", color: "#222" },
  zoneCapacity: { fontSize: 12, color: "#999" },
  zoneLevelBadge: { flexDirection: "row", alignItems: "center" },
  statusDotSmall: { width: 10, height: 10, borderRadius: 5, marginRight: 5 },
  zoneLevelText: { fontSize: 14, fontWeight: "600" },
  occupancyBarBg: {
    height: 8,
    backgroundColor: "#e5e7eb",
    borderRadius: 4,
    overflow: "hidden",
  },
  occupancyBarFill: { height: 8, borderRadius: 4 },
  occupancyText: { fontSize: 12, color: "#888", marginTop: 4, textAlign: "right" },
  reportRow: {
    backgroundColor: UTA.royalBlue + '0D',
    borderRadius: 10,
    padding: 12,
    marginBottom: 10,
    marginTop: -6,
  },
  reportLabel: { fontSize: 13, fontWeight: "600", marginBottom: 8, color: "#444" },
  reportButtons: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  reportBtn: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  reportBtnText: { color: "#fff", fontWeight: "bold", fontSize: 13 },
  guestNote: {
    marginTop: 16,
    fontSize: 13,
    color: "#999",
    textAlign: "center",
    fontStyle: "italic",
  },
});
