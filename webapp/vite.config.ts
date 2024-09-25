/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

const SERVER_URL = "http://localhost:8080";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isDesktopMode = mode === "desktop";

  return {
    // Serve the web app at the `/static` entry point on Desktop mode (cf. 'antarest/main.py')
    base: isDesktopMode ? "/static/" : "/",
    // Entries will be defined as globals during dev and statically replaced during build
    define: {
      // Not working in dev without `JSON.stringify`
      __BUILD_TIMESTAMP__: JSON.stringify(Date.now()),
    },
    esbuild: {
      // Remove logs safely when building production bundle
      // https://esbuild.github.io/api/#pure
      pure: mode === "production" ? ["console"] : [],
    },
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
    test: {
      globals: true, // Use the APIs globally
      environment: "jsdom",
      css: true,
      setupFiles: "./src/tests/setup.ts",
    },
  };
});
