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

const directories: Directory[] = [
  { id: "other", name: "Other", parentId: null },
  { id: "keep", name: "Keep", parentId: "other" },
  { id: "parent", name: "Parent", parentId: null },
  { id: "target", name: "Target", parentId: "parent" },
  { id: "child", name: "Child", parentId: "target" },
];

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
        <ThemeProvider theme={createTheme({ cssVariables: true })}>
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
  let resolveDirectories: (value: Directory[]) => void = () => undefined;
  const pending = new Promise<Directory[]>((resolve) => {
    resolveDirectories = resolve;
  });
  vi.mocked(getDirectories).mockReturnValue(pending);
  const store = setup({ directoryId: "target", cachedDirectories: [] });

  return {
    store,
    finish: (value: Directory[]) => {
      resolveDirectories(value);
      return pending;
    },
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getDirectories).mockResolvedValue(directories);
});

test("reveals a nested favorite repeatedly without collapsing an unrelated branch", async () => {
  const user = userEvent.setup();
  const store = setup();

  await user.click(await screen.findByText("Other"));

  expect(treeItem("Other")).toHaveAttribute("aria-expanded", "true");

  const reveal = () =>
    store.dispatch(
      requestStudyFolderReveal({
        tree: "managed",
        directoryId: "target",
        directoryIds: ["target", "child"],
      }),
    );

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
    await finish(directories);
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

test("starts creation on mount and preserves the draft while tree selection changes", async () => {
  const user = userEvent.setup();
  const store = setup({ initiallyCreating: true });
  const input = await screen.findByRole("textbox");
  await waitFor(() => expect(input).toHaveFocus());

  await user.type(input, "New folder");
  act(() => {
    store.dispatch(
      requestStudyFolderReveal({
        tree: "managed",
        directoryId: "target",
        directoryIds: ["target", "child"],
      }),
    );
  });

  await waitFor(() => expect(treeItem("Target")).toHaveAttribute("aria-checked", "true"));
  expect(input).toHaveValue("New folder");

  await user.type(input, " draft");

  expect(input).toHaveValue("New folder draft");

  await user.keyboard("{Escape}");

  expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  expect(createDirectory).not.toHaveBeenCalled();
});

test("starts creation after mount and saves a fresh draft after cancelling and reopening", async () => {
  const user = userEvent.setup();
  vi.mocked(createDirectory).mockResolvedValue({
    id: "created",
    name: "Saved folder",
    parentId: null,
  });
  setup();
  await screen.findByText("Parent");

  expect(screen.queryByRole("textbox")).not.toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "New folder" }));
  const firstInput = await screen.findByRole("textbox");
  await waitFor(() => expect(firstInput).toHaveFocus());
  await user.type(firstInput, "Discarded draft{Escape}");

  expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  expect(createDirectory).not.toHaveBeenCalled();

  await user.click(screen.getByRole("button", { name: "New folder" }));
  const reopenedInput = await screen.findByRole("textbox");
  await waitFor(() => expect(reopenedInput).toHaveFocus());

  expect(reopenedInput).toHaveValue("");

  await user.type(reopenedInput, "Saved folder{Enter}");

  await screen.findByText("Saved folder");
  await waitFor(() => expect(screen.queryByRole("textbox")).not.toBeInTheDocument());
  expect(vi.mocked(createDirectory).mock.calls.map(([params]) => params)).toEqual([
    { name: "Saved folder", parentId: null },
  ]);
  expect(enqueueErrorSnackbar).not.toHaveBeenCalled();
});
