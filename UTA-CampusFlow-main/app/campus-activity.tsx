import { AppBackground } from "@/components/app-background";
import { useAppTheme } from "@/components/app-theme-provider";
import { useRouter } from "expo-router";
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

export default function CampusActivityScreen() {
  const router = useRouter();
  const { palette } = useAppTheme();

  return (
    <AppBackground>
      <View style={styles.container}>
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Text style={[styles.backText, { color: palette.accent }]}>Back</Text>
        </TouchableOpacity>

        <View style={[styles.card, { backgroundColor: palette.surface, borderColor: palette.border }]}>
          <Text style={[styles.title, { color: palette.text }]}>Campus Activity</Text>
          <Text style={[styles.subtitle, { color: palette.mutedText }]}>
            This space can host broader trends later, like busiest times, popular reporting zones,
            and weekly crowd patterns.
          </Text>
          <View style={[styles.badge, { backgroundColor: palette.surfaceAlt }]}>
            <Text style={[styles.badgeText, { color: palette.text }]}>Ready for future gamification stats</Text>
          </View>
        </View>
      </View>
    </AppBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    paddingTop: 56,
  },
  backBtn: {
    marginBottom: 16,
  },
  backText: {
    fontSize: 16,
    fontWeight: "700",
  },
  card: {
    borderRadius: 20,
    borderWidth: 1,
    padding: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: "800",
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 16,
  },
  badge: {
    alignSelf: "flex-start",
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  badgeText: {
    fontSize: 13,
    fontWeight: "700",
  },
});
