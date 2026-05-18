// firebase/firebase.ts
import ReactNativeAsyncStorage from "@react-native-async-storage/async-storage";
import { getReactNativePersistence } from "@firebase/auth/dist/rn/index.js";
import { initializeApp } from "firebase/app";
import {
  getAuth,
  initializeAuth,
} from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyCEpz1vDRpe6JXonyQMpLZQunsvV7DLaK0",
  authDomain: "campusflow-372c6.firebaseapp.com",
  projectId: "campusflow-372c6",
  storageBucket: "campusflow-372c6.appspot.com",
  messagingSenderId: "962317562696",
  appId: "1:962317562696:web:4c9b245bb2c51d3512397d"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firestore
const db = getFirestore(app);

// Initialize Firebase Auth
const auth = (() => {
  try {
    return initializeAuth(app, {
      persistence: getReactNativePersistence(ReactNativeAsyncStorage),
    });
  } catch {
    return getAuth(app);
  }
})();

export { app, auth, db };
