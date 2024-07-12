import * as matchers from "@testing-library/jest-dom/matchers";
import "@testing-library/jest-dom";
import { cleanup } from "@testing-library/react";
import { expect } from "vitest";

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
