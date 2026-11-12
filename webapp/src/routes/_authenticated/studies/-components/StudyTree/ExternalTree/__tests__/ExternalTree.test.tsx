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

import { useAppMode } from "@/hooks/useAppMode";
import { finishStudyFolderReveal, requestStudyFolderReveal } from "@/redux/ducks/studies";
import { getWorkspaceDiskUsage } from "@/services/api/filesystem";
import { getFolders, getWorkspaces } from "@/services/api/study";
import storage, { StorageKey } from "@/services/utils/localStorage";
import { deferred } from "@/tests/queryUtils";
import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  DISK_USAGE,
  externalStudy,
  folder,
  FOLDERS_BY_PATH,
  FULL_DISK_USAGE,
  WORKSPACE,
} from "./fixtures";
import { renderExternalTree, treeItem } from "./utils";

const { enqueueErrorSnackbar, translate } = vi.hoisted(() => ({
  enqueueErrorSnackbar: vi.fn(),
  translate: (key: string, values?: Record<string, string>) =>
    key === "studies.tree.diskUsage.workspaceLabel" ? `Storage ${values?.workspace}` : key,
}));

vi.mock("@/redux/store", () => ({ default: { dispatch: vi.fn() } }));
vi.mock("@/hooks/useAppMode", () => ({ useAppMode: vi.fn() }));
vi.mock("@/services/api/filesystem", () => ({ getWorkspaceDiskUsage: vi.fn() }));
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
  useTranslation: () => Object.assign([translate], { t: translate, i18n: { language: "en" } }),
}));
vi.mock(
  "@/routes/-shared/components/studies/FavoriteToggle/FavoriteExternalDirectoryToggle",
  () => ({
    default: () => null,
  }),
);

beforeEach(() => {
  vi.clearAllMocks();
  window.localStorage?.clear();
  vi.mocked(useAppMode).mockReturnValue({ isWebMode: true, isDesktopMode: false });
  vi.mocked(getWorkspaceDiskUsage).mockResolvedValue(DISK_USAGE);
  vi.mocked(getWorkspaces).mockResolvedValue([WORKSPACE]);
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

  renderExternalTree({ initialPath: "/workspace/Projects/Target" });

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
  const store = renderExternalTree({
    studies: [externalStudy("Other/Keep/Study"), externalStudy("Target/Child/Study")],
    initialPath: "/workspace/Target",
  });
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
  const store = renderExternalTree({
    studies: [externalStudy("Target/Child/Study"), externalStudy("Other/Keep/Study")],
    initialPath: "/workspace/Target",
  });

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

  const store = renderExternalTree({ initialPath: "/workspace/Target" });
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

  const store = renderExternalTree({
    studies: [externalStudy("Target/Study")],
    initialPath: "/workspace/Target",
  });
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

test("shows each workspace's own usage without adding indicators to nested folders", async () => {
  const user = userEvent.setup();
  vi.mocked(getFolders).mockImplementation((_workspace, path) =>
    Promise.resolve(path === "" ? [folder("Projects", "/workspace")] : []),
  );
  vi.mocked(getWorkspaceDiskUsage).mockImplementation((workspace) =>
    Promise.resolve(workspace === WORKSPACE.name ? DISK_USAGE : FULL_DISK_USAGE),
  );

  renderExternalTree({
    studies: [
      externalStudy("Projects/Study"),
      externalStudy("Archive/Study", { workspace: "second" }),
    ],
  });

  expect(await screen.findByRole("progressbar", { name: "Storage workspace" })).toHaveAttribute(
    "aria-valuenow",
    "40",
  );
  expect(await screen.findByRole("progressbar", { name: "Storage second" })).toHaveAttribute(
    "aria-valuenow",
    "90",
  );

  await user.click(screen.getByText("workspace"));
  await user.click(await screen.findByText("Projects"));

  expect(screen.getAllByRole("progressbar")).toHaveLength(2);
});

test("does not request workspace storage in desktop mode", async () => {
  vi.mocked(useAppMode).mockReturnValue({ isWebMode: false, isDesktopMode: true });

  renderExternalTree({ studies: [externalStudy("Projects/Study")] });

  await screen.findByText("workspace");

  expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  expect(getWorkspaceDiskUsage).not.toHaveBeenCalled();
});

test("storage interactions do not select a workspace or collapse its folders", async () => {
  const user = userEvent.setup();
  const folders = deferred<Awaited<ReturnType<typeof getFolders>>>();
  vi.mocked(getFolders).mockReturnValueOnce(folders.promise);

  const store = renderExternalTree({ studies: [externalStudy("Projects/Study")] });
  await screen.findByRole("progressbar", { name: "Storage workspace" });

  await user.click(screen.getByText("workspace"));
  await user.click(screen.getByText("Projects"));

  const progress = screen.getByRole("progressbar", { name: "Storage workspace" });

  await user.dblClick(progress);
  await user.keyboard("{Enter} {ArrowLeft}{ArrowRight}{ArrowDown}");
  await act(() => folders.resolve([folder("Projects", "/workspace")]));

  expect(progress.closest("[tabindex]")).toHaveFocus();
  expect(treeItem("workspace")).toHaveAttribute("aria-expanded", "true");

  await user.click(await screen.findByRole("tooltip"));

  expect(store.getState().studies.filters.external.path).toBe("/workspace/Projects");
});
