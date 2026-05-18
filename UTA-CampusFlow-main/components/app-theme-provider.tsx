import {
  BACKGROUND_THEMES,
  DEFAULT_THEME_ID,
  getBackgroundTheme,
} from "@/constants/background-themes";
import { auth, db } from "@/firebase/firebase";
import {
  ensureUserProfile,
  normalizeUnlockedThemes,
  syncUserProfileIdentity,
} from "@/firebase/user-profile";
import { onAuthStateChanged } from "firebase/auth";
import { doc, onSnapshot } from "firebase/firestore";
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

type AppThemeContextValue = {
  selectedThemeId: string;
  previewThemeId: string | null;
  unlockedThemes: string[];
  ready: boolean;
  setPreviewThemeId: React.Dispatch<React.SetStateAction<string | null>>;
};

const AppThemeContext = createContext<AppThemeContextValue>({
  selectedThemeId: DEFAULT_THEME_ID,
  previewThemeId: null,
  unlockedThemes: [DEFAULT_THEME_ID],
  ready: false,
  setPreviewThemeId: () => null,
});

export function AppThemeProvider({ children }: { children: React.ReactNode }) {
  const [selectedThemeId, setSelectedThemeId] = useState(DEFAULT_THEME_ID);
  const [previewThemeId, setPreviewThemeId] = useState<string | null>(null);
  const [unlockedThemes, setUnlockedThemes] = useState<string[]>([DEFAULT_THEME_ID]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let unsubscribeProfile: (() => void) | undefined;

    const unsubscribeAuth = onAuthStateChanged(auth, (user) => {
      unsubscribeProfile?.();

      if (!user || user.isAnonymous) {
        setSelectedThemeId(DEFAULT_THEME_ID);
        setPreviewThemeId(null);
        setUnlockedThemes([DEFAULT_THEME_ID]);
        setReady(true);
        return;
      }

      setReady(false);
      ensureUserProfile(user.uid).catch((error) => {
        console.error("Failed to initialize theme profile:", error);
      });
      syncUserProfileIdentity(user).catch((error) => {
        console.error("Failed to sync user identity:", error);
      });

      const userRef = doc(db, "users", user.uid);
      unsubscribeProfile = onSnapshot(
        userRef,
        (snapshot) => {
          const data = snapshot.data();
          const nextUnlocked = normalizeUnlockedThemes(data?.unlockedThemes);
          const nextSelected =
            typeof data?.selectedTheme === "string" && nextUnlocked.includes(data.selectedTheme)
              ? data.selectedTheme
              : DEFAULT_THEME_ID;

          setUnlockedThemes(nextUnlocked);
          setSelectedThemeId(nextSelected);
          setReady(true);
        },
        (error) => {
          console.error("Theme profile listener failed:", error);
          setSelectedThemeId(DEFAULT_THEME_ID);
          setPreviewThemeId(null);
          setUnlockedThemes([DEFAULT_THEME_ID]);
          setReady(true);
        }
      );
    });

    return () => {
      unsubscribeProfile?.();
      unsubscribeAuth();
    };
  }, []);

  const value = useMemo(
    () => ({
      selectedThemeId,
      previewThemeId,
      unlockedThemes,
      ready,
      setPreviewThemeId,
    }),
    [previewThemeId, ready, selectedThemeId, unlockedThemes]
  );

  return <AppThemeContext.Provider value={value}>{children}</AppThemeContext.Provider>;
}

export function useAppTheme() {
  const context = useContext(AppThemeContext);
  const currentTheme = useMemo(
    () => getBackgroundTheme(context.previewThemeId ?? context.selectedThemeId),
    [context.previewThemeId, context.selectedThemeId]
  );

  return {
    ...context,
    currentTheme,
    isPreviewing: context.previewThemeId !== null,
    palette: currentTheme.palette,
    isDark: currentTheme.palette.isDark,
    availableThemes: BACKGROUND_THEMES,
  };
}
