/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0B0F14",
        panel: "#121821",
        panel2: "#1A2230",
        border: "#26303F",
        accent: "#FF6A3D",
        accent2: "#2DD4BF",
        risk: {
          low: "#2DD4BF",
          medium: "#F5A623",
          high: "#FF6A3D",
          critical: "#E5484D",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
    },
  },
  plugins: [],
};
