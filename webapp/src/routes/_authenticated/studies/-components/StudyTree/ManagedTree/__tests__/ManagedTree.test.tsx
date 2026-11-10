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

import studiesReducer, { requestStudyFolderReveal } from "@/redux/ducks/studies";
import { directoryQueries } from "@/queries/directories/queries";
import { createDirectory, getDirectories } from "@/services/api/directories";
import { deferred } from "@/tests/queryUtils";
import { DIRECTORIES, TARGET_FOLDER } from "./fixtures";
import type { Directory } from "@/services/api/directories/types";
import { createTheme, ThemeProvider } from "@mui/material";
import { configureStore } from "@reduxjs/toolkit";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Suspense, useState } from "react";
import { Provider } from "react-redux";
import ManagedTree from "..";

const { enqueueErrorSnackbar, translate } = vi.hoisted(() => ({
  enqueueErrorSnackbar: vi.fn(),
  translate: (key: string) => key,
}));

vi.mock("@/redux/store", () => ({ default: { dispatch: vi.fn() } }));
vi.mock("@/services/api/directories", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/services/api/directories")>()),
  createDirectory: vi.fn(),
  getDirectories: vi.fn(),
}));
vi.mock("@/hooks/useEnqueueErrorSnackbar", () => ({ default: () => enqueueErrorSnackbar }));
vi.mock("react-i18next", async (importOriginal) => ({
  ...(await importOriginal<typeof import("react-i18next")>()),
  useTranslation: () => ({ t: translate }),
}));
vi.mock("@/routes/-shared/components/studies/FavoriteToggle/FavoriteDirectoryToggle", () => ({
  default: () => null,
}));

const theme = createTheme({ cssVariables: true });

function treeItem(name: string) {
  return screen.getByText(name).closest('[role="treeitem"]');
}

function CreationHarness({ initiallyCreating }: { initiallyCreating: boolean }) {
  const [isCreatingDirectory, setIsCreatingDirectory] = useState(initiallyCreating);

  return (
    <>
      <button onClick={() => setIsCreatingDirectory(true)}>New folder</button>
      <ManagedTree
        isCreatingDirectory={isCreatingDirectory}
        onDirectoryCreated={() => setIsCreatingDirectory(false)}
        onRootClick={vi.fn()}
      />
    </>
  );
}

function setup({
  directoryId = null,
  cachedDirectories,
  initiallyCreating = false,
}: {
  directoryId?: string | null;
  cachedDirectories?: Directory[];
  initiallyCreating?: boolean;
} = {}) {
  const store = configureStore({ reducer: { studies: studiesReducer } });
  store.dispatch(
    requestStudyFolderReveal({
      tree: "managed",
      directoryId,
      directoryIds: directoryId ? [directoryId] : null,
    }),
  );
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  if (cachedDirectories) {
    queryClient.setQueryData(directoryQueries.list().queryKey, cachedDirectories, {
      updatedAt: Date.now() - 60_000,
    });
  }

  render(
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <Suspense fallback="Loading">
            <CreationHarness initiallyCreating={initiallyCreating} />
          </Suspense>
        </ThemeProvider>
      </QueryClientProvider>
    </Provider>,
  );

  return store;
}

function setupDirectoryRefresh() {
  const response = deferred<Directory[]>();
  vi.mocked(getDirectories).mockReturnValue(response.promise);
  const store = setup({ directoryId: "target", cachedDirectories: [] });

  return {
    store,
    finish: (value: Directory[]) => {
      response.resolve(value);
      return response.promise;
    },
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getDirectories).mockResolvedValue(DIRECTORIES);
});

test("reveals a nested favorite repeatedly without collapsing an unrelated branch", async () => {
  const user = userEvent.setup();
  const store = setup();

  await user.click(await screen.findByText("Other"));

  expect(treeItem("Other")).toHaveAttribute("aria-expanded", "true");

  const reveal = () => store.dispatch(requestStudyFolderReveal(TARGET_FOLDER));

  act(() => {
    reveal();
  });

  await waitFor(() => expect(treeItem("Target")).toHaveAttribute("aria-checked", "true"));
  expect(treeItem("Parent")).toHaveAttribute("aria-expanded", "true");
  expect(treeItem("Target")).toHaveAttribute("aria-expanded", "true");
  expect(treeItem("Other")).toHaveAttribute("aria-expanded", "true");
  expect(screen.getByText("Child")).toBeVisible();

  await user.click(screen.getByText("Target"));

  expect(treeItem("Target")).toHaveAttribute("aria-expanded", "false");

  act(() => {
    reveal();
  });

  await waitFor(() => expect(treeItem("Target")).toHaveAttribute("aria-expanded", "true"));
  expect(treeItem("Other")).toHaveAttribute("aria-expanded", "true");
});

test("reveals a target absent from stale data once the directory refresh finds it", async () => {
  const { store, finish } = setupDirectoryRefresh();

  await waitFor(() => expect(getDirectories).toHaveBeenCalledOnce());
  expect(enqueueErrorSnackbar).not.toHaveBeenCalled();
  expect(store.getState().studies.folderRevealRequest).toMatchObject({
    tree: "managed",
    directoryId: "target",
  });

  await act(async () => {
    await finish(DIRECTORIES);
  });

  await screen.findByText("Target");
  expect(treeItem("Target")).toHaveAttribute("aria-checked", "true");
  expect(treeItem("Target")).toHaveAttribute("aria-expanded", "true");
  expect(enqueueErrorSnackbar).not.toHaveBeenCalled();
});

test("waits for the directory refresh to confirm that the target is missing", async () => {
  const { store, finish } = setupDirectoryRefresh();

  await waitFor(() => expect(getDirectories).toHaveBeenCalledOnce());
  expect(enqueueErrorSnackbar).not.toHaveBeenCalled();
  expect(store.getState().studies.folderRevealRequest).not.toBeNull();

  await act(async () => {
    await finish([]);
  });

  await waitFor(() => expect(store.getState().studies.folderRevealRequest).toBeNull());
  expect(enqueueErrorSnackbar.mock.calls).toEqual([
    ["studies.tree.error.folderUnavailable", "target"],
  ]);
});

test("does not report the managed root as missing when there are no directories", async () => {
  vi.mocked(getDirectories).mockResolvedValue([]);
  const store = setup();

  await screen.findByText("studies.tree.noDirectories");
  expect(enqueueErrorSnackbar).not.toHaveBeenCalled();
  expect(store.getState().studies.folderRevealRequest).toMatchObject({
    tree: "managed",
    directoryId: null,
  });
});

test.each([true, false])(
  "preserves the creation draft during tree updates (creating on mount: %s)",
  async (initiallyCreating) => {
    const user = userEvent.setup();
    const store = setup({ initiallyCreating });

    if (!initiallyCreating) {
      await screen.findByText("Parent");
      await user.click(screen.getByRole("button", { name: "New folder" }));
    }

    const input = await screen.findByRole("textbox");
    await waitFor(() => expect(input).toHaveFocus());

    await user.type(input, "New folder");
    act(() => {
      store.dispatch(requestStudyFolderReveal(TARGET_FOLDER));
    });

    await waitFor(() => expect(treeItem("Target")).toHaveAttribute("aria-checked", "true"));
    expect(input).toHaveValue("New folder");

    await user.type(input, " draft");

    expect(input).toHaveValue("New folder draft");

    await user.keyboard("{Escape}");

    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(createDirectory).not.toHaveBeenCalled();
  },
);
