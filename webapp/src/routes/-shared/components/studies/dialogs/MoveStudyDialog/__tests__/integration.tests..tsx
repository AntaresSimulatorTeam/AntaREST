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
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Suspense } from "react";
import { vi } from "vitest";
import { directoryQueries } from "@/queries/directories/queries";
import type { Directory } from "@/services/api/directories/types";
import type { StudyMetadata } from "@/types/types";
import MoveStudyDialog from "..";

////////////////////////////////////////////////////////////////
// Hoisted mocks
////////////////////////////////////////////////////////////////

const {
  mockMoveStudy,
  mockGetDirectories,
  mockEnqueueSnackbar,
  mockDispatch,
  mockUpdateStudyFilters,
} = vi.hoisted(() => ({
  mockMoveStudy: vi.fn(),
  mockGetDirectories: vi.fn(),
  mockEnqueueSnackbar: vi.fn(),
  mockDispatch: vi.fn(),
  mockUpdateStudyFilters: vi.fn((payload: unknown) => ({
    type: "studies/UPDATE_FILTERS",
    payload,
  })),
}));

////////////////////////////////////////////////////////////////
// Module mocks
////////////////////////////////////////////////////////////////

vi.mock("react-i18next", () => {
  const t = (key: string) => key;
  const i18n = { language: "en", changeLanguage: vi.fn() };
  // useTranslation returns an array-like object: [t, i18n, ready]
  // Components may destructure as `const [t] = useTranslation()` or `const { t } = useTranslation()`
  const result = Object.assign([t, i18n, true], { t, i18n, ready: true });
  return {
    useTranslation: () => result,
    initReactI18next: { type: "3rdParty", init: vi.fn() },
  };
});

vi.mock("@/i18n", () => ({
  default: { t: (key: string) => key },
}));

vi.mock("notistack", async (importOriginal) => {
  const actual = await importOriginal<typeof import("notistack")>();
  return {
    ...actual,
    useSnackbar: () => ({
      enqueueSnackbar: mockEnqueueSnackbar,
      closeSnackbar: vi.fn(),
    }),
  };
});

vi.mock("@/hooks/useFormBlocker", () => ({
  default: vi.fn(),
}));

vi.mock("@/redux/hooks/useAppDispatch", () => ({
  default: () => mockDispatch,
}));

vi.mock("@/redux/ducks/studies", () => ({
  updateStudyFilters: mockUpdateStudyFilters,
}));

vi.mock("@/services/api/study", () => ({
  moveStudy: mockMoveStudy,
}));

vi.mock("@/services/api/directories", () => ({
  getDirectories: mockGetDirectories,
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
 * @returns - Flat directories structure.
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

function makeStudy(overrides: Partial<StudyMetadata> = {}): StudyMetadata {
  return {
    id: "study-1",
    name: "Study 1",
    managed: true,
    ...overrides,
  } as StudyMetadata;
}

const directories = makeDirectories();

////////////////////////////////////////////////////////////////
// Setup
////////////////////////////////////////////////////////////////

beforeEach(() => {
  vi.clearAllMocks();
  mockMoveStudy.mockResolvedValue(undefined);
  mockGetDirectories.mockResolvedValue(directories);
  mockDispatch.mockImplementation((action: unknown) => action);
});

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

interface RenderOptions {
  studies: StudyMetadata[];
  open?: boolean;
}

function renderDialog({ studies, open = true }: RenderOptions) {
  const onClose = vi.fn();

  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: Infinity },
    },
  });

  // Pre-seed cache so useSuspenseQuery resolves synchronously.
  queryClient.setQueryData(directoryQueries.list().queryKey, directories);

  render(
    <QueryClientProvider client={queryClient}>
      <Suspense fallback={<div>Loading…</div>}>
        <MoveStudyDialog open={open} onClose={onClose} studies={studies} />
      </Suspense>
    </QueryClientProvider>,
  );

  return { onClose, queryClient };
}

function getSubmitButton() {
  return screen.getByRole("button", { name: "global.move" });
}

function getDirectoryNames(): string[] {
  const listbox = screen.getByRole("listbox");
  return within(listbox)
    .queryAllByRole("option")
    .map((el) => el.getAttribute("aria-label") ?? "");
}

/**
 * Clicks a directory option by name.
 *
 * @param user - The userEvent instance.
 * @param name - The accessible name of the directory option.
 */
async function clickDirectory(user: ReturnType<typeof userEvent.setup>, name: string) {
  const listbox = screen.getByRole("listbox");
  const option = within(listbox).getByRole("option", { name });
  await user.click(option);
}

////////////////////////////////////////////////////////////////
// Tests
////////////////////////////////////////////////////////////////

describe("MoveStudyDialog", () => {
  describe("rendering", () => {
    test("opens explorer at the study's current directory for a single study", () => {
      const studies = [makeStudy({ id: "s1", directoryId: "a" })];

      renderDialog({ studies });

      // Explorer shows children of directoryA
      expect(getDirectoryNames()).toEqual(["subA1", "subA2"]);

      // Breadcrumbs include directoryA
      expect(screen.getByRole("button", { name: "directoryA" })).toBeInTheDocument();
    });
  });

  describe("submit button state", () => {
    test("disabled when destination has not changed (single study in non-root directory)", () => {
      const studies = [makeStudy({ id: "s1", directoryId: "a" })];
      renderDialog({ studies });

      expect(getSubmitButton()).toBeDisabled();
    });

    test("enabled immediately when studies come from different directories", () => {
      const studies = [
        makeStudy({ id: "s1", directoryId: "a" }),
        makeStudy({ id: "s2", directoryId: "b" }),
      ];
      renderDialog({ studies });

      expect(getSubmitButton()).not.toBeDisabled();
    });

    test("becomes enabled after navigating to a different directory", async () => {
      const user = userEvent.setup();
      const studies = [makeStudy({ id: "s1", directoryId: "a" })];
      renderDialog({ studies });

      expect(getSubmitButton()).toBeDisabled();

      // Change directory from "directoryA" to "directoryA/subA2"
      await clickDirectory(user, "subA2");

      await waitFor(() => {
        expect(getSubmitButton()).not.toBeDisabled();
      });
    });
  });

  describe("successful move", () => {
    test("skips directory refetch for existing directory", async () => {
      const user = userEvent.setup();
      const studies = [
        makeStudy({ id: "s1", name: "Study 1", directoryId: "a" }),
        makeStudy({ id: "s2", name: "Study 2", directoryId: "b" }),
      ];
      const { onClose } = renderDialog({ studies });

      // Submit immediately (allowSubmitOnPristine = true, destination is root "")
      await user.click(getSubmitButton());

      await waitFor(() => {
        expect(mockMoveStudy).toHaveBeenCalledTimes(2);
      });

      expect(mockMoveStudy).toHaveBeenCalledWith("s1", "");
      expect(mockMoveStudy).toHaveBeenCalledWith("s2", "");

      // No directory refetch needed destination is an existing directory (no newDirectoryPath)
      expect(mockGetDirectories).not.toHaveBeenCalled();

      await waitFor(() => {
        expect(onClose).toHaveBeenCalledTimes(1);
      });

      expect(mockEnqueueSnackbar).toHaveBeenCalledWith(
        "studies.success.moveStudies",
        expect.objectContaining({ variant: "success" }),
      );
    });

    test("moves studies to a navigated directory", async () => {
      const user = userEvent.setup();
      const studies = [makeStudy({ id: "s1", directoryId: "b" })];
      const { onClose } = renderDialog({ studies });

      // Initial explorer is at directoryB navigate to root first
      await user.click(screen.getByRole("button", { name: "root" }));

      // Navigate into directoryA > subA2
      await clickDirectory(user, "directoryA");
      await clickDirectory(user, "subA2");

      await waitFor(() => {
        expect(getSubmitButton()).not.toBeDisabled();
      });

      await user.click(getSubmitButton());

      await waitFor(() => {
        expect(mockMoveStudy).toHaveBeenCalledWith("s1", "directoryA/subA2");
      });

      await waitFor(() => {
        expect(onClose).toHaveBeenCalled();
      });
    });

    test("moves sequentially so the first call can create a new directory for subsequent calls", async () => {
      const user = userEvent.setup();

      // Track call order
      const callOrder: string[] = [];
      mockMoveStudy.mockImplementation(
        (id: string) =>
          new Promise<void>((resolve) => {
            callOrder.push(id);
            setTimeout(resolve, 10);
          }),
      );

      const studies = [
        makeStudy({ id: "s1", directoryId: "a" }),
        makeStudy({ id: "s2", directoryId: "b" }),
        makeStudy({ id: "s3", directoryId: "c" }),
      ];
      renderDialog({ studies });

      await user.click(getSubmitButton());

      await waitFor(() => {
        expect(mockMoveStudy).toHaveBeenCalledTimes(3);
      });

      // Calls happen in study order (sequential, not parallel)
      expect(callOrder).toEqual(["s1", "s2", "s3"]);
    });
  });

  describe("partial failure", () => {
    test("shows both warning and success snackbars, and closes dialog", async () => {
      const user = userEvent.setup();
      const studies = [
        makeStudy({ id: "s1", name: "Study 1", directoryId: "a" }),
        makeStudy({ id: "s2", name: "Study 2", directoryId: "b" }),
        makeStudy({ id: "s3", name: "Study 3", directoryId: "c" }),
      ];

      mockMoveStudy
        .mockResolvedValueOnce(undefined)
        .mockRejectedValueOnce(new Error("API error"))
        .mockResolvedValueOnce(undefined);

      const { onClose } = renderDialog({ studies });

      await user.click(getSubmitButton());

      await waitFor(() => {
        expect(onClose).toHaveBeenCalledTimes(1);
      });

      // Warning for the failed study
      expect(mockEnqueueSnackbar).toHaveBeenCalledWith(
        "studies.warning.moveStudiesPartial",
        expect.objectContaining({ variant: "warning" }),
      );

      // Success for the 2 that succeeded
      expect(mockEnqueueSnackbar).toHaveBeenCalledWith(
        "studies.success.moveStudies",
        expect.objectContaining({ variant: "success" }),
      );

      // No directory refetch needed destination is an existing directory (no newDirectoryPath)
      expect(mockGetDirectories).not.toHaveBeenCalled();
    });
  });

  describe("total failure", () => {
    test("dialog stays open and does not fetch fresh directories when all moves fail", async () => {
      const user = userEvent.setup();
      const studies = [
        makeStudy({ id: "s1", directoryId: "a" }),
        makeStudy({ id: "s2", directoryId: "b" }),
      ];

      mockMoveStudy.mockRejectedValue(new Error("Server error"));

      const { onClose } = renderDialog({ studies });

      await user.click(getSubmitButton());

      // Wait for both move calls to complete
      await waitFor(() => {
        expect(mockMoveStudy).toHaveBeenCalledTimes(2);
      });

      // Wait for the submit error to be processed (Form shows an error snackbar)
      await waitFor(() => {
        // The submit button should be re-enabled (no longer loading)
        expect(getSubmitButton()).not.toBeDisabled();
      });

      // Dialog stays open
      expect(onClose).not.toHaveBeenCalled();

      expect(screen.getByText("studies.moveStudies")).toBeInTheDocument();

      // Do not refetch because the throw happens before fetchQuery
      expect(mockGetDirectories).not.toHaveBeenCalled();
    });
  });

  describe("redirect checkbox", () => {
    test("dispatches updateStudyFilters when redirect is checked (default)", async () => {
      const user = userEvent.setup();
      const studies = [
        makeStudy({ id: "s1", directoryId: "a" }),
        makeStudy({ id: "s2", directoryId: "b" }),
      ];
      const { onClose } = renderDialog({ studies });

      // Navigate to directoryA before submitting
      await clickDirectory(user, "directoryA");

      await waitFor(() => {
        expect(getSubmitButton()).not.toBeDisabled();
      });

      await user.click(getSubmitButton());

      await waitFor(() => {
        expect(onClose).toHaveBeenCalled();
      });

      // Verify dispatch was called with the correct redirect payload
      expect(mockDispatch).toHaveBeenCalledWith(
        expect.objectContaining({
          payload: {
            activeTree: "managed",
            managed: {
              directoryId: "a",
              directoryIds: ["a", "a1", "a2", "a2d"],
            },
          },
        }),
      );
    });

    test("dispatches with null directoryId when moving to root", async () => {
      const user = userEvent.setup();
      const studies = [
        makeStudy({ id: "s1", directoryId: "a" }),
        makeStudy({ id: "s2", directoryId: "b" }),
      ];
      const { onClose } = renderDialog({ studies });

      // Destination is already root (""), submit immediately
      await user.click(getSubmitButton());

      await waitFor(() => {
        expect(onClose).toHaveBeenCalled();
      });

      expect(mockDispatch).toHaveBeenCalledWith(
        expect.objectContaining({
          payload: {
            activeTree: "managed",
            managed: {
              directoryId: null,
              directoryIds: null,
            },
          },
        }),
      );
    });
  });
});
