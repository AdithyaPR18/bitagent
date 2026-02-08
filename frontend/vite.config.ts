import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
      "/agent": "http://localhost:8000",
      "/ml": "http://localhost:8000",
      "/reputation": "http://localhost:8000",
      "/payments": "http://localhost:8000",
      "/dashboard": "http://localhost:8000",
      "/health": "http://localhost:8000",
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
});
