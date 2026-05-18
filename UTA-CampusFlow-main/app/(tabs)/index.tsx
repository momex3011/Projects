import { AppBackground } from "@/components/app-background";
import { useAppTheme } from "@/components/app-theme-provider";
import { useRouter } from "expo-router";
import { onAuthStateChanged, signOut } from "firebase/auth";
import {
  collection,
  doc,
  onSnapshot,
  orderBy,
  query,
  where,
} from "firebase/firestore";
import React, { useEffect, useState } from "react";
import {
  Animated,
  Dimensions,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  TouchableWithoutFeedback,
  View,
} from "react-native";
import { UTA } from "../../constants/theme";
import { auth, db } from "../../firebase/firebase";

const { width, height } = Dimensions.get("window");

function getGymCapacity(): number {
  const hour = new Date().getHours();
  const peak: Record<number, number> = {
    6: 15,
    7: 25,
    8: 35,
    9: 40,
    10: 45,
    11: 50,
    12: 65,
    13: 55,
    14: 45,
    15: 50,
    16: 70,
    17: 85,
    18: 95,
    19: 80,
    20: 55,
    21: 35,
    22: 15,
  };
  return peak[hour] ?? 20;
}

function getNextBus(): { route: string; mins: number; color: string } {
  const buses = [
    { route: "Blue Route", mins: 4, color: "#1E90FF" },
    { route: "Orange Route", mins: 7, color: UTA.blazeOrange },
    { route: "Express Route", mins: 12, color: "#FF5733" },
  ];
  return buses[Math.floor(Date.now() / 60000) % buses.length];
}

function getDiningStatus(): { name: string; open: boolean } {
  const hour = new Date().getHours();
  return { name: "Connection Cafe", open: hour >= 7 && hour <= 22 };
}

function estimateCampusActivity(): string {
  const hour = new Date().getHours();
  const day = new Date().getDay();

  if (day === 0 || day === 6) return "Low";
  if ((hour >= 10 && hour <= 14) || (hour >= 16 && hour <= 18)) return "High";
  if ((hour >= 8 && hour < 10) || (hour > 14 && hour < 16) || (hour > 18 && hour <= 20)) {
    return "Moderate";
  }
  return "Low";
}

export default function HomeScreen() {
  const router = useRouter();
  const { palette } = useAppTheme();
  const [user, setUser] = useState<any>(null);
  const [authReady, setAuthReady] = useState(false);
  const [mavPoints, setMavPoints] = useState(0);
  const [menuVisible, setMenuVisible] = useState(false);
  const [slideAnim] = useState(new Animated.Value(-280));
  const [currentTime, setCurrentTime] = useState(new Date());
  const [campusActivity, setCampusActivity] = useState<string>("Low");

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 30000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (nextUser) => {
      setUser(nextUser);
      setAuthReady(true);
    });
    return unsubscribe;
  }, []);

  useEffect(() => {
    if (!user || user.isAnonymous) {
      setMavPoints(0);
      return;
    }

    const userRef = doc(db, "users", user.uid);
    const unsubscribe = onSnapshot(
      userRef,
      (snapshot) => {
        if (snapshot.exists()) {
          setMavPoints(snapshot.data().points || 0);
        }
      },
      () => {
        setMavPoints(0);
      }
    );

    return unsubscribe;
  }, [user]);

  useEffect(() => {
    if (!authReady) return;
    if (!user || user.isAnonymous) {
      setCampusActivity(estimateCampusActivity());
      return;
    }

    const oneHourAgo = new Date();
    oneHourAgo.setHours(oneHourAgo.getHours() - 1);

    const reportQuery = query(
      collection(db, "campusReports"),
      where("createdAt", ">=", oneHourAgo),
      orderBy("createdAt", "desc")
    );

    const unsubscribe = onSnapshot(
      reportQuery,
      (snapshot) => {
        const count = snapshot.size;
        if (count >= 10) setCampusActivity("High");
        else if (count >= 4) setCampusActivity("Moderate");
        else setCampusActivity("Low");
      },
      () => {
        setCampusActivity(estimateCampusActivity());
      }
    );

    return unsubscribe;
  }, [authReady, user]);

  const openMenu = () => {
    setMenuVisible(true);
    Animated.timing(slideAnim, {
      toValue: 0,
      duration: 250,
      useNativeDriver: false,
    }).start();
  };

  const closeMenu = () => {
    Animated.timing(slideAnim, {
      toValue: -280,
      duration: 250,
      useNativeDriver: false,
    }).start(() => setMenuVisible(false));
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
      closeMenu();
      router.replace("/AuthScreen");
    } catch (error) {
      console.error(error);
    }
  };

  const isGuest = user?.isAnonymous;
  const bus = getNextBus();
  const gym = getGymCapacity();
  const dining = getDiningStatus();
  const activityColor =
    campusActivity === "High"
      ? UTA.red
      : campusActivity === "Moderate"
        ? UTA.yellow
        : UTA.green;

  const timeStr = currentTime.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
  const dateStr = currentTime.toLocaleDateString([], {
    weekday: "long",
    month: "short",
    day: "numeric",
  });

  return (
    <AppBackground>
      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <TouchableOpacity
            onPress={openMenu}
            style={[styles.profileBtn, { backgroundColor: palette.accent }]}>
            <Image
              source={{ uri: "https://img.icons8.com/ios-filled/50/FFFFFF/user-male-circle.png" }}
              style={styles.profileIcon}
            />
          </TouchableOpacity>

          <View style={styles.headerCenter}>
            <Text style={[styles.headerTime, { color: palette.text }]}>{timeStr}</Text>
            <Text style={[styles.headerDate, { color: palette.mutedText }]}>{dateStr}</Text>
          </View>

          {!isGuest && user && (
            <View style={[styles.pointsBadge, { backgroundColor: palette.accentStrong }]}>
              <Text style={styles.pointsEmoji}>💰</Text>
              <Text style={styles.pointsText}>{mavPoints}</Text>
            </View>
          )}
        </View>

        <Text style={[styles.welcomeText, { color: palette.mutedText }]}>
          {isGuest ? "Welcome, Guest" : "Welcome, Maverick"}
        </Text>
        <Text style={[styles.appTitle, { color: palette.accent }]}>UTA CampusFlow</Text>

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.widgetsRow}
          style={styles.widgetsScroll}>
          <TouchableOpacity
            style={[styles.widget, { borderTopColor: bus.color, backgroundColor: palette.surface }]}
            onPress={() => router.push("/bus-tracker")}>
            <Text style={styles.widgetIcon}>🚌</Text>
            <Text style={[styles.widgetTitle, { color: palette.mutedText }]}>{bus.route}</Text>
            <Text style={[styles.widgetValue, { color: bus.color }]}>{bus.mins} min</Text>
            <Text style={[styles.widgetLabel, { color: palette.mutedText }]}>Next arrival</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.widget,
              {
                borderTopColor: gym > 75 ? UTA.red : gym > 50 ? UTA.yellow : UTA.green,
                backgroundColor: palette.surface,
              },
            ]}
            onPress={() => router.push("/fitness-center")}>
            <Text style={styles.widgetIcon}>💪</Text>
            <Text style={[styles.widgetTitle, { color: palette.mutedText }]}>MAC Gym</Text>
            <View style={styles.ringContainer}>
              <View style={[styles.ringBg, { backgroundColor: palette.border }]}>
                <View
                  style={[
                    styles.ringFill,
                    {
                      width: `${gym}%`,
                      backgroundColor: gym > 75 ? UTA.red : gym > 50 ? UTA.yellow : UTA.green,
                    },
                  ]}
                />
              </View>
              <Text style={[styles.ringText, { color: palette.text }]}>{gym}%</Text>
            </View>
            <Text style={[styles.widgetLabel, { color: palette.mutedText }]}>Capacity</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.widget,
              {
                borderTopColor: dining.open ? UTA.green : UTA.red,
                backgroundColor: palette.surface,
              },
            ]}
            onPress={() => router.push("/dining-availability")}>
            <Text style={styles.widgetIcon}>🍽️</Text>
            <Text style={[styles.widgetTitle, { color: palette.mutedText }]}>{dining.name}</Text>
            <View style={styles.statusRow}>
              <View
                style={[
                  styles.statusDot,
                  { backgroundColor: dining.open ? UTA.green : UTA.red },
                ]}
              />
              <Text style={[styles.widgetValue, { color: dining.open ? UTA.green : UTA.red }]}>
                {dining.open ? "OPEN" : "CLOSED"}
              </Text>
            </View>
            <Text style={[styles.widgetLabel, { color: palette.mutedText }]}>Right now</Text>
          </TouchableOpacity>

          <View
            style={[
              styles.widget,
              { borderTopColor: activityColor, backgroundColor: palette.surface },
            ]}>
            <Text style={styles.widgetIcon}>📊</Text>
            <Text style={[styles.widgetTitle, { color: palette.mutedText }]}>Campus</Text>
            <Text style={[styles.widgetValue, { color: activityColor }]}>{campusActivity}</Text>
            <Text style={[styles.widgetLabel, { color: palette.mutedText }]}>Activity</Text>
          </View>
        </ScrollView>

        <Text style={[styles.sectionLabel, { color: palette.text }]}>Quick Actions</Text>
        <View style={styles.actionsGrid}>
          <TouchableOpacity
            style={[styles.actionCard, { backgroundColor: palette.surface }]}
            onPress={() => router.push("/(tabs)/map")}>
            <Text style={styles.actionIcon}>🗺️</Text>
            <Text style={[styles.actionText, { color: palette.text }]}>Heat Map</Text>
            <Text style={[styles.actionSub, { color: palette.mutedText }]}>Live crowd data</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionCard, { backgroundColor: palette.surface }]}
            onPress={() => router.push("/leaderboard")}>
            <Text style={styles.actionIcon}>📈</Text>
            <Text style={[styles.actionText, { color: palette.text }]}>Leaderboard</Text>
            <Text style={[styles.actionSub, { color: palette.mutedText }]}>Top contributors</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionCard, { backgroundColor: palette.surface }]}
            onPress={() => router.push("/library")}>
            <Text style={styles.actionIcon}>📚</Text>
            <Text style={[styles.actionText, { color: palette.text }]}>Library</Text>
            <Text style={[styles.actionSub, { color: palette.mutedText }]}>Floors & noise</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionCard, { backgroundColor: palette.surface }]}
            onPress={() => router.push("/dining-availability")}>
            <Text style={styles.actionIcon}>🍔</Text>
            <Text style={[styles.actionText, { color: palette.text }]}>Dining</Text>
            <Text style={[styles.actionSub, { color: palette.mutedText }]}>What&apos;s open</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionCard, { backgroundColor: palette.surface }]}
            onPress={() => router.push("/fitness-center")}>
            <Text style={styles.actionIcon}>🏋️</Text>
            <Text style={[styles.actionText, { color: palette.text }]}>MAC Gym</Text>
            <Text style={[styles.actionSub, { color: palette.mutedText }]}>Zone tracking</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionCard, { backgroundColor: palette.surface }]}
            onPress={() => router.push("/bus-tracker")}>
            <Text style={styles.actionIcon}>🚌</Text>
            <Text style={[styles.actionText, { color: palette.text }]}>Bus</Text>
            <Text style={[styles.actionSub, { color: palette.mutedText }]}>Route tracker</Text>
          </TouchableOpacity>
        </View>

        {isGuest && (
          <View
            style={[
              styles.guestBanner,
              { backgroundColor: palette.surfaceAlt, borderLeftColor: palette.accent },
            ]}>
            <Text style={[styles.guestText, { color: palette.text }]}>
              Sign in with your @mavs.uta.edu email to report data and earn MavPoints!
            </Text>
          </View>
        )}
      </ScrollView>

      {menuVisible && (
        <TouchableWithoutFeedback onPress={closeMenu}>
          <View style={[styles.overlay, { backgroundColor: palette.overlay }]}>
            <TouchableWithoutFeedback>
              <Animated.View
                style={[
                  styles.sideMenu,
                  {
                    left: slideAnim,
                    backgroundColor: palette.surface,
                  },
                ]}>
                <View style={styles.menuHeader}>
                  <Text style={styles.menuAvatar}>👤</Text>
                  <Text style={[styles.menuEmail, { color: palette.mutedText }]} numberOfLines={1}>
                    {user?.email || "Guest"}
                  </Text>
                  {!isGuest && (
                    <View style={[styles.menuPointsBadge, { backgroundColor: palette.accentStrong }]}>
                      <Text style={styles.menuPointsText}>💰 {mavPoints} pts</Text>
                    </View>
                  )}
                </View>

                <View style={[styles.menuDivider, { backgroundColor: palette.border }]} />

                <TouchableOpacity
                  style={styles.menuItem}
                  onPress={() => {
                    closeMenu();
                    router.push("/(tabs)/survey");
                  }}>
                  <Text style={[styles.menuItemText, { color: palette.text }]}>📝 Submit Report</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.menuItem}
                  onPress={() => {
                    closeMenu();
                    router.push("/(tabs)/map");
                  }}>
                  <Text style={[styles.menuItemText, { color: palette.text }]}>🗺️ Heat Map</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.menuItem}
                  onPress={() => {
                    closeMenu();
                    router.push("/leaderboard");
                  }}>
                  <Text style={[styles.menuItemText, { color: palette.text }]}>Leaderboard</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.menuItem}
                  onPress={() => {
                    closeMenu();
                    router.push("/fitness-center");
                  }}>
                  <Text style={[styles.menuItemText, { color: palette.text }]}>💪 MAC Gym</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.menuItem}
                  onPress={() => {
                    closeMenu();
                    router.push("/library");
                  }}>
                  <Text style={[styles.menuItemText, { color: palette.text }]}>📚 Library</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.menuItem}
                  onPress={() => {
                    closeMenu();
                    router.push("/(tabs)/shop");
                  }}>
                  <Text style={[styles.menuItemText, { color: palette.text }]}>🎨 Theme Shop</Text>
                </TouchableOpacity>

                <View style={[styles.menuDivider, { backgroundColor: palette.border }]} />

                <TouchableOpacity
                  style={[styles.menuLogout, { backgroundColor: palette.surfaceAlt }]}
                  onPress={handleLogout}>
                  <Text style={[styles.menuLogoutText, { color: palette.accentStrong }]}>Logout</Text>
                </TouchableOpacity>
              </Animated.View>
            </TouchableWithoutFeedback>
          </View>
        </TouchableWithoutFeedback>
      )}
    </AppBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 18,
    paddingTop: 54,
    paddingBottom: 30,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 14,
  },
  profileBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: "center",
    alignItems: "center",
  },
  profileIcon: { width: 30, height: 30, borderRadius: 15 },
  headerCenter: { alignItems: "center", flex: 1 },
  headerTime: { fontSize: 22, fontWeight: "bold" },
  headerDate: { fontSize: 12 },
  pointsBadge: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  pointsEmoji: { fontSize: 14, marginRight: 4 },
  pointsText: { color: "#FFFFFF", fontWeight: "bold", fontSize: 15 },
  welcomeText: { fontSize: 14, marginTop: 4 },
  appTitle: { fontSize: 26, fontWeight: "bold", marginBottom: 16 },
  widgetsScroll: { marginBottom: 20 },
  widgetsRow: { paddingRight: 8, gap: 12 },
  widget: {
    width: 150,
    borderRadius: 14,
    padding: 14,
    borderTopWidth: 4,
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 6,
    elevation: 2,
  },
  widgetIcon: { fontSize: 22, marginBottom: 6 },
  widgetTitle: { fontSize: 13, fontWeight: "600", marginBottom: 4 },
  widgetValue: { fontSize: 20, fontWeight: "bold" },
  widgetLabel: { fontSize: 11, marginTop: 2 },
  statusRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  statusDot: { width: 8, height: 8, borderRadius: 4 },
  ringContainer: { marginVertical: 4 },
  ringBg: { height: 8, borderRadius: 4, overflow: "hidden" },
  ringFill: { height: 8, borderRadius: 4 },
  ringText: { fontSize: 18, fontWeight: "bold", marginTop: 2 },
  sectionLabel: { fontSize: 16, fontWeight: "bold", marginBottom: 10 },
  actionsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginBottom: 16,
  },
  actionCard: {
    width: (width - 56) / 3,
    borderRadius: 14,
    padding: 14,
    alignItems: "center",
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowOffset: { width: 0, height: 1 },
    shadowRadius: 4,
    elevation: 1,
  },
  actionDisabled: { opacity: 0.45 },
  actionIcon: { fontSize: 26, marginBottom: 6 },
  actionText: { fontSize: 13, fontWeight: "bold" },
  actionSub: { fontSize: 10, marginTop: 2, textAlign: "center" },
  guestBanner: {
    borderRadius: 10,
    padding: 14,
    borderLeftWidth: 4,
    marginTop: 4,
  },
  guestText: { fontSize: 13, lineHeight: 18 },
  overlay: {
    position: "absolute",
    top: 0,
    left: 0,
    width,
    height,
    zIndex: 100,
  },
  sideMenu: {
    position: "absolute",
    top: 0,
    width: 280,
    height: "100%",
    paddingTop: 60,
    paddingHorizontal: 20,
    shadowColor: "#000",
    shadowOpacity: 0.15,
    shadowOffset: { width: 4, height: 0 },
    shadowRadius: 12,
    elevation: 10,
  },
  menuHeader: { alignItems: "center", marginBottom: 16 },
  menuAvatar: { fontSize: 48, marginBottom: 8 },
  menuEmail: { fontSize: 14, marginBottom: 6 },
  menuPointsBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 14,
  },
  menuPointsText: { color: "#FFFFFF", fontWeight: "bold", fontSize: 13 },
  menuDivider: { height: 1, marginVertical: 12 },
  menuItem: { paddingVertical: 12 },
  menuItemText: { fontSize: 16, fontWeight: "500" },
  menuLogout: {
    paddingVertical: 12,
    marginTop: 8,
    borderRadius: 8,
    alignItems: "center",
  },
  menuLogoutText: { fontSize: 16, fontWeight: "bold" },
});
