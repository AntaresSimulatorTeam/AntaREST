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
import storage, { StorageKey } from "@/services/utils/localStorage";
import type { StudyMetadata } from "@/types/types";
import { deferred } from "@/tests/queryUtils";
import { externalStudy, folder, FOLDERS_BY_PATH } from "./fixtures";
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

function setup(studies: StudyMetadata[] = [], initialPath?: string) {
  const store = configureStore({ reducer: { studies: studiesReducer } });

  if (initialPath) {
    store.dispatch(requestStudyFolderReveal({ tree: "external", path: initialPath }));
  }

  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: 60_000 } },
  });

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
  vi.mocked(getFolders).mockImplementation((_workspace, path) => {
    if (path === "") {
      return Promise.resolve([folder("Target", "/workspace"), folder("Other", "/workspace")]);
    }

    if (path === "Target") {
      return Promise.resolve([folder("Child", "/workspace/Target")]);
    }

    if (path === "Other") {
      return Promise.resolve([folder("Keep", "/workspace/Other")]);
    }

    return Promise.resolve([]);
  });
});

afterEach(() => vi.restoreAllMocks());

test("loads an absent favorite from its workspace through its children before revealing it", async () => {
  vi.mocked(getFolders).mockImplementation((_workspace, path) =>
    Promise.resolve(FOLDERS_BY_PATH[path] ?? []),
  );

  setup([], "/workspace/Projects/Target");

  await screen.findByText("Child");
  expect(treeItem("Projects")).toHaveAttribute("aria-expanded", "true");
  expect(treeItem("Target")).toHaveAttribute("aria-expanded", "true");
  expect(treeItem("Target")).toHaveAttribute("aria-checked", "true");
  expect(getFolders).toHaveBeenCalledWith("workspace", "");
  expect(getFolders).toHaveBeenCalledWith("workspace", "Projects");
  expect(getFolders).toHaveBeenCalledWith("workspace", "Projects/Target");
});

test("reopens the same favorite after collapse and preserves another expanded branch", async () => {
  const user = userEvent.setup();
  const store = setup(
    [externalStudy("Other/Keep/Study"), externalStudy("Target/Child/Study")],
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

  expect(requestId).toBeDefined();
  act(() => store.dispatch(finishStudyFolderReveal(requestId ?? "")));

  await user.click(screen.getByText("Target"));

  expect(treeItem("Target")).toHaveAttribute("aria-expanded", "false");

  act(() => {
    store.dispatch(requestStudyFolderReveal({ tree: "external", path: "/workspace/Target" }));
  });

  await waitFor(() => expect(treeItem("Target")).toHaveAttribute("aria-expanded", "true"));
  expect(treeItem("Other")).toHaveAttribute("aria-expanded", "true");
});

test("revalidates a previously explored favorite and removes its deleted cached branch", async () => {
  const cachedFolders = [
    folder("Target", "/workspace"),
    folder("Child", "/workspace/Target"),
    folder("Other", "/workspace"),
  ];
  const getItem = storage.getItem.bind(storage);
  vi.spyOn(storage, "getItem").mockImplementation((key) =>
    key === StorageKey.StudyTreeFolders ? cachedFolders : getItem(key),
  );
  const saveFolders = vi.spyOn(storage, "setItem");
  const store = setup(
    [externalStudy("Target/Child/Study"), externalStudy("Other/Keep/Study")],
    "/workspace/Target",
  );

  await screen.findByText("Child");
  await waitFor(() => expect(getFolders).toHaveBeenCalledWith("workspace", "Target"));

  const requestId = store.getState().studies.folderRevealRequest?.requestId;

  expect(requestId).toBeDefined();
  act(() => store.dispatch(finishStudyFolderReveal(requestId ?? "")));
  vi.mocked(getFolders).mockResolvedValue([folder("Other", "/workspace")]);

  act(() => {
    store.dispatch(requestStudyFolderReveal({ tree: "external", path: "/workspace/Target" }));
  });

  await waitFor(() => expect(enqueueErrorSnackbar).toHaveBeenCalledOnce());
  expect(store.getState().studies.folderRevealRequest).toBeNull();
  expect(screen.queryByText("Target")).not.toBeInTheDocument();
  expect(screen.queryByText("Child")).not.toBeInTheDocument();
  expect(screen.getByText("Other")).toBeInTheDocument();
  expect(saveFolders).toHaveBeenLastCalledWith(StorageKey.StudyTreeFolders, [
    folder("Other", "/workspace"),
  ]);
});

test("does not apply a delayed folder response after the reveal is cancelled", async () => {
  const response = deferred<Array<ReturnType<typeof folder>>>();
  vi.mocked(getFolders).mockReturnValueOnce(response.promise);

  const store = setup([], "/workspace/Target");
  await waitFor(() => expect(getFolders).toHaveBeenCalledOnce());
  const requestId = store.getState().studies.folderRevealRequest?.requestId;

  expect(requestId).toBeDefined();
  act(() => store.dispatch(finishStudyFolderReveal(requestId ?? "")));

  await act(() => response.resolve([folder("Target", "/workspace")]));

  expect(screen.queryByText("Target")).not.toBeInTheDocument();
  expect(getFolders).toHaveBeenCalledOnce();
});

test("loads children on the next reveal after cancelling a target-child response", async () => {
  const children = [folder("New child", "/workspace/Target")];
  const response = deferred<typeof children>();
  let pending = true;
  vi.mocked(getFolders).mockImplementation((_workspace, path) => {
    if (path === "") {
      return Promise.resolve([folder("Target", "/workspace")]);
    }

    return pending ? response.promise : Promise.resolve(children);
  });

  const store = setup([externalStudy("Target/Study")], "/workspace/Target");
  await waitFor(() => expect(getFolders).toHaveBeenCalledWith("workspace", "Target"));
  const requestId = store.getState().studies.folderRevealRequest?.requestId;

  expect(requestId).toBeDefined();
  act(() => store.dispatch(finishStudyFolderReveal(requestId ?? "")));

  await act(() => response.resolve(children));
  pending = false;

  expect(screen.queryByText("New child")).not.toBeInTheDocument();

  act(() => {
    store.dispatch(requestStudyFolderReveal({ tree: "external", path: "/workspace/Target" }));
  });

  await screen.findByText("New child");
  expect(treeItem("Target")).toHaveAttribute("aria-checked", "true");
  expect(treeItem("Target")).toHaveAttribute("aria-expanded", "true");
});
