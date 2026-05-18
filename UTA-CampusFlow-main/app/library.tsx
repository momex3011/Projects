// app/library.tsx — Central Library floor-by-floor noise & crowd tracker
import { useRouter } from "expo-router";
import { onAuthStateChanged } from "firebase/auth";
import {
    addDoc,
    collection,
    doc,
    getDoc,
    onSnapshot,
    orderBy,
    query,
    serverTimestamp,
    setDoc,
    updateDoc,
    where,
} from "firebase/firestore";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
    Alert,
    Modal,
    ScrollView,
    StyleSheet,
    Text,
    TouchableOpacity,
    View,
} from "react-native";
import { UTA } from "../constants/theme";
import { auth, db } from "../firebase/firebase";

// ── Floor definitions ──
const floors = [
  {
    id: 1,
    label: "1st Floor",
    zones: [
      { id: "1-computers", name: "Computer Lab", icon: "💻", type: "collaborative" },
      { id: "1-circulation", name: "Circulation Desk", icon: "📖", type: "moderate" },
      { id: "1-group-study", name: "Group Study Area", icon: "👥", type: "collaborative" },
      { id: "1-cafe", name: "Starbucks Café", icon: "☕", type: "social" },
    ],
    description: "Main entrance, computers, café, group study",
  },
  {
    id: 2,
    label: "2nd Floor",
    zones: [
      { id: "2-reference", name: "Reference Section", icon: "📚", type: "quiet" },
      { id: "2-study-tables", name: "Open Study Tables", icon: "📝", type: "moderate" },
      { id: "2-media", name: "Media Center", icon: "🎧", type: "moderate" },
      { id: "2-tutoring", name: "Tutoring Center", icon: "🎓", type: "collaborative" },
    ],
    description: "Reference, media center, tutoring hub",
  },
  {
    id: 3,
    label: "3rd Floor",
    zones: [
      { id: "3-study-rooms", name: "Study Rooms A-F", icon: "🚪", type: "bookable" },
      { id: "3-collaboration", name: "Collaboration Space", icon: "🤝", type: "collaborative" },
      { id: "3-printing", name: "Print Station", icon: "🖨️", type: "moderate" },
      { id: "3-lounge", name: "Student Lounge", icon: "🛋️", type: "social" },
    ],
    description: "Reservable study rooms, collaboration areas",
  },
  {
    id: 4,
    label: "4th Floor",
    zones: [
      { id: "4-silent-study", name: "Silent Study Hall", icon: "🤫", type: "silent" },
      { id: "4-special-collections", name: "Special Collections", icon: "🏛️", type: "quiet" },
      { id: "4-individual-desks", name: "Individual Desks", icon: "🪑", type: "quiet" },
    ],
    description: "Silent study, special collections, individual desks",
  },
  {
    id: 5,
    label: "5th Floor",
    zones: [
      { id: "5-archives", name: "Archives & Records", icon: "📜", type: "quiet" },
      { id: "5-grad-study", name: "Graduate Study Area", icon: "🎓", type: "silent" },
      { id: "5-carrels", name: "Study Carrels", icon: "📕", type: "silent" },
    ],
    description: "Archives, graduate-only quiet study",
  },
  {
    id: 6,
    label: "6th Floor",
    zones: [
      { id: "6-sky-lounge", name: "Sky Lounge", icon: "🌤️", type: "moderate" },
      { id: "6-individual-pods", name: "Individual Study Pods", icon: "🔇", type: "silent" },
      { id: "6-window-desks", name: "Window Study Desks", icon: "🪟", type: "quiet" },
    ],
    description: "Top floor — sky lounge, solo study pods",
  },
];

// ── Study rooms (Floor 3) ──
const studyRooms = [
  { id: "room-a", name: "Room A", capacity: 4 },
  { id: "room-b", name: "Room B", capacity: 6 },
  { id: "room-c", name: "Room C", capacity: 4 },
  { id: "room-d", name: "Room D", capacity: 8 },
  { id: "room-e", name: "Room E", capacity: 4 },
  { id: "room-f", name: "Room F", capacity: 6 },
];

// ── Operating hours ──
const operatingHours = [
  { day: "Mon–Thu", hours: "7:00 AM – 12:00 AM" },
  { day: "Fri", hours: "7:00 AM – 9:00 PM" },
  { day: "Sat", hours: "9:00 AM – 6:00 PM" },
  { day: "Sun", hours: "12:00 PM – 12:00 AM" },
];

// ── Types ──
type NoiseLevel = "silent" | "quiet" | "moderate" | "loud";
type OccupancyLevel = "empty" | "low" | "moderate" | "busy" | "full";
type RoomStatus = "available" | "occupied" | "reserved";

interface FloorData {
  noise: NoiseLevel;
  occupancy: OccupancyLevel;
  reportCount: number;
}

interface RoomData {
  status: RoomStatus;
  until?: string;
}

const noiseLevels: { key: NoiseLevel; label: string; icon: string; color: string }[] = [
  { key: "silent", label: "Silent", icon: "🤫", color: UTA.green },
  { key: "quiet", label: "Quiet", icon: "📖", color: "#3B82F6" },
  { key: "moderate", label: "Moderate", icon: "🗣️", color: UTA.yellow },
  { key: "loud", label: "Loud", icon: "📢", color: UTA.red },
];

const occupancyLevels: { key: OccupancyLevel; label: string; pct: number; color: string }[] = [
  { key: "empty", label: "Empty", pct: 5, color: UTA.green },
  { key: "low", label: "Low", pct: 25, color: "#3B82F6" },
  { key: "moderate", label: "Moderate", pct: 55, color: UTA.yellow },
  { key: "busy", label: "Busy", pct: 80, color: UTA.orange },
  { key: "full", label: "Full", pct: 98, color: UTA.red },
];

function noiseColor(n: NoiseLevel): string {
  return noiseLevels.find((l) => l.key === n)?.color ?? UTA.gray400;
}
function noiseLabel(n: NoiseLevel): string {
  return noiseLevels.find((l) => l.key === n)?.label ?? "Unknown";
}
function noiseIcon(n: NoiseLevel): string {
  return noiseLevels.find((l) => l.key === n)?.icon ?? "❓";
}
function occupancyColor(o: OccupancyLevel): string {
  return occupancyLevels.find((l) => l.key === o)?.color ?? UTA.gray400;
}
function occupancyPct(o: OccupancyLevel): number {
  return occupancyLevels.find((l) => l.key === o)?.pct ?? 0;
}

function roomStatusColor(s: RoomStatus): string {
  switch (s) {
    case "available": return UTA.green;
    case "occupied": return UTA.red;
    case "reserved": return UTA.yellow;
  }
}

// Time-based estimates
function estimateNoise(floorId: number): NoiseLevel {
  const hour = new Date().getHours();
  const day = new Date().getDay();
  if (day === 0 || day === 6) return floorId >= 4 ? "silent" : "quiet";
  if (hour >= 11 && hour <= 15) {
    if (floorId <= 2) return "moderate";
    if (floorId === 3) return "moderate";
    return "quiet";
  }
  if (hour >= 17 && hour <= 22) {
    if (floorId <= 2) return "loud";
    if (floorId === 3) return "moderate";
    return "quiet";
  }
  return floorId >= 4 ? "silent" : "quiet";
}
function estimateOccupancy(floorId: number): OccupancyLevel {
  const hour = new Date().getHours();
  const day = new Date().getDay();
  if (day === 0 || day === 6) return "low";
  if (hour >= 10 && hour <= 14) return floorId <= 3 ? "busy" : "moderate";
  if (hour >= 17 && hour <= 22) return floorId <= 3 ? "busy" : "moderate";
  return "low";
}

// Estimate study room status based on time
function estimateRoomStatus(): RoomStatus {
  const hour = new Date().getHours();
  const day = new Date().getDay();
  if (day === 0 || day === 6) return "available";
  if (hour >= 10 && hour <= 20) return Math.random() > 0.4 ? "occupied" : "available";
  return "available";
}

function normalizeNoise(raw: string): NoiseLevel {
  const s = raw.toLowerCase();
  if (s.includes("silent")) return "silent";
  if (s.includes("quiet")) return "quiet";
  if (s.includes("loud")) return "loud";
  return "moderate";
}
function normalizeOccupancy(raw: string): OccupancyLevel {
  const s = raw.toLowerCase();
  if (s.includes("empty")) return "empty";
  if (s.includes("full")) return "full";
  if (s.includes("busy")) return "busy";
  if (s.includes("low")) return "low";
  return "moderate";
}

export default function LibraryScreen() {
  const router = useRouter();
  const [user, setUser] = useState(auth.currentUser);
  const [authReady, setAuthReady] = useState(false);
  const isGuest = user?.isAnonymous;

  const [selectedFloor, setSelectedFloor] = useState(1);
  const [floorData, setFloorData] = useState<Record<number, FloorData>>({});
  const [roomStatuses, setRoomStatuses] = useState<Record<string, RoomData>>({});
  const [showHours, setShowHours] = useState(false);

  // Report modal
  const [reportVisible, setReportVisible] = useState(false);
  const [reportFloor, setReportFloor] = useState(1);
  const [reportNoise, setReportNoise] = useState<NoiseLevel | "">("");
  const [reportOccupancy, setReportOccupancy] = useState<OccupancyLevel | "">("");
  const [reportStep, setReportStep] = useState(0); // 0=noise, 1=occupancy
  const [cooldownMins, setCooldownMins] = useState(0);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (nextUser) => {
      setUser(nextUser);
      setAuthReady(true);
    });

    return unsubscribe;
  }, []);

  // Initialize estimates
  useEffect(() => {
    const estimated: Record<number, FloorData> = {};
    for (const f of floors) {
      estimated[f.id] = {
        noise: estimateNoise(f.id),
        occupancy: estimateOccupancy(f.id),
        reportCount: 0,
      };
    }
    setFloorData(estimated);

    // Initialize room statuses
    const rooms: Record<string, RoomData> = {};
    for (const r of studyRooms) {
      rooms[r.id] = { status: estimateRoomStatus() };
    }
    setRoomStatuses(rooms);
  }, []);

  // Listen for library reports from Firestore
  useEffect(() => {
    if (!authReady) return;
    if (!user || user.isAnonymous) return;

    const twoHoursAgo = new Date();
    twoHoursAgo.setHours(twoHoursAgo.getHours() - 2);
    const q = query(
      collection(db, "libraryReports"),
      where("createdAt", ">=", twoHoursAgo),
      orderBy("createdAt", "desc")
    );
    const unsub = onSnapshot(
      q,
      (snapshot) => {
        const byFloor: Record<number, { noises: string[]; occupancies: string[] }> = {};
        snapshot.forEach((d) => {
          const data = d.data();
          const fid = data.floor as number;
          if (!byFloor[fid]) byFloor[fid] = { noises: [], occupancies: [] };
          if (data.noiseLevel) byFloor[fid].noises.push(data.noiseLevel);
          if (data.occupancyLevel) byFloor[fid].occupancies.push(data.occupancyLevel);
        });
        setFloorData((prev) => {
          const updated = { ...prev };
          for (const f of floors) {
            if (byFloor[f.id] && byFloor[f.id].noises.length > 0) {
              const noises = byFloor[f.id].noises.map(normalizeNoise);
              const occupancies = byFloor[f.id].occupancies.map(normalizeOccupancy);
              // Most common noise
              const noiseCounts: Record<string, number> = {};
              noises.forEach((n) => (noiseCounts[n] = (noiseCounts[n] || 0) + 1));
              const topNoise = Object.entries(noiseCounts).sort((a, b) => b[1] - a[1])[0][0] as NoiseLevel;
              // Most common occupancy
              const occCounts: Record<string, number> = {};
              occupancies.forEach((o) => (occCounts[o] = (occCounts[o] || 0) + 1));
              const topOcc = Object.entries(occCounts).sort((a, b) => b[1] - a[1])[0][0] as OccupancyLevel;

              updated[f.id] = {
                noise: topNoise,
                occupancy: topOcc,
                reportCount: byFloor[f.id].noises.length,
              };
            } else if (!updated[f.id]) {
              updated[f.id] = {
                noise: estimateNoise(f.id),
                occupancy: estimateOccupancy(f.id),
                reportCount: 0,
              };
            }
          }
          return updated;
        });
      },
      () => {
        // Keep the estimate-based view when guest access or rules block reads.
      }
    );
    return unsub;
  }, [authReady, user]);

  // Listen for study room updates
  useEffect(() => {
    if (!authReady) return;
    if (!user || user.isAnonymous) return;

    const unsub = onSnapshot(
      collection(db, "libraryRooms"),
      (snapshot) => {
        setRoomStatuses((prev) => {
          const updated = { ...prev };
          snapshot.forEach((d) => {
            const data = d.data();
            if (data.roomId && data.status) {
              updated[data.roomId] = {
                status: data.status as RoomStatus,
                until: data.until || undefined,
              };
            }
          });
          return updated;
        });
      },
      () => {
        // Keep estimate-based room states when live reads are unavailable.
      }
    );
    return unsub;
  }, [authReady, user]);

  // Cooldown check
  useEffect(() => {
    if (!authReady) return;
    if (!user || isGuest) return;
    const check = async () => {
      try {
        const snap = await getDoc(doc(db, "users", user.uid));
        if (snap.exists()) {
          const last = snap.data().lastLibraryReportTime?.toDate();
          if (last) {
            const diff = 30 * 60 * 1000 - (Date.now() - last.getTime());
            setCooldownMins(diff > 0 ? Math.ceil(diff / 60000) : 0);
          }
        }
      } catch { /* ignore */ }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, [authReady, isGuest, user]);

  const currentFloor = useMemo(() => floors.find((f) => f.id === selectedFloor)!, [selectedFloor]);
  const currentData = floorData[selectedFloor];

  // Check if library is open now
  const isLibraryOpen = useMemo(() => {
    const now = new Date();
    const hour = now.getHours();
    const day = now.getDay();
    if (day === 6) return hour >= 9 && hour < 18; // Sat
    if (day === 0) return hour >= 12 || hour === 0; // Sun 12pm-midnight
    if (day === 5) return hour >= 7 && hour < 21; // Fri
    return hour >= 7 || hour === 0; // Mon-Thu 7am-midnight
  }, []);

  // Submit report
  const submitReport = useCallback(async () => {
    if (!user || isGuest) {
      Alert.alert("Sign In Required", "Only registered users can submit reports.");
      return;
    }
    if (cooldownMins > 0) {
      Alert.alert("Cooldown Active", `Please wait ${cooldownMins} minutes before reporting again.`);
      return;
    }
    if (!reportNoise || !reportOccupancy) return;
    try {
      const userRef = doc(db, "users", user.uid);
      const userSnap = await getDoc(userRef);
      if (!userSnap.exists()) await setDoc(userRef, { points: 0 });

      await addDoc(collection(db, "libraryReports"), {
        floor: reportFloor,
        noiseLevel: reportNoise,
        occupancyLevel: reportOccupancy,
        createdAt: serverTimestamp(),
        userId: user.uid,
      });
      const pts = userSnap.exists() ? (userSnap.data().points || 0) : 0;
      await updateDoc(userRef, { lastLibraryReportTime: serverTimestamp(), points: pts + 10 });

      Alert.alert("Report Submitted! 📚", "You earned 10 MavPoints. Thanks for helping fellow Mavs!");
      setReportVisible(false);
      setReportStep(0);
      setReportNoise("");
      setReportOccupancy("");
      setCooldownMins(30);
    } catch (err) {
      console.error(err);
      Alert.alert("Error", "Failed to submit report.");
    }
  }, [user, isGuest, cooldownMins, reportFloor, reportNoise, reportOccupancy]);

  // Available rooms count
  const availableRoomCount = useMemo(
    () => Object.values(roomStatuses).filter((r) => r.status === "available").length,
    [roomStatuses]
  );

  return (
    <View style={s.root}>
      <ScrollView contentContainerStyle={s.container} showsVerticalScrollIndicator={false}>
        {/* Back + Title */}
        <TouchableOpacity onPress={() => router.back()} style={s.backBtn}>
          <Text style={s.backText}>← Back</Text>
        </TouchableOpacity>

        <Text style={s.title}>📚 Central Library</Text>
        <Text style={s.subtitle}>Floor-by-floor noise & occupancy tracker</Text>

        {/* Open/Closed Banner */}
        <View style={[s.statusBanner, { backgroundColor: isLibraryOpen ? UTA.green + "15" : UTA.red + "15", borderLeftColor: isLibraryOpen ? UTA.green : UTA.red }]}>
          <View style={s.statusBannerRow}>
            <View style={[s.statusDot, { backgroundColor: isLibraryOpen ? UTA.green : UTA.red }]} />
            <Text style={[s.statusBannerText, { color: isLibraryOpen ? UTA.green : UTA.red }]}>
              {isLibraryOpen ? "Library is OPEN" : "Library is CLOSED"}
            </Text>
          </View>
          <TouchableOpacity onPress={() => setShowHours(!showHours)}>
            <Text style={s.hoursToggle}>{showHours ? "Hide Hours ▲" : "View Hours ▼"}</Text>
          </TouchableOpacity>
        </View>

        {/* Hours (collapsible) */}
        {showHours && (
          <View style={s.hoursCard}>
            {operatingHours.map((h) => (
              <View key={h.day} style={s.hoursRow}>
                <Text style={s.hoursDay}>{h.day}</Text>
                <Text style={s.hoursTime}>{h.hours}</Text>
              </View>
            ))}
          </View>
        )}

        {/* ── Floor Selector ── */}
        <Text style={s.sectionTitle}>Select Floor</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.floorSelector}>
          {floors.map((f) => {
            const fd = floorData[f.id];
            const nc = fd ? noiseColor(fd.noise) : UTA.gray400;
            const isActive = selectedFloor === f.id;
            return (
              <TouchableOpacity
                key={f.id}
                style={[s.floorChip, isActive && s.floorChipActive]}
                onPress={() => setSelectedFloor(f.id)}
              >
                <View style={[s.floorDot, { backgroundColor: nc }]} />
                <Text style={[s.floorChipText, isActive && s.floorChipTextActive]}>F{f.id}</Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {/* ── Floor Overview Card ── */}
        {currentData && (
          <View style={s.floorCard}>
            <Text style={s.floorCardTitle}>{currentFloor.label}</Text>
            <Text style={s.floorCardDesc}>{currentFloor.description}</Text>

            <View style={s.floorStats}>
              {/* Noise */}
              <View style={s.statBox}>
                <Text style={s.statIcon}>{noiseIcon(currentData.noise)}</Text>
                <Text style={[s.statValue, { color: noiseColor(currentData.noise) }]}>
                  {noiseLabel(currentData.noise)}
                </Text>
                <Text style={s.statLabel}>Noise Level</Text>
              </View>
              {/* Occupancy */}
              <View style={s.statBox}>
                <Text style={s.statIcon}>👥</Text>
                <Text style={[s.statValue, { color: occupancyColor(currentData.occupancy) }]}>
                  {currentData.occupancy.charAt(0).toUpperCase() + currentData.occupancy.slice(1)}
                </Text>
                <Text style={s.statLabel}>Occupancy</Text>
              </View>
              {/* Reports */}
              <View style={s.statBox}>
                <Text style={s.statIcon}>📊</Text>
                <Text style={s.statValue}>{currentData.reportCount}</Text>
                <Text style={s.statLabel}>Reports (2h)</Text>
              </View>
            </View>

            {/* Occupancy Bar */}
            <View style={s.occBarSection}>
              <Text style={s.occBarLabel}>Occupancy</Text>
              <View style={s.occBarBg}>
                <View
                  style={[
                    s.occBarFill,
                    {
                      width: `${occupancyPct(currentData.occupancy)}%`,
                      backgroundColor: occupancyColor(currentData.occupancy),
                    },
                  ]}
                />
              </View>
              <Text style={[s.occBarPct, { color: occupancyColor(currentData.occupancy) }]}>
                ~{occupancyPct(currentData.occupancy)}%
              </Text>
            </View>

            {currentData.reportCount === 0 && (
              <Text style={s.estimateNote}>
                ⏱ Showing time-based estimate — be the first to report!
              </Text>
            )}
          </View>
        )}

        {/* ── Zone Details ── */}
        <Text style={s.sectionTitle}>Zones on {currentFloor.label}</Text>
        {currentFloor.zones.map((zone) => {
          const typeColors: Record<string, string> = {
            silent: UTA.green,
            quiet: "#3B82F6",
            moderate: UTA.yellow,
            collaborative: UTA.blazeOrange,
            social: UTA.orange,
            bookable: UTA.royalBlue,
          };
          const tc = typeColors[zone.type] ?? UTA.gray400;
          return (
            <View key={zone.id} style={s.zoneCard}>
              <View style={s.zoneRow}>
                <Text style={s.zoneIcon}>{zone.icon}</Text>
                <View style={s.zoneInfo}>
                  <Text style={s.zoneName}>{zone.name}</Text>
                  <View style={[s.zoneTypeBadge, { backgroundColor: tc + "18" }]}>
                    <Text style={[s.zoneTypeText, { color: tc }]}>
                      {zone.type.charAt(0).toUpperCase() + zone.type.slice(1)}
                    </Text>
                  </View>
                </View>
              </View>
            </View>
          );
        })}

        {/* ── Study Rooms (Floor 3) ── */}
        {selectedFloor === 3 && (
          <>
            <Text style={s.sectionTitle}>🚪 Study Rooms</Text>
            <Text style={s.roomSummary}>
              {availableRoomCount} of {studyRooms.length} rooms available
            </Text>
            <View style={s.roomGrid}>
              {studyRooms.map((room) => {
                const rd = roomStatuses[room.id] || { status: "available" as RoomStatus };
                const sc = roomStatusColor(rd.status);
                return (
                  <View key={room.id} style={[s.roomCard, { borderLeftColor: sc }]}>
                    <View style={s.roomHeader}>
                      <Text style={s.roomName}>{room.name}</Text>
                      <View style={[s.roomStatusBadge, { backgroundColor: sc + "18" }]}>
                        <View style={[s.roomStatusDot, { backgroundColor: sc }]} />
                        <Text style={[s.roomStatusText, { color: sc }]}>
                          {rd.status.charAt(0).toUpperCase() + rd.status.slice(1)}
                        </Text>
                      </View>
                    </View>
                    <Text style={s.roomCapacity}>Seats {room.capacity}</Text>
                    {rd.until && <Text style={s.roomUntil}>Until {rd.until}</Text>}
                  </View>
                );
              })}
            </View>
          </>
        )}

        {/* ── All Floors Summary ── */}
        <Text style={s.sectionTitle}>📊 All Floors at a Glance</Text>
        <View style={s.summaryTable}>
          <View style={s.summaryHeaderRow}>
            <Text style={[s.summaryCell, s.summaryHeaderText, { flex: 0.6 }]}>Floor</Text>
            <Text style={[s.summaryCell, s.summaryHeaderText]}>Noise</Text>
            <Text style={[s.summaryCell, s.summaryHeaderText]}>Occupancy</Text>
            <Text style={[s.summaryCell, s.summaryHeaderText, { flex: 0.5 }]}>Reports</Text>
          </View>
          {floors.map((f) => {
            const fd = floorData[f.id];
            if (!fd) return null;
            return (
              <TouchableOpacity
                key={f.id}
                style={[s.summaryRow, selectedFloor === f.id && s.summaryRowActive]}
                onPress={() => setSelectedFloor(f.id)}
              >
                <Text style={[s.summaryCell, { flex: 0.6, fontWeight: "600" }]}>F{f.id}</Text>
                <View style={[s.summaryCell, { flexDirection: "row", alignItems: "center", gap: 4 }]}>
                  <View style={[s.miniDot, { backgroundColor: noiseColor(fd.noise) }]} />
                  <Text style={s.summaryCellText}>{noiseLabel(fd.noise)}</Text>
                </View>
                <View style={[s.summaryCell, { flexDirection: "row", alignItems: "center", gap: 4 }]}>
                  <View style={[s.miniDot, { backgroundColor: occupancyColor(fd.occupancy) }]} />
                  <Text style={s.summaryCellText}>
                    {fd.occupancy.charAt(0).toUpperCase() + fd.occupancy.slice(1)}
                  </Text>
                </View>
                <Text style={[s.summaryCell, { flex: 0.5, textAlign: "center" }]}>{fd.reportCount}</Text>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* ── Tips ── */}
        <View style={s.tipsCard}>
          <Text style={s.tipsTitle}>💡 Library Tips</Text>
          <Text style={s.tipItem}>• Floors 4–6 are quietest for deep focus study</Text>
          <Text style={s.tipItem}>• Floor 3 study rooms can be reserved online</Text>
          <Text style={s.tipItem}>• Floor 1 Starbucks closes at 8 PM weekdays</Text>
          <Text style={s.tipItem}>• Weekday evenings (5–10 PM) are busiest</Text>
          <Text style={s.tipItem}>• Report conditions to help other Mavericks!</Text>
        </View>

        {/* Cooldown */}
        {cooldownMins > 0 && (
          <View style={s.cooldownBanner}>
            <Text style={s.cooldownText}>⏳ Report cooldown: {cooldownMins} min remaining</Text>
          </View>
        )}

        {/* Guest note */}
        {isGuest && (
          <View style={s.guestBanner}>
            <Text style={s.guestText}>
              🔒 Sign in with your @mavs.uta.edu email to report library conditions and earn MavPoints!
            </Text>
          </View>
        )}
      </ScrollView>

      {/* ── FAB ── */}
      <TouchableOpacity
        style={s.fab}
        onPress={() => {
          if (!user || isGuest) {
            Alert.alert("Sign In Required", "Only registered users can submit reports.");
            return;
          }
          if (cooldownMins > 0) {
            Alert.alert("Cooldown Active", `Wait ${cooldownMins} more minutes.`);
            return;
          }
          setReportFloor(selectedFloor);
          setReportNoise("");
          setReportOccupancy("");
          setReportStep(0);
          setReportVisible(true);
        }}
        activeOpacity={0.8}
      >
        <Text style={s.fabIcon}>+</Text>
      </TouchableOpacity>

      {/* ── Report Modal ── */}
      <Modal visible={reportVisible} animationType="slide" transparent>
        <View style={s.modalOverlay}>
          <View style={s.modalContent}>
            {/* Stepper */}
            <View style={s.stepper}>
              {["Noise", "Occupancy"].map((label, i) => (
                <View key={label} style={s.stepItem}>
                  <View style={[s.stepCircle, reportStep >= i && s.stepCircleActive]}>
                    <Text style={[s.stepNum, reportStep >= i && s.stepNumActive]}>{i + 1}</Text>
                  </View>
                  <Text style={[s.stepLabel, reportStep >= i && s.stepLabelActive]}>{label}</Text>
                </View>
              ))}
            </View>

            <Text style={s.modalFloorLabel}>Reporting for: {floors.find((f) => f.id === reportFloor)?.label}</Text>

            {/* Floor quick-change */}
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.modalFloorRow}>
              {floors.map((f) => (
                <TouchableOpacity
                  key={f.id}
                  style={[s.modalFloorChip, reportFloor === f.id && s.modalFloorChipActive]}
                  onPress={() => setReportFloor(f.id)}
                >
                  <Text style={[s.modalFloorChipText, reportFloor === f.id && s.modalFloorChipTextActive]}>
                    F{f.id}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            {/* Step 0: Noise */}
            {reportStep === 0 && (
              <View>
                <Text style={s.modalTitle}>How noisy is Floor {reportFloor}?</Text>
                {noiseLevels.map((nl) => (
                  <TouchableOpacity
                    key={nl.key}
                    style={[s.optionBtn, reportNoise === nl.key && { backgroundColor: nl.color }]}
                    onPress={() => {
                      setReportNoise(nl.key);
                      setReportStep(1);
                    }}
                  >
                    <Text style={[s.optionText, reportNoise === nl.key && s.optionTextActive]}>
                      {nl.icon} {nl.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}

            {/* Step 1: Occupancy */}
            {reportStep === 1 && (
              <View>
                <Text style={s.modalTitle}>How full is Floor {reportFloor}?</Text>
                {occupancyLevels.map((ol) => (
                  <TouchableOpacity
                    key={ol.key}
                    style={[s.optionBtn, reportOccupancy === ol.key && { backgroundColor: ol.color }]}
                    onPress={() => setReportOccupancy(ol.key)}
                  >
                    <Text style={[s.optionText, reportOccupancy === ol.key && s.optionTextActive]}>
                      {ol.label} (~{ol.pct}%)
                    </Text>
                  </TouchableOpacity>
                ))}
                {reportOccupancy !== "" && (
                  <TouchableOpacity style={s.submitBtn} onPress={submitReport}>
                    <Text style={s.submitBtnText}>Submit Report</Text>
                  </TouchableOpacity>
                )}
                <TouchableOpacity style={s.backStepBtn} onPress={() => setReportStep(0)}>
                  <Text style={s.backStepText}>← Back to Noise</Text>
                </TouchableOpacity>
              </View>
            )}

            <TouchableOpacity style={s.closeBtn} onPress={() => setReportVisible(false)}>
              <Text style={s.closeBtnText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: UTA.offWhite },
  container: { padding: 16, paddingTop: 48, paddingBottom: 100 },

  backBtn: { marginBottom: 8 },
  backText: { fontSize: 16, color: UTA.royalBlue, fontWeight: "bold" },
  title: { fontSize: 24, fontWeight: "bold", textAlign: "center", color: UTA.royalBlue },
  subtitle: { fontSize: 13, color: UTA.gray500, textAlign: "center", marginBottom: 14 },

  // Open/Closed Banner
  statusBanner: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    borderRadius: 12, padding: 14, borderLeftWidth: 4, marginBottom: 14,
  },
  statusBannerRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  statusDot: { width: 10, height: 10, borderRadius: 5 },
  statusBannerText: { fontSize: 15, fontWeight: "bold" },
  hoursToggle: { fontSize: 12, color: UTA.royalBlue, fontWeight: "600" },

  // Hours
  hoursCard: {
    backgroundColor: "#fff", borderRadius: 12, padding: 14, marginBottom: 14,
    shadowColor: "#000", shadowOpacity: 0.04, shadowOffset: { width: 0, height: 1 }, shadowRadius: 3, elevation: 1,
  },
  hoursRow: { flexDirection: "row", justifyContent: "space-between", marginBottom: 6 },
  hoursDay: { fontSize: 14, fontWeight: "600", color: UTA.gray800 },
  hoursTime: { fontSize: 14, color: UTA.gray500 },

  // Floor selector
  sectionTitle: { fontSize: 17, fontWeight: "bold", color: UTA.gray800, marginBottom: 10, marginTop: 8 },
  floorSelector: { gap: 10, paddingBottom: 12 },
  floorChip: {
    width: 56, height: 56, borderRadius: 28, backgroundColor: "#fff",
    justifyContent: "center", alignItems: "center",
    shadowColor: "#000", shadowOpacity: 0.06, shadowOffset: { width: 0, height: 1 }, shadowRadius: 3, elevation: 1,
  },
  floorChipActive: { backgroundColor: UTA.royalBlue },
  floorDot: { width: 8, height: 8, borderRadius: 4, marginBottom: 3 },
  floorChipText: { fontSize: 14, fontWeight: "bold", color: UTA.gray600 },
  floorChipTextActive: { color: "#fff" },

  // Floor overview card
  floorCard: {
    backgroundColor: "#fff", borderRadius: 14, padding: 18, marginBottom: 14,
    shadowColor: "#000", shadowOpacity: 0.06, shadowOffset: { width: 0, height: 2 }, shadowRadius: 4, elevation: 2,
  },
  floorCardTitle: { fontSize: 20, fontWeight: "bold", color: UTA.royalBlue, marginBottom: 4 },
  floorCardDesc: { fontSize: 13, color: UTA.gray500, marginBottom: 14 },
  floorStats: { flexDirection: "row", justifyContent: "space-around", marginBottom: 14 },
  statBox: { alignItems: "center" },
  statIcon: { fontSize: 22, marginBottom: 4 },
  statValue: { fontSize: 16, fontWeight: "bold", color: UTA.gray800 },
  statLabel: { fontSize: 11, color: UTA.gray400, marginTop: 2 },

  // Occupancy bar
  occBarSection: { marginTop: 4 },
  occBarLabel: { fontSize: 12, fontWeight: "600", color: UTA.gray500, marginBottom: 4 },
  occBarBg: { height: 10, backgroundColor: UTA.gray200, borderRadius: 5, overflow: "hidden" },
  occBarFill: { height: 10, borderRadius: 5 },
  occBarPct: { fontSize: 12, fontWeight: "bold", marginTop: 3, textAlign: "right" },
  estimateNote: { fontSize: 11, color: UTA.gray400, fontStyle: "italic", marginTop: 8 },

  // Zone cards
  zoneCard: {
    backgroundColor: "#fff", borderRadius: 12, padding: 14, marginBottom: 8,
    shadowColor: "#000", shadowOpacity: 0.03, shadowOffset: { width: 0, height: 1 }, shadowRadius: 2, elevation: 1,
  },
  zoneRow: { flexDirection: "row", alignItems: "center" },
  zoneIcon: { fontSize: 26, marginRight: 12 },
  zoneInfo: { flex: 1 },
  zoneName: { fontSize: 15, fontWeight: "600", color: UTA.gray800, marginBottom: 3 },
  zoneTypeBadge: { alignSelf: "flex-start", paddingHorizontal: 10, paddingVertical: 3, borderRadius: 10 },
  zoneTypeText: { fontSize: 11, fontWeight: "600" },

  // Study Rooms
  roomSummary: { fontSize: 13, color: UTA.gray500, marginBottom: 10, marginTop: -4 },
  roomGrid: { gap: 8, marginBottom: 8 },
  roomCard: {
    backgroundColor: "#fff", borderRadius: 12, padding: 14, borderLeftWidth: 4,
    shadowColor: "#000", shadowOpacity: 0.04, shadowOffset: { width: 0, height: 1 }, shadowRadius: 3, elevation: 1,
  },
  roomHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 4 },
  roomName: { fontSize: 15, fontWeight: "bold", color: UTA.gray800 },
  roomStatusBadge: { flexDirection: "row", alignItems: "center", paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12, gap: 5 },
  roomStatusDot: { width: 8, height: 8, borderRadius: 4 },
  roomStatusText: { fontSize: 12, fontWeight: "600" },
  roomCapacity: { fontSize: 12, color: UTA.gray500 },
  roomUntil: { fontSize: 11, color: UTA.gray400, fontStyle: "italic", marginTop: 2 },

  // Summary table
  summaryTable: {
    backgroundColor: "#fff", borderRadius: 12, overflow: "hidden", marginBottom: 14,
    shadowColor: "#000", shadowOpacity: 0.04, shadowOffset: { width: 0, height: 1 }, shadowRadius: 3, elevation: 1,
  },
  summaryHeaderRow: {
    flexDirection: "row", backgroundColor: UTA.royalBlue + "0D", paddingVertical: 10, paddingHorizontal: 12,
  },
  summaryHeaderText: { fontWeight: "bold", fontSize: 12, color: UTA.gray600 },
  summaryRow: { flexDirection: "row", paddingVertical: 10, paddingHorizontal: 12, borderTopWidth: 1, borderTopColor: UTA.gray100 },
  summaryRowActive: { backgroundColor: UTA.lightBlue },
  summaryCell: { flex: 1 },
  summaryCellText: { fontSize: 12, color: UTA.gray600 },
  miniDot: { width: 8, height: 8, borderRadius: 4 },

  // Tips
  tipsCard: {
    backgroundColor: UTA.lightBlue, borderRadius: 12, padding: 16, marginBottom: 14,
    borderLeftWidth: 4, borderLeftColor: UTA.royalBlue,
  },
  tipsTitle: { fontSize: 15, fontWeight: "bold", color: UTA.royalBlue, marginBottom: 8 },
  tipItem: { fontSize: 13, color: UTA.gray600, marginBottom: 4, lineHeight: 18 },

  // Cooldown + Guest
  cooldownBanner: {
    backgroundColor: UTA.blazeOrange + "18", borderRadius: 10,
    padding: 12, borderLeftWidth: 4, borderLeftColor: UTA.blazeOrange, marginBottom: 14,
  },
  cooldownText: { fontSize: 13, color: UTA.blazeOrange, fontWeight: "600" },
  guestBanner: {
    backgroundColor: UTA.lightBlue, borderRadius: 10, padding: 14,
    borderLeftWidth: 4, borderLeftColor: UTA.royalBlue,
  },
  guestText: { fontSize: 13, color: UTA.royalBlue, lineHeight: 18 },

  // FAB
  fab: {
    position: "absolute", bottom: 28, right: 20,
    width: 60, height: 60, borderRadius: 30,
    backgroundColor: UTA.blazeOrange, justifyContent: "center", alignItems: "center",
    shadowColor: UTA.blazeOrange, shadowOpacity: 0.4, shadowOffset: { width: 0, height: 4 },
    shadowRadius: 10, elevation: 6,
  },
  fabIcon: { fontSize: 32, color: "#fff", fontWeight: "bold", marginTop: -2 },

  // Modal
  modalOverlay: { flex: 1, backgroundColor: "rgba(0,0,0,0.5)", justifyContent: "flex-end" },
  modalContent: {
    backgroundColor: "#fff", borderTopLeftRadius: 24, borderTopRightRadius: 24,
    padding: 24, paddingBottom: 40, maxHeight: "80%",
  },
  stepper: { flexDirection: "row", justifyContent: "center", gap: 32, marginBottom: 16 },
  stepItem: { alignItems: "center" },
  stepCircle: {
    width: 32, height: 32, borderRadius: 16, backgroundColor: UTA.gray200,
    justifyContent: "center", alignItems: "center", marginBottom: 4,
  },
  stepCircleActive: { backgroundColor: UTA.royalBlue },
  stepNum: { fontSize: 14, fontWeight: "bold", color: UTA.gray400 },
  stepNumActive: { color: "#fff" },
  stepLabel: { fontSize: 11, color: UTA.gray400 },
  stepLabelActive: { color: UTA.royalBlue, fontWeight: "600" },

  modalFloorLabel: { fontSize: 14, fontWeight: "600", color: UTA.gray600, marginBottom: 8 },
  modalFloorRow: { gap: 8, marginBottom: 16 },
  modalFloorChip: {
    width: 42, height: 42, borderRadius: 21, backgroundColor: UTA.gray100,
    justifyContent: "center", alignItems: "center",
  },
  modalFloorChipActive: { backgroundColor: UTA.royalBlue },
  modalFloorChipText: { fontSize: 13, fontWeight: "bold", color: UTA.gray600 },
  modalFloorChipTextActive: { color: "#fff" },

  modalTitle: { fontSize: 18, fontWeight: "bold", color: UTA.gray800, marginBottom: 12 },
  optionBtn: {
    paddingVertical: 14, paddingHorizontal: 16, backgroundColor: UTA.gray100,
    borderRadius: 12, marginBottom: 8,
  },
  optionText: { fontSize: 15, color: UTA.gray800, fontWeight: "500" },
  optionTextActive: { color: "#fff" },

  submitBtn: {
    marginTop: 14, backgroundColor: UTA.blazeOrange, borderRadius: 12,
    paddingVertical: 14, alignItems: "center",
    shadowColor: UTA.blazeOrange, shadowOpacity: 0.3, shadowOffset: { width: 0, height: 3 },
    shadowRadius: 6, elevation: 3,
  },
  submitBtnText: { color: "#fff", fontSize: 16, fontWeight: "bold" },
  backStepBtn: { marginTop: 10, paddingVertical: 6 },
  backStepText: { color: UTA.royalBlue, fontSize: 14, fontWeight: "600" },
  closeBtn: { marginTop: 14, alignItems: "center", paddingVertical: 8 },
  closeBtnText: { color: UTA.gray400, fontSize: 14, fontWeight: "600" },
});
