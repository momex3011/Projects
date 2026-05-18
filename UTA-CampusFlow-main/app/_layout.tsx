import { AppThemeProvider } from "@/components/app-theme-provider";
import { Slot } from "expo-router";

export default function RootLayout() {
  return (
    <AppThemeProvider>
      <Slot />
    </AppThemeProvider>
  );
}
