import type { Config } from "tailwindcss";
import plugin from "tailwindcss/plugin";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        builder: {
          bg: "#f6f1ff",
          ink: "#2f3049",
          muted: "#6b6f8f",
          blush: "#ffb8d1",
          mint: "#b8f2e6",
          sun: "#ffd166",
          sky: "#7bdff2",
          lilac: "#d9c2ff",
        },
      },
      borderRadius: {
        clay: "32px",
        "clay-xl": "42px",
      },
      boxShadow: {
        clay: "14px 18px 36px rgba(137, 126, 170, 0.22), -14px -14px 30px rgba(255, 255, 255, 0.86), inset 2px 2px 4px rgba(255, 255, 255, 0.7), inset -8px -8px 14px rgba(193, 197, 255, 0.16)",
        "clay-soft": "8px 10px 20px rgba(137, 126, 170, 0.14), -8px -8px 16px rgba(255, 255, 255, 0.78), inset 1px 1px 2px rgba(255, 255, 255, 0.8), inset -4px -4px 10px rgba(193, 197, 255, 0.14)",
        "clay-pressed": "inset 7px 7px 14px rgba(204, 198, 231, 0.64), inset -8px -8px 15px rgba(255, 255, 255, 0.88)",
      },
      backgroundImage: {
        "builder-glow":
          "radial-gradient(circle at 12% 18%, rgba(255, 184, 209, 0.75), transparent 34%), radial-gradient(circle at 88% 12%, rgba(123, 223, 242, 0.55), transparent 28%), radial-gradient(circle at 54% 92%, rgba(255, 209, 102, 0.4), transparent 26%), linear-gradient(160deg, #f8f4ff 0%, #eef3ff 48%, #fff7ef 100%)",
      },
    },
  },
  plugins: [
    plugin(({ addUtilities, theme }) => {
      addUtilities({
        ".clay-surface": {
          background:
            "linear-gradient(145deg, rgba(255,255,255,0.92), rgba(241,243,255,0.62))",
          borderRadius: theme("borderRadius.clay") as string,
          border: "1px solid rgba(255,255,255,0.82)",
          boxShadow: theme("boxShadow.clay") as string,
          backdropFilter: "blur(24px)",
        },
        ".clay-inset": {
          background:
            "linear-gradient(145deg, rgba(243,239,255,0.92), rgba(255,255,255,0.74))",
          boxShadow: theme("boxShadow.clay-pressed") as string,
          borderRadius: "28px",
        },
        ".clay-chip": {
          background:
            "linear-gradient(145deg, rgba(255,255,255,0.88), rgba(244,247,255,0.74))",
          border: "1px solid rgba(255,255,255,0.8)",
          borderRadius: "999px",
          boxShadow: theme("boxShadow.clay-soft") as string,
        },
      });
    }),
  ],
};

export default config;
