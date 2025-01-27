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

import { defineConfig } from "cypress";
import { resolve } from "path";

export default defineConfig({
  e2e: {
    supportFile: "cypress/support/e2e.ts",
    specPattern: "cypress/e2e/**/*.cy.{ts,tsx}",
    baseUrl: "http://localhost:3000",
    viewportWidth: 1280,
    viewportHeight: 720,
  },
  component: {
    supportFile: "cypress/support/component.ts",
    specPattern: "cypress/component/**/*.cy.{ts,tsx}",
    devServer: {
      framework: "react",
      bundler: "vite",
      viteConfig: {
        configFile: resolve(import.meta.dirname, "vite.config.ts"),
      },
    },
  },
});
