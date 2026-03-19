/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Suspense } from "react";
import { type Mock, vi } from "vitest";
import { directoryQueries } from "@/queries/directories/queries";
import type { Directory } from "@/services/api/directories/types";
import { StudyDestinationFE } from "..";
import type { DirectoryDestination } from "../types";

// Mock react-i18next so translated keys are returned as-is.
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: "en", changeLanguage: vi.fn() },
  }),
  initReactI18next: { type: "3rdParty", init: vi.fn() },
}));

////////////////////////////////////////////////////////////////
// Fixtures
////////////////////////////////////////////////////////////////

/**
 * Builds a flat directory list representing:
 *
 * root
 * ├── directoryA        (id: "a")
 * │   ├── subA1      (id: "a1")  ← leaf
 * │   └── subA2      (id: "a2")
 * │       └── deep   (id: "a2d") ← leaf
 * ├── directoryB        (id: "b")   ← leaf
 * └── directoryC        (id: "c")   ← leaf
 *
 * @returns Flat directories structure.
 */
function makeDirectories(): Directory[] {
  return [
    { id: "a", name: "directoryA", parentId: null },
    { id: "a1", name: "subA1", parentId: "a" },
    { id: "a2", name: "subA2", parentId: "a" },
    { id: "a2d", name: "deep", parentId: "a2" },
    { id: "b", name: "directoryB", parentId: null },
    { id: "c", name: "directoryC", parentId: null },
  ];
}

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

const ROOT_DIRECTORY: DirectoryDestination = { directoryId: null, newSubdirectoriesPath: "" };

interface RenderOptions {
  value?: DirectoryDestination;
  onChange?: Mock;
  onBlur?: Mock;
  error?: boolean;
  helperText?: React.ReactNode;
}

function renderComponent(options: RenderOptions = {}) {
  const {
    value = ROOT_DIRECTORY,
    onChange = vi.fn(),
    onBlur = vi.fn(),
    error,
    helperText,
  } = options;

  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: Infinity },
    },
  });

  // Pre-seed the cache so useSuspenseQuery resolves synchronously.
  queryClient.setQueryData(directoryQueries.list().queryKey, makeDirectories());

  const result = render(
    <QueryClientProvider client={queryClient}>
      <Suspense fallback={<div>Loading…</div>}>
        <StudyDestinationFE
          value={value}
          onChange={onChange}
          onBlur={onBlur}
          error={error}
          helperText={helperText}
        />
      </Suspense>
    </QueryClientProvider>,
  );

  return { ...result, onChange, onBlur };
}

function getDirectoryNames(): string[] {
  const listbox = screen.getByRole("listbox");
  const options = within(listbox).queryAllByRole("option");
  return options.map((element) => element.getAttribute("aria-label") ?? "");
}

async function clickDirectory(user: ReturnType<typeof userEvent.setup>, name: string) {
  const listbox = screen.getByRole("listbox");
  const option = within(listbox).getByRole("option", { name });
  await user.click(option);
}

function getNewDirectoryPathInput(): HTMLInputElement {
  return screen.getByRole("textbox", {
    name: "studies.destination.newDirectoryPath",
  });
}

function getGoUpButton(): HTMLButtonElement {
  return screen.getByRole("button", {
    name: "studies.destination.goUp",
  });
}

////////////////////////////////////////////////////////////////
// Tests
////////////////////////////////////////////////////////////////

describe("StudyDestinationFE", () => {
  describe("initial rendering at root", () => {
    test("displays root-level directories sorted alphabetically", () => {
      renderComponent();
      expect(getDirectoryNames()).toEqual(["directoryA", "directoryB", "directoryC"]);
    });

    test("shows root breadcrumb as active", () => {
      renderComponent();
      expect(screen.getByRole("button", { name: "root" })).toBeInTheDocument();
    });

    test("go-up button is disabled at root", () => {
      renderComponent();
      expect(getGoUpButton()).toBeDisabled();
    });

    test("new directory path input is empty", () => {
      renderComponent();
      expect(getNewDirectoryPathInput().value).toBe("");
    });
  });

  describe("initial rendering with pre-set value", () => {
    test("navigates directly to the directory matching the ID", () => {
      renderComponent({ value: { directoryId: "a2", newSubdirectoriesPath: "" } });

      // Should show children of subA2 (id: "a2")
      expect(getDirectoryNames()).toEqual(["deep"]);

      // Breadcrumbs: root > directoryA > subA2
      expect(screen.getByRole("button", { name: "root" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "directoryA" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "subA2" })).toBeInTheDocument();

      // No new directory path since the value has an empty newSubdirectoriesPath
      expect(getNewDirectoryPathInput().value).toBe("");
    });

    test("navigates to a root-level directory", () => {
      renderComponent({ value: { directoryId: "a", newSubdirectoriesPath: "" } });

      // Should show children of directoryA
      expect(getDirectoryNames()).toEqual(["subA1", "subA2"]);

      expect(screen.getByRole("button", { name: "root" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "directoryA" })).toBeInTheDocument();
    });

    test("populates the new directory path input when newSubdirectoriesPath is provided", () => {
      renderComponent({ value: { directoryId: "a", newSubdirectoriesPath: "newChild" } });

      // Should show children of directoryA (the known directory)
      expect(getDirectoryNames()).toEqual(["subA1", "subA2"]);

      // New directory path input shows the provided newSubdirectoriesPath
      expect(getNewDirectoryPathInput().value).toBe("newChild");
    });

    test("falls back to root when the directoryId is not found or null", () => {
      renderComponent({ value: { directoryId: "not-found", newSubdirectoriesPath: "" } });

      // Should be at root
      expect(getDirectoryNames()).toEqual(["directoryA", "directoryB", "directoryC"]);
      expect(getNewDirectoryPathInput().value).toBe("");
      expect(getGoUpButton()).toBeDisabled();

      // Also test with null directoryId
      renderComponent({ value: { directoryId: null, newSubdirectoriesPath: "" } });

      expect(getDirectoryNames()).toEqual(["directoryA", "directoryB", "directoryC"]);
      expect(getGoUpButton()).toBeDisabled();
      expect(getNewDirectoryPathInput().value).toBe("");
    });

    test("navigates to a deeply nested directory", () => {
      renderComponent({ value: { directoryId: "a2d", newSubdirectoriesPath: "" } });

      // "deep" is a leaf no children
      expect(screen.getByText("studies.destination.noSubDirectories")).toBeInTheDocument();

      // Breadcrumbs: root > directoryA > subA2 > deep
      expect(screen.getByRole("button", { name: "root" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "directoryA" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "subA2" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "deep" })).toBeInTheDocument();
    });
  });

  describe("directory navigation", () => {
    test("clicking a directory navigates into it and shows its children", async () => {
      const user = userEvent.setup();
      const { onChange } = renderComponent();

      await clickDirectory(user, "directoryA");

      // Now shows children of directoryA
      expect(getDirectoryNames()).toEqual(["subA1", "subA2"]);

      // onChange emitted the structured value
      expect(onChange).toHaveBeenCalledWith({
        target: { value: { directoryId: "a", newSubdirectoriesPath: "" } },
      });
    });
  });

  describe("go-up button", () => {
    test("becomes disabled once we reach root", async () => {
      const user = userEvent.setup();
      renderComponent();

      await clickDirectory(user, "directoryA");
      expect(getGoUpButton()).not.toBeDisabled();

      await user.click(getGoUpButton());
      expect(getGoUpButton()).toBeDisabled();
    });

    test("navigates correctly from a deeply nested directory", async () => {
      const user = userEvent.setup();
      renderComponent({ value: { directoryId: "a2d", newSubdirectoriesPath: "" } });

      // Currently in "deep" (child of subA2)
      expect(screen.getByText("studies.destination.noSubDirectories")).toBeInTheDocument();

      // Go up to subA2
      await user.click(getGoUpButton());
      expect(getDirectoryNames()).toEqual(["deep"]);

      // Go up to directoryA
      await user.click(getGoUpButton());
      expect(getDirectoryNames()).toEqual(["subA1", "subA2"]);

      // Go up to root
      await user.click(getGoUpButton());
      expect(getDirectoryNames()).toEqual(["directoryA", "directoryB", "directoryC"]);
      expect(getGoUpButton()).toBeDisabled();
    });
  });

  describe("breadcrumb navigation", () => {
    test("clicking root breadcrumb returns to root from nested directory", async () => {
      const user = userEvent.setup();
      const { onChange } = renderComponent();

      await clickDirectory(user, "directoryA");
      await clickDirectory(user, "subA2");

      // Click root breadcrumb
      await user.click(screen.getByRole("button", { name: "root" }));

      expect(getDirectoryNames()).toEqual(["directoryA", "directoryB", "directoryC"]);
      expect(onChange).toHaveBeenLastCalledWith({
        target: { value: { directoryId: null, newSubdirectoriesPath: "" } },
      });
    });
  });

  describe("new directory path input", () => {
    test("pressing Backspace on empty new directory path triggers go-up", async () => {
      const user = userEvent.setup();
      const { onChange } = renderComponent();

      // Navigate into directoryA
      await clickDirectory(user, "directoryA");
      expect(getDirectoryNames()).toEqual(["subA1", "subA2"]);

      // Focus the input and press Backspace
      const input = getNewDirectoryPathInput();
      await user.click(input);
      await user.keyboard("{Backspace}");

      // Should have gone up to root
      expect(getDirectoryNames()).toEqual(["directoryA", "directoryB", "directoryC"]);
      expect(onChange).toHaveBeenLastCalledWith({
        target: { value: { directoryId: null, newSubdirectoriesPath: "" } },
      });
    });

    test("Backspace does nothing when new directory path has text", async () => {
      const user = userEvent.setup();
      renderComponent();

      const input = getNewDirectoryPathInput();
      await user.click(input);
      await user.type(input, "ab");

      // Now press Backspace should just remove last character, not navigate
      await user.keyboard("{Backspace}");
      expect(input.value).toBe("a");

      // Still at root
      expect(getDirectoryNames()).toEqual(["directoryA", "directoryB", "directoryC"]);
    });

    test("new directory path is preserved when navigating via directory click", async () => {
      const user = userEvent.setup();
      const { onChange } = renderComponent();

      // Type a new name at root
      const input = getNewDirectoryPathInput();
      await user.click(input);
      await user.type(input, "extra");

      // Now click a directory
      await clickDirectory(user, "directoryA");

      // The new directory path should still be present
      expect(getNewDirectoryPathInput().value).toBe("extra");
      expect(onChange).toHaveBeenLastCalledWith({
        target: { value: { directoryId: "a", newSubdirectoriesPath: "extra" } },
      });
    });
  });

  describe("combined interactions", () => {
    test("full workflow: navigate, type new directory path, breadcrumb back, verify value", async () => {
      const user = userEvent.setup();
      const { onChange } = renderComponent();

      // 1. Navigate into directoryA
      await clickDirectory(user, "directoryA");
      expect(onChange).toHaveBeenLastCalledWith({
        target: { value: { directoryId: "a", newSubdirectoriesPath: "" } },
      });

      // 2. Navigate into subA2
      await clickDirectory(user, "subA2");
      expect(onChange).toHaveBeenLastCalledWith({
        target: { value: { directoryId: "a2", newSubdirectoriesPath: "" } },
      });

      // 3. Type a new sub-directory path
      const input = getNewDirectoryPathInput();
      await user.click(input);
      await user.type(input, "new-directory");
      expect(onChange).toHaveBeenLastCalledWith({
        target: { value: { directoryId: "a2", newSubdirectoriesPath: "new-directory" } },
      });

      // 4. Click the directoryA breadcrumb to jump back
      await user.click(screen.getByRole("button", { name: "directoryA" }));

      // new directory path should be preserved
      expect(getNewDirectoryPathInput().value).toBe("new-directory");
      expect(onChange).toHaveBeenLastCalledWith({
        target: { value: { directoryId: "a", newSubdirectoriesPath: "new-directory" } },
      });

      // 5. Clear the new directory path and go to root
      await user.clear(getNewDirectoryPathInput());
      await user.click(screen.getByRole("button", { name: "root" }));

      expect(getDirectoryNames()).toEqual(["directoryA", "directoryB", "directoryC"]);
      expect(onChange).toHaveBeenLastCalledWith({
        target: { value: { directoryId: null, newSubdirectoriesPath: "" } },
      });
    });
  });
});
