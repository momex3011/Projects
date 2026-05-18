import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { StyleProp, StyleSheet, View, ViewStyle } from "react-native";
import { useAppTheme } from "./app-theme-provider";

export function AppBackground({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  const { currentTheme, palette } = useAppTheme();

  return (
    <View style={[styles.container, { backgroundColor: palette.background }, style]}>
      <LinearGradient
        colors={currentTheme.gradient.colors}
        start={currentTheme.gradient.start}
        end={currentTheme.gradient.end}
        style={StyleSheet.absoluteFill}
      />
      <View pointerEvents="none" style={StyleSheet.absoluteFill}>
        <View style={[styles.glowPrimary, { backgroundColor: palette.glowPrimary }]} />
        <View style={[styles.glowSecondary, { backgroundColor: palette.glowSecondary }]} />
      </View>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  glowPrimary: {
    position: "absolute",
    top: -90,
    right: -50,
    width: 280,
    height: 280,
    borderRadius: 140,
    opacity: 0.9,
  },
  glowSecondary: {
    position: "absolute",
    bottom: -110,
    left: -70,
    width: 300,
    height: 300,
    borderRadius: 150,
    opacity: 0.9,
  },
});
