// firebase/auth.ts
import { signInAnonymously, signInWithEmailAndPassword } from "firebase/auth";
import { auth } from "./firebase";

// Login with UTA email
export const loginUTAEmail = async (email: string, password: string) => {
  if (!email.endsWith("@mavs.uta.edu")) {
    throw new Error("Email must be a UTA email.");
  }
  return signInWithEmailAndPassword(auth, email, password);
};

// Login as guest (anonymous)
export const loginGuest = async () => {
  return signInAnonymously(auth);
};