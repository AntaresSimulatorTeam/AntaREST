import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

const SERVER_URL = "http://localhost:8080";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isDesktopMode = mode === "desktop";

  return {
    // When the web application is running in Desktop mode,
    // the web app is served at the `/static` entry point
    base: isDesktopMode ? "/static/" : "/",
    plugins: [react({ devTarget: "es2022" })],
    server: {
      port: 3000,
      strictPort: true,
      proxy: {
        // Main API URLs
        "/v1": SERVER_URL,
        // Core API URLs
        "/health": SERVER_URL,
        "/kill": SERVER_URL,
        "/version": SERVER_URL,
        // WebSocket
        "/ws": SERVER_URL,
      },
    },
  };
});
