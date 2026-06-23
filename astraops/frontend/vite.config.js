import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/predict": "http://localhost:8000",
      "/simulate": "http://localhost:8000",
      "/similar-events": "http://localhost:8000",
      "/feedback": "http://localhost:8000",
    },
  },
});
