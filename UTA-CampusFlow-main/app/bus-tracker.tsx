import { AppBackground } from "@/components/app-background";
import { useAppTheme } from "@/components/app-theme-provider";
import { useRouter } from "expo-router";
import React from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";

const busRoutes = [
  { name: "Express Route", hours: "7:30 AM - 6:00 PM Monday-Friday", color: "#FF5733", stops: ["Lot27/Studio Arts","Arbor Oaks","Greek Row Parking Lot","University Center","MAC","P.E. Building","Greek Row (Arbor Oaks/Meadow Run)"] },
  { name: "Orange Route", hours: "7:30 AM - 6:00 PM Monday-Friday", color: "#FFA500", stops: ["Lot 27/Studio Arts","Lot 26/Maverick Stadium","Maverick Place","848 Mitchell","Centennial Court","Pickard Hall","College of Business","Smart Hospital","Greek Row (Arbor Oaks/Meadow Run)"] },
  { name: "Blue Route", hours: "7:30 AM - 6:00 PM Monday-Friday", color: "#1E90FF", stops: ["University Center","MAC","Greek Row (Arbor Oaks/Meadow Run)","Meadow Run","Swift Center","Timber Brook","The Arlie"] },
  { name: "Black Route", hours: "7:30 AM - 6:00 PM Monday-Friday", color: "#000000", stops: ["Lot 53","Lot 52","Lot 50","Heights on Pecan","College of Business"] },
  { name: "Yellow Route", hours: "7:30 AM - 6:00 PM Monday-Friday", color: "#FFD700", stops: ["Liv+","Mesquite/1st Street*","University Center","Arlington Hall/CPC","College of Business"] },
  { name: "Extended Red Route", hours: "7:30 AM - 7:00 PM Monday-Friday", color: "#FF0000", stops: ["Maverick Place","848 Mitchell","Centennial Court","Lot 49","Lot 50","Heights on Pecan/Lot 56","Livplus","Business Building","College Park Center","UC","Social Work","Arli","Timber Brook","MAC","Greek Row","Studio Arts","UC"] },
  { name: "Green Shopping Route", hours: "5:30 PM - 9:00 PM Monday-Friday", color: "#008000", stops: ["UTA","Walmart"], notes: "Departs UTA every :00 and :30, departs Walmart every :15 and :45 minutes" },
];

export default function BusTrackerScreen() {
  const router = useRouter();
  const { palette } = useAppTheme();

  return (
    <AppBackground>
      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.push("/")}>
          <Text style={[styles.backButtonText, { color: palette.accent }]}>&larr; Back to Home</Text>
        </TouchableOpacity>

        <Text style={[styles.title, { color: palette.text }]}>Campus Bus Tracker</Text>

        {busRoutes.map((route, index) => (
          <View key={index} style={[styles.routeCard, { backgroundColor: palette.surface, borderColor: palette.border }]}>
            <View style={[styles.colorBar, { backgroundColor: route.color }]} />
            <Text style={[styles.routeName, { color: palette.text }]}>{route.name}</Text>
            <Text style={[styles.hours, { color: palette.mutedText }]}>{route.hours}</Text>
            <Text style={[styles.stopsLabel, { color: palette.text }]}>Stops:</Text>
            {route.stops.map((stop, i) => (
              <Text key={i} style={[styles.stop, { color: palette.mutedText }]}>• {stop}</Text>
            ))}
            {route.notes && <Text style={[styles.notes, { color: palette.mutedText }]}>Note: {route.notes}</Text>}
          </View>
        ))}
      </ScrollView>
    </AppBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    paddingTop: 85,
    paddingBottom: 40,
  },
  backButton: {
    marginBottom: 15,
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: "bold",
  },
  title: {
    fontSize: 28,
    fontWeight: "bold",
    marginBottom: 20,
    textAlign: "center",
  },
  routeCard: {
    borderRadius: 18,
    borderWidth: 1,
    padding: 16,
    marginBottom: 14,
  },
  colorBar: {
    height: 6,
    width: "100%",
    borderRadius: 3,
    marginBottom: 10,
  },
  routeName: {
    fontSize: 20,
    fontWeight: "bold",
    marginBottom: 5,
  },
  hours: {
    fontSize: 14,
    marginBottom: 10,
  },
  stopsLabel: {
    fontWeight: "700",
    marginBottom: 5,
  },
  stop: {
    fontSize: 14,
    marginLeft: 10,
    marginBottom: 2,
  },
  notes: {
    marginTop: 10,
    fontStyle: "italic",
  },
});