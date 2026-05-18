// app/AuthScreen.tsx
import { useRouter } from "expo-router";
import { createUserWithEmailAndPassword, sendEmailVerification, sendPasswordResetEmail } from "firebase/auth";
import React, { useState } from "react";
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { UTA } from "../constants/theme";
import { loginGuest, loginUTAEmail } from "../firebase/auth";
import { auth } from "../firebase/firebase";

type AuthScreenProps = {
  onAuthSuccess?: () => void; // optional callback
};

export default function AuthScreen({ onAuthSuccess }: AuthScreenProps) {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [unverifiedUser, setUnverifiedUser] = useState<any>(null);

  // Login with UTA email
  const handleLogin = async () => {
    if (!email.endsWith("@mavs.uta.edu")) {
      Alert.alert("Invalid Email", "Use your UTA email ending with @mavs.uta.edu");
      return;
    }

    setLoading(true);
    try {
      const userCredential = await loginUTAEmail(email, password);
      const user = userCredential.user;

      await user.reload(); // refresh verification status

      if (!user.emailVerified) {
        setUnverifiedUser(user);
        Alert.alert(
          "Email not verified",
          "Please verify your UTA email before logging in. You can resend the verification link below."
        );
        return;
      }

      setUnverifiedUser(null);
      if (onAuthSuccess) onAuthSuccess();
      else router.replace("/");
    } catch (err: any) {
      console.error(err);
      Alert.alert("Login Failed", err.message || "Unknown error occurred");
    } finally {
      setLoading(false);
    }
  };

  // Guest login
  const handleGuestLogin = async () => {
    setLoading(true);
    try {
      const userCredential = await loginGuest();
      console.log("Logged in as guest:", userCredential.user.uid);

      if (onAuthSuccess) onAuthSuccess();
      else router.replace("/");
    } catch (err: any) {
      console.error(err);
      Alert.alert("Login Failed", err.message || JSON.stringify(err));
    } finally {
      setLoading(false);
    }
  };

  // Signup with UTA email
  const handleSignUp = async () => {
    if (!email.endsWith("@mavs.uta.edu")) {
      Alert.alert("Invalid Email", "Please use your UTA email ending with @mavs.uta.edu");
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert("Password Mismatch", "Passwords do not match");
      return;
    }
    if (password.length < 6) {
      Alert.alert("Weak Password", "Password should be at least 6 characters");
      return;
    }

    setLoading(true);
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      if (userCredential.user) {
        await sendEmailVerification(userCredential.user);
        Alert.alert(
          "Verify your email",
          "A verification link has been sent to your UTA email. Please verify before logging in."
        );
        setMode("login");
      }
    } catch (err: any) {
      console.error(err);
      Alert.alert("Sign Up Failed", err.message || "Unknown error occurred");
    } finally {
      setLoading(false);
    }
  };

  // Forgot password
  const handleForgotPassword = async () => {
    if (!email.endsWith("@mavs.uta.edu")) {
      Alert.alert("Invalid Email", "Use your UTA email to reset password.");
      return;
    }
    setLoading(true);
    try {
      await sendPasswordResetEmail(auth, email);
      Alert.alert("Email Sent", "Password reset email has been sent. Check your inbox.");
    } catch (err: any) {
      console.error(err);
      Alert.alert("Error", err.message || "Failed to send password reset email.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
      >
        {/* UTA Branding Header */}
        <View style={styles.brandHeader}>
          <Text style={styles.brandIcon}>🎓</Text>
          <Text style={styles.title}>UTA CampusFlow</Text>
          <Text style={styles.subtitle}>Your campus, at a glance</Text>
        </View>

        {/* Email Validation Hint */}
        <View style={styles.hintBox}>
          <Text style={styles.hintText}>Use your @mavs.uta.edu email to sign in</Text>
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.inputLabel}>UTA Email</Text>
          <TextInput
            style={styles.input}
            placeholder="yourname@mavs.uta.edu"
            placeholderTextColor="#9CA3AF"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
          />
          <Text style={styles.inputLabel}>Password</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter your password"
            placeholderTextColor="#9CA3AF"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            autoCapitalize="none"
          />
          {mode === "signup" && (
            <>
              <Text style={styles.inputLabel}>Confirm Password</Text>
              <TextInput
                style={styles.input}
                placeholder="Re-enter your password"
                placeholderTextColor="#9CA3AF"
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                secureTextEntry
                autoCapitalize="none"
              />
            </>
          )}
        </View>

        {mode === "login" ? (
          <>
            {/* Primary Login Button */}
            <TouchableOpacity
              style={[styles.buttonPrimary, loading && styles.buttonDisabled]}
              onPress={handleLogin}
              disabled={loading}
            >
              <Text style={styles.buttonPrimaryText}>
                {loading ? "Signing in..." : "Login"}
              </Text>
            </TouchableOpacity>

            <Text style={styles.orText}>OR</Text>

            {/* Ghost-style Guest Button */}
            <TouchableOpacity
              style={[styles.buttonGhost, loading && styles.buttonDisabled]}
              onPress={handleGuestLogin}
              disabled={loading}
            >
              <Text style={styles.buttonGhostText}>Continue as Guest</Text>
            </TouchableOpacity>

            <View style={styles.linksRow}>
              <TouchableOpacity onPress={handleForgotPassword}>
                <Text style={styles.linkText}>Forgot Password?</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => setMode("signup")}>
                <Text style={styles.linkText}>Create Account</Text>
              </TouchableOpacity>
            </View>

            {unverifiedUser && (
              <TouchableOpacity
                onPress={async () => {
                  setLoading(true);
                  try {
                    await sendEmailVerification(unverifiedUser);
                    Alert.alert(
                      "Email Sent",
                      "Verification email resent. Check your inbox."
                    );
                  } catch (err: any) {
                    console.error(err);
                    Alert.alert("Error", err.message || "Failed to resend email.");
                  } finally {
                    setLoading(false);
                  }
                }}
                style={styles.resendBtn}
              >
                <Text style={styles.resendText}>Resend Verification Email</Text>
              </TouchableOpacity>
            )}
          </>
        ) : (
          <>
            <TouchableOpacity
              style={[styles.buttonPrimary, loading && styles.buttonDisabled]}
              onPress={handleSignUp}
              disabled={loading}
            >
              <Text style={styles.buttonPrimaryText}>
                {loading ? "Creating account..." : "Sign Up"}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              onPress={() => setMode("login")}
              style={{ marginTop: 18 }}
            >
              <Text style={styles.linkText}>← Back to Login</Text>
            </TouchableOpacity>
          </>
        )}

        <Text style={styles.footer}>University of Texas at Arlington</Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
    backgroundColor: UTA.offWhite,
  },
  brandHeader: {
    alignItems: "center",
    marginBottom: 24,
  },
  brandIcon: {
    fontSize: 48,
    marginBottom: 8,
  },
  title: {
    fontSize: 32,
    fontWeight: "bold",
    color: UTA.royalBlue,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 15,
    color: UTA.gray500,
    textAlign: "center",
  },
  hintBox: {
    backgroundColor: UTA.lightBlue,
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 14,
    marginBottom: 20,
    borderLeftWidth: 3,
    borderLeftColor: UTA.royalBlue,
  },
  hintText: {
    color: UTA.royalBlue,
    fontSize: 13,
    fontWeight: "500",
  },
  inputContainer: { width: "100%" },
  inputLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: UTA.gray600,
    marginBottom: 4,
    marginLeft: 2,
  },
  input: {
    height: 50,
    backgroundColor: "#fff",
    borderRadius: 10,
    paddingHorizontal: 15,
    marginBottom: 14,
    borderWidth: 1.5,
    borderColor: UTA.gray200,
    fontSize: 15,
    color: UTA.gray800,
  },
  buttonPrimary: {
    width: "100%",
    height: 52,
    backgroundColor: UTA.royalBlue,
    borderRadius: 12,
    justifyContent: "center",
    alignItems: "center",
    marginTop: 8,
    shadowColor: UTA.royalBlue,
    shadowOpacity: 0.3,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 8,
    elevation: 4,
  },
  buttonPrimaryText: {
    color: "#fff",
    fontSize: 17,
    fontWeight: "bold",
    letterSpacing: 0.3,
  },
  buttonDisabled: { opacity: 0.6 },
  orText: {
    marginVertical: 14,
    color: UTA.gray400,
    fontWeight: "600",
    fontSize: 13,
  },
  buttonGhost: {
    width: "100%",
    height: 52,
    backgroundColor: "transparent",
    borderRadius: 12,
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 2,
    borderColor: UTA.royalBlue,
  },
  buttonGhostText: {
    color: UTA.royalBlue,
    fontSize: 17,
    fontWeight: "bold",
  },
  linksRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    width: "100%",
    marginTop: 18,
    paddingHorizontal: 4,
  },
  linkText: {
    color: UTA.blazeOrange,
    fontWeight: "600",
    fontSize: 14,
  },
  resendBtn: {
    marginTop: 14,
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: UTA.lightBlue,
    borderRadius: 8,
  },
  resendText: {
    color: UTA.royalBlue,
    fontWeight: "600",
    fontSize: 14,
  },
  footer: {
    marginTop: 30,
    fontSize: 12,
    color: UTA.gray400,
  },
});