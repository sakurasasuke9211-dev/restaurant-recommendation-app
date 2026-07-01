/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        zomato: {
          red: "#CB202D",
          brand: "#8B1538",
          dark: "#1A1A1A",
          muted: "#696969",
          cream: "#F9F9F9",
          surface: "#FFFFFF",
          rating: "#24963F",
        },
      },
      fontFamily: {
        sans: ["Inter", "DM Sans", "system-ui", "sans-serif"],
        display: ["Georgia", "Times New Roman", "serif"],
      },
      boxShadow: {
        card: "0 4px 24px rgba(0, 0, 0, 0.08)",
        search: "0 8px 40px rgba(0, 0, 0, 0.06)",
        hero: "0 16px 48px rgba(0, 0, 0, 0.25)",
      },
    },
  },
  plugins: [],
};
