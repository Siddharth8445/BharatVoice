/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#2563EB",
        "primary-hover": "#1D4ED8",
        background: "#F8FAFC",
        surface: "#FFFFFF",
        border: "#E2E8F0",
        heading: "#0F172A",
        body: "#475569",
        success: "#16A34A",
        warning: "#D97706",
        danger: "#DC2626",
      },
    },
  },
  plugins: [],
}
