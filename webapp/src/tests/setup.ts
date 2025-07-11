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

import "@testing-library/jest-dom/vitest";
import { expect, afterEach } from "vitest";
import { cleanup } from "@testing-library/react";
import * as matchers from "@testing-library/jest-dom/matchers";
import "./mocks/mockResizeObserver";

// Set timezone to UTC for consistent test behavior across different environments
process.env.TZ = "UTC";

// Extend Vitest's expect function with jest-dom matchers for enhanced DOM assertions.
expect.extend(matchers);

afterEach(() => {
  cleanup();
});

// Additional setup can include:
// - Mocks: Define global mocks for browser APIs like localStorage, fetch, etc.
// - Global Test Data: Setup common data used across multiple test files.
// - Configuration Settings: Adjust global settings for tests, such as timeouts or environment variables.
// - Cleanup: Implement global afterEach or beforeEach hooks for cleanup and setup between tests.
