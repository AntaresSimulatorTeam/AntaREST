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

import studiesReducer, {
  finishStudyFolderReveal,
  requestStudyFolderReveal,
} from "@/redux/ducks/studies";
import { getFolders, getWorkspaces } from "@/services/api/study";
import { StorageMode, StudyType, type StudyMetadata } from "@/types/types";
import { createTheme, ThemeProvider } from "@mui/material";
import { configureStore } from "@reduxjs/toolkit";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Provider } from "react-redux";
import ExternalTree from "..";

const { enqueueErrorSnackbar, translate } = vi.hoisted(() => ({
  enqueueErrorSnackbar: vi.fn(),
  translate: (key: string) => key,
}));

vi.mock("@/redux/store", () => ({ default: { dispatch: vi.fn() } }));
vi.mock("@/services/api/study", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/services/api/study")>()),
  getFolders: vi.fn(),
  getWorkspaces: vi.fn(),
}));
vi.mock("@/hooks/useEnqueueErrorSnackbar", () => ({
  default: () => enqueueErrorSnackbar,
}));
vi.mock("react-i18next", async (importOriginal) => ({
  ...(await importOriginal<typeof import("react-i18next")>()),
  useTranslation: () => Object.assign([translate], { t: translate }),
}));
vi.mock(
  "@/routes/-shared/components/studies/FavoriteToggle/FavoriteExternalDirectoryToggle",
  () => ({
    default: () => null,
  }),
);

const theme = createTheme({ cssVariables: true });

function makeStudy(folder: string): StudyMetadata {
  return {
    id: folder,
    name: folder,
    folder,
    workspace: "workspace",
    managed: false,
    creationDate: "2026-10-30",
    modificationDate: "2026-10-30",
    owner: { name: "Owner" },
    editor: "",
    author: "",
    type: StudyType.RAW,
    version: "9.3",
    archived: false,
    storageMode: StorageMode.FILESYSTEM,
    groups: [],
    publicMode: "READ",
  };
}

function folder(name: string, parentPath: string) {
  return {
    name,
    path: [parentPath.replace(/^\/workspace\/?/, ""), name].filter(Boolean).join("/"),
    parentPath,
    workspace: "workspace",
    hasChildren: true,
  };
}

function setup(studies: StudyMetadata[] = [], initialPath?: string) {
  const store = configureStore({ reducer: { studies: studiesReducer } });

  if (initialPath) {
    store.dispatch(requestStudyFolderReveal({ tree: "external", path: initialPath }));
  }

  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  render(
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <ExternalTree studies={studies} onRootClick={vi.fn()} />
        </ThemeProvider>
      </QueryClientProvider>
    </Provider>,
  );

  return store;
}

function treeItem(name: string) {
  return screen.getByText(name).closest('[role="treeitem"]');
}

beforeEach(() => {
  vi.clearAllMocks();
  window.localStorage?.clear();
  vi.mocked(getWorkspaces).mockResolvedValue([{ name: "workspace", diskName: "" }]);
  vi.mocked(getFolders).mockResolvedValue([]);
});

test("loads an absent favorite from its workspace through its children before revealing it", async () => {
  const foldersByPath: Record<string, Array<ReturnType<typeof folder>>> = {
    "": [folder("Projects", "/workspace")],
    Projects: [folder("Target", "/workspace/Projects")],
    "Projects/Target": [folder("Child", "/workspace/Projects/Target")],
  };
  vi.mocked(getFolders).mockImplementation((_workspace, path) =>
    Promise.resolve(foldersByPath[path] ?? []),
  );

  setup([], "/workspace/Projects/Target");

  await screen.findByText("Child");
  expect(treeItem("Projects")).toHaveAttribute("aria-expanded", "true");
  expect(treeItem("Target")).toHaveAttribute("aria-expanded", "true");
  expect(treeItem("Target")).toHaveAttribute("aria-checked", "true");
  expect(getFolders).toHaveBeenNthCalledWith(1, "workspace", "");
  expect(getFolders).toHaveBeenNthCalledWith(2, "workspace", "Projects");
  expect(getFolders).toHaveBeenNthCalledWith(3, "workspace", "Projects/Target");
  expect(getFolders).toHaveBeenCalledTimes(3);
});

test("reopens the same favorite after collapse and preserves another expanded branch", async () => {
  const user = userEvent.setup();
  const store = setup(
    [makeStudy("Other/Keep/Study"), makeStudy("Target/Child/Study")],
    "/workspace/Target",
  );
  await screen.findByText("Child");

  await user.click(screen.getByText("Other"));

  expect(treeItem("Other")).toHaveAttribute("aria-expanded", "true");

  act(() => {
    store.dispatch(requestStudyFolderReveal({ tree: "external", path: "/workspace/Target" }));
  });

  await waitFor(() => expect(treeItem("Target")).toHaveAttribute("aria-checked", "true"));

  const requestId = store.getState().studies.folderRevealRequest?.requestId;

  if (requestId) {
    act(() => store.dispatch(finishStudyFolderReveal(requestId)));
  }

  await user.click(screen.getByText("Target"));

  expect(treeItem("Target")).toHaveAttribute("aria-expanded", "false");

  act(() => {
    store.dispatch(requestStudyFolderReveal({ tree: "external", path: "/workspace/Target" }));
  });

  await waitFor(() => expect(treeItem("Target")).toHaveAttribute("aria-expanded", "true"));
  expect(treeItem("Other")).toHaveAttribute("aria-expanded", "true");
});

test("reports a folder that is no longer in its parent and finishes the reveal request", async () => {
  const store = setup([], "/workspace/Missing");

  await waitFor(() => expect(enqueueErrorSnackbar).toHaveBeenCalledOnce());
  expect(store.getState().studies.folderRevealRequest).toBeNull();
  expect(screen.queryByText("Missing")).not.toBeInTheDocument();
});

test("does not apply a delayed folder response after the reveal is cancelled", async () => {
  let resolveFolders: (folders: Array<ReturnType<typeof folder>>) => void = () => undefined;
  vi.mocked(getFolders).mockReturnValueOnce(
    new Promise((resolve) => {
      resolveFolders = resolve;
    }),
  );

  const store = setup([], "/workspace/Target");
  await waitFor(() => expect(getFolders).toHaveBeenCalledOnce());
  const requestId = store.getState().studies.folderRevealRequest?.requestId;

  if (requestId) {
    act(() => store.dispatch(finishStudyFolderReveal(requestId)));
  }

  await act(() => resolveFolders([folder("Target", "/workspace")]));

  expect(screen.queryByText("Target")).not.toBeInTheDocument();
  expect(getFolders).toHaveBeenCalledOnce();
});

test("loads children on the next reveal after cancelling a target-child response", async () => {
  const children = [folder("New child", "/workspace/Target")];
  let resolveFolders: (folders: typeof children) => void = () => undefined;
  vi.mocked(getFolders)
    .mockReturnValueOnce(
      new Promise((resolve) => {
        resolveFolders = resolve;
      }),
    )
    .mockResolvedValue(children);

  const store = setup([makeStudy("Target/Study")], "/workspace/Target");
  await waitFor(() => expect(getFolders).toHaveBeenCalledWith("workspace", "Target"));
  const requestId = store.getState().studies.folderRevealRequest?.requestId;

  if (requestId) {
    act(() => store.dispatch(finishStudyFolderReveal(requestId)));
  }

  await act(() => resolveFolders(children));

  expect(screen.queryByText("New child")).not.toBeInTheDocument();

  act(() => {
    store.dispatch(requestStudyFolderReveal({ tree: "external", path: "/workspace/Target" }));
  });

  await screen.findByText("New child");
  expect(treeItem("Target")).toHaveAttribute("aria-checked", "true");
  expect(treeItem("Target")).toHaveAttribute("aria-expanded", "true");
});
