import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        body: ["var(--font-body)", "sans-serif"],
        display: ["var(--font-display)", "sans-serif"]
      },
      boxShadow: {
        clay:
          "24px 24px 48px rgba(8, 14, 24, 0.34), -18px -18px 36px rgba(255, 255, 255, 0.08), inset 1px 1px 0 rgba(255,255,255,0.2)",
        "clay-soft":
          "18px 18px 36px rgba(8, 14, 24, 0.26), -10px -10px 24px rgba(255, 255, 255, 0.06), inset 1px 1px 0 rgba(255,255,255,0.14)"
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-6px)" }
        },
        pulseGlow: {
          "0%, 100%": { opacity: "0.45" },
          "50%": { opacity: "0.9" }
        }
      },
      animation: {
        float: "float 8s ease-in-out infinite",
        "pulse-glow": "pulseGlow 4s ease-in-out infinite"
      }
    }
  },
  plugins: []
};

export default config;
