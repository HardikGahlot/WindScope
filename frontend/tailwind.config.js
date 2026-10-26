/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#070b14",
          900: "#0b1120",
          850: "#0f172a",
          800: "#1e293b",
          700: "#334155",
        },
        brand: {
          cyan: "#06b6d4",
          teal: "#14b8a6",
          emerald: "#10b981",
          amber: "#f59e0b",
          rose: "#f43f5e",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
}
