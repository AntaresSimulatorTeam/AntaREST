/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

const SERVER_URL = "http://localhost:8080";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isDesktopMode = mode === "desktop";

  return {
    // Serve the web app at the `/static` entry point on Desktop mode (cf. 'antarest/main.py')
    base: isDesktopMode ? "/static/" : "/",
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
