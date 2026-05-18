import type { CollectibleArtSpec, IdentityKind } from "@/constants/gamification";
import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { StyleSheet, Text, View } from "react-native";

type CollectiblePreviewKind = IdentityKind | "achievement";

type CollectiblePreviewProps = {
  art: CollectibleArtSpec;
  kind: CollectiblePreviewKind;
  label: string;
  size?: number;
};

export function CollectiblePreview({
  art,
  kind,
  label,
  size = 88,
}: CollectiblePreviewProps) {
  const radius = size * 0.34;
  const iconSize = kind === "title" ? size * 0.24 : size * 0.3;
  const bannerWidth = kind === "title" ? size * 0.78 : size * 0.72;

  return (
    <View style={[styles.wrap, { width: size, height: size + 10 }]}>
      <LinearGradient
        colors={art.gradientColors}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[styles.shell, { width: size, height: size, borderRadius: radius }]}>
        <View
          style={[
            styles.rim,
            {
              borderColor: `${art.rimColor}88`,
              borderRadius: radius - 4,
            },
          ]}
        />
        <View
          style={[
            styles.sparkle,
            {
              backgroundColor: `${art.sparkleColor}CC`,
              top: size * 0.16,
              right: size * 0.16,
            },
          ]}
        />
        <View
          style={[
            styles.sparkle,
            styles.sparkleSmall,
            {
              backgroundColor: `${art.sparkleColor}A6`,
              bottom: size * 0.24,
              left: size * 0.18,
            },
          ]}
        />

        {kind === "frame" ? (
          <View
            style={[
              styles.frameShell,
              {
                borderColor: `${art.rimColor}AA`,
                borderRadius: radius - 8,
              },
            ]}>
            <View style={[styles.avatarCore, { backgroundColor: `${art.rimColor}22` }]}>
              <MaterialCommunityIcons
                name={"account" as never}
                size={iconSize}
                color={art.iconColor}
              />
            </View>
          </View>
        ) : kind === "title" ? (
          <View style={[styles.titlePlate, { backgroundColor: `${art.rimColor}22` }]}>
            <MaterialCommunityIcons
              name={art.icon as never}
              size={iconSize}
              color={art.iconColor}
            />
            <View style={styles.titleLines}>
              <View style={[styles.titleLine, { backgroundColor: `${art.rimColor}CC` }]} />
              <View
                style={[
                  styles.titleLine,
                  styles.titleLineShort,
                  { backgroundColor: `${art.rimColor}88` },
                ]}
              />
            </View>
          </View>
        ) : (
          <View style={[styles.iconNest, { backgroundColor: `${art.rimColor}20` }]}>
            <MaterialCommunityIcons
              name={art.icon as never}
              size={iconSize}
              color={art.iconColor}
            />
          </View>
        )}
      </LinearGradient>

      <View style={[styles.banner, { width: bannerWidth, backgroundColor: art.rimColor }]}>
        <Text style={styles.bannerText} numberOfLines={1}>
          {label}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    alignItems: "center",
    justifyContent: "center",
  },
  shell: {
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
  },
  rim: {
    position: "absolute",
    top: 4,
    right: 4,
    bottom: 4,
    left: 4,
    borderWidth: 1.3,
  },
  sparkle: {
    position: "absolute",
    width: 10,
    height: 10,
    borderRadius: 999,
  },
  sparkleSmall: {
    width: 6,
    height: 6,
  },
  iconNest: {
    width: "54%",
    height: "54%",
    borderRadius: 999,
    alignItems: "center",
    justifyContent: "center",
  },
  titlePlate: {
    width: "72%",
    height: "48%",
    borderRadius: 16,
    paddingHorizontal: 10,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  titleLines: {
    flex: 1,
    gap: 5,
  },
  titleLine: {
    height: 5,
    borderRadius: 999,
    width: "100%",
  },
  titleLineShort: {
    width: "68%",
  },
  frameShell: {
    width: "64%",
    height: "64%",
    borderWidth: 2,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255,255,255,0.16)",
  },
  avatarCore: {
    width: "68%",
    height: "68%",
    borderRadius: 999,
    alignItems: "center",
    justifyContent: "center",
  },
  banner: {
    position: "absolute",
    bottom: 0,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
    shadowColor: "#000000",
    shadowOpacity: 0.08,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 6,
    elevation: 2,
  },
  bannerText: {
    color: "#FFFFFF",
    textAlign: "center",
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.3,
    textTransform: "uppercase",
  },
});
