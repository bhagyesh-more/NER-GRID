/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        command: {
          bg: "#0B0F19",
          card: "#111827",
          panel: "#0D1322",
          border: "#1F2937",
          accent: "#3B82F6",
          emerald: "#10B981",
          amber: "#F59E0B",
          rose: "#EF4444",
          muted: "#9CA3AF",
        }
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "Courier New", "monospace"],
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      }
    },
  },
  plugins: [],
}
