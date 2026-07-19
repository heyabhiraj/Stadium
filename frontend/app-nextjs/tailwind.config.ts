import type { Config } from "tailwindcss";

// Design system tokens from implementation.md (navy/blue + status colours,
// Inter type, 12px radius, 8px spacing grid).
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#0b1f3a",
        brand: "#2563eb",
        success: "#16a34a",
        warning: "#f59e0b",
        busy: "#ea580c",
        danger: "#dc2626",
        surface: "#ffffff",
        canvas: "#f4f6fb",
      },
      borderRadius: { xl: "12px" },
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
};
export default config;
