/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

//! Keep '0.0.0.0', because 'localhost' may not working on Mac
const SERVER_URL = "http://0.0.0.0:8080";

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
    build: {
      // Exclude test files and directories from production builds
      // This improves build performance and reduces bundle size
      rollupOptions: {
        external: ["**/__tests__/**", "**/*.test.ts", "**/*.test.tsx"],
      },
    },
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"), // Relative imports from the src directory
      },
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
      globals: true, // Use the APIs globally,
      environment: "jsdom",
      css: true,
      setupFiles: "./src/tests/setup.ts",
    },
  };
});
