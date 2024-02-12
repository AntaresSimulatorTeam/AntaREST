import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

const SERVER_URL = "http://localhost:8080";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isDesktopMode = mode === "desktop";

  return {
    // Serve the web app at the `/static` entry point on Desktop mode
    base: isDesktopMode ? "/static/" : "/",
    plugins: [react({ devTarget: "es2022" })],
    server: {
      port: 3000,
      strictPort: true,
      proxy: {
        // API, WebSocket and Swagger URLs
        "^/(v1|health|kill|version|ws|openapi.json|redoc)": {
          target: SERVER_URL,
          changeOrigin: true, // Recommended for avoiding CORS issues
          ws: true, // WebSocket support for hot module replacement
        },
      },
    },
  };
});
