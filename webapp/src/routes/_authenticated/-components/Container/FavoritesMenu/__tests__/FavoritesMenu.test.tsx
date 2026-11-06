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

import type { StudyFilters, StudyFolder } from "@/redux/ducks/studies";
import type { Directory } from "@/services/api/directories/types";
import { StorageMode, StudyType, type StudyMetadata } from "@/types/types";
import { configureStore, createAction } from "@reduxjs/toolkit";
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
  RouterProvider,
} from "@tanstack/react-router";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Provider } from "react-redux";
import FavoritesMenu from "..";
import type { Favorite } from "../types";

type ExplorerFilters = Pick<StudyFilters, "activeTree" | "managed" | "external">;

const mocks = vi.hoisted(() => ({
  dispatch: vi.fn(),
  enqueueError: vi.fn(),
  isMenuOpen: true,
  favorites: [] as Favorite[],
  studies: {} as Record<string, StudyMetadata>,
  directories: [] as Directory[],
}));

vi.mock("../useFavorites", () => ({ default: () => mocks.favorites }));
vi.mock("@/redux/hooks/useAppDispatch", () => ({ default: () => mocks.dispatch }));
vi.mock("@/redux/selectors", () => ({
  isMenuOpen: () => mocks.isMenuOpen,
  getStudiesById: () => mocks.studies,
  getStudyFilters: (state: { filters: ExplorerFilters }) => state.filters,
}));
vi.mock("@/redux/ducks/studies", () => ({
  requestStudyFolderReveal: (payload: unknown) => ({ type: "reveal", payload }),
  setStudy: (id: string) => ({ type: "fetch-study", payload: id }),
}));
vi.mock("@/hooks/useEnqueueErrorSnackbar", () => ({ default: () => mocks.enqueueError }));
vi.mock("@/queries/directories/queries", () => ({ directoryQueries: { list: () => ({}) } }));
vi.mock("@tanstack/react-query", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@tanstack/react-query")>()),
  useSuspenseQuery: () => ({ data: mocks.directories }),
}));
vi.mock("react-i18next", async (importOriginal) => ({
  ...(await importOriginal<typeof import("react-i18next")>()),
  useTranslation: () => ({ t: (key: string) => key }),
}));
vi.mock("@/routes/-shared/components/studies/FavoriteToggle", () => ({ default: () => null }));

const favoriteStudy: Favorite = {
  id: "study-study-id",
  name: "Favorite study",
  type: "study",
  original: { studyId: "study-id", studyName: "Favorite study" },
};

const initialFilters: ExplorerFilters = {
  activeTree: "managed",
  managed: { directoryId: null, directoryIds: null, showDescendants: false, collapsed: false },
  external: { path: "", showDescendants: false, collapsed: false },
};
const updateFilters = createAction<typeof initialFilters>("test/updateFilters");

function createStudy(overrides: Partial<StudyMetadata> = {}): StudyMetadata {
  return {
    id: "study-id",
    name: "Favorite study",
    creationDate: "2026-10-30",
    modificationDate: "2026-10-30",
    owner: { id: 1, name: "Owner" },
    editor: "Editor",
    author: "Author",
    type: StudyType.RAW,
    version: "9.3",
    workspace: "default",
    managed: true,
    archived: false,
    storageMode: StorageMode.FILESYSTEM,
    groups: [],
    publicMode: "NONE",
    directoryId: "folder",
    ...overrides,
  };
}

async function renderFavorites() {
  const store = configureStore({
    reducer: {
      filters: (state = initialFilters, action) =>
        updateFilters.match(action) ? action.payload : state,
    },
  });
  const root = createRootRoute({
    component: () => (
      <Provider store={store}>
        <FavoritesMenu />
        <Outlet />
      </Provider>
    ),
  });
  const router = createRouter({
    routeTree: root.addChildren([
      createRoute({ getParentRoute: () => root, path: "/" }),
      createRoute({ getParentRoute: () => root, path: "/studies" }),
      createRoute({ getParentRoute: () => root, path: "/studies/$studyId" }),
      createRoute({ getParentRoute: () => root, path: "/tasks" }),
    ]),
    history: createMemoryHistory({ initialEntries: ["/"] }),
  });

  render(<RouterProvider router={router} />);

  const user = userEvent.setup();
  const trigger = await screen.findByRole("button", { name: "studies.favorites" });

  if (!mocks.isMenuOpen) {
    vi.spyOn(trigger, "getBoundingClientRect").mockReturnValue(new DOMRect(24, 24, 48, 48));
  }

  await user.click(trigger);
  await screen.findByText("Favorite study");

  return { user, router, store };
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.dispatch.mockReset();

  mocks.isMenuOpen = true;
  mocks.favorites = [favoriteStudy];
  mocks.studies = { "study-id": createStudy() };
  mocks.directories = [
    { id: "folder", name: "Folder", parentId: null },
    { id: "child", name: "Child", parentId: "folder" },
  ];
});

afterEach(() => {
  vi.restoreAllMocks();
});

test.each([true, false])(
  "primary favorite opens the study (expanded sidebar: %s)",
  async (expanded) => {
    mocks.isMenuOpen = expanded;
    const { user, router } = await renderFavorites();

    await user.click(screen.getByText("Favorite study"));

    await waitFor(() => expect(router.state.location.pathname).toBe("/studies/study-id"));
    expect(mocks.dispatch).not.toHaveBeenCalled();
  },
);

test.each([true, false])(
  "secondary action reveals the folder without opening the study (expanded sidebar: %s)",
  async (expanded) => {
    mocks.isMenuOpen = expanded;
    const { user, router } = await renderFavorites();

    await user.click(screen.getByRole("button", { name: "studies.showInExplorer" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/studies"));
    expect(mocks.dispatch).toHaveBeenCalledWith({
      type: "reveal",
      payload: { tree: "managed", directoryId: "folder", directoryIds: ["folder", "child"] },
    });
    await waitFor(() => expect(screen.queryByRole("menu")).not.toBeInTheDocument());
  },
);

test("fetches missing study metadata before revealing its folder", async () => {
  mocks.studies = {};
  mocks.dispatch.mockReturnValue({ unwrap: () => Promise.resolve(createStudy()) });
  const { user, router } = await renderFavorites();

  await user.click(screen.getByRole("button", { name: "studies.showInExplorer" }));

  await waitFor(() => expect(router.state.location.pathname).toBe("/studies"));
  expect(mocks.dispatch).toHaveBeenNthCalledWith(1, { type: "fetch-study", payload: "study-id" });
  expect(mocks.dispatch).toHaveBeenNthCalledWith(2, {
    type: "reveal",
    payload: { tree: "managed", directoryId: "folder", directoryIds: ["folder", "child"] },
  });
});

test("reports metadata errors without navigating to another location", async () => {
  const error = new Error("Study unavailable");
  mocks.studies = {};
  mocks.dispatch.mockReturnValue({ unwrap: () => Promise.reject(error) });
  const { user, router } = await renderFavorites();

  await user.click(screen.getByRole("button", { name: "studies.showInExplorer" }));

  expect(mocks.enqueueError).toHaveBeenCalledWith("studies.error.showInExplorer", error);
  expect(router.state.location.pathname).toBe("/");
  expect(mocks.dispatch).toHaveBeenCalledTimes(1);
});

test("reports a navigation rejection after the reveal changes the selected folder", async () => {
  const error = new Error("Navigation failed");
  let rejectNavigation: (error: Error) => void = vi.fn();
  const pendingNavigation = new Promise<void>((_resolve, reject) => {
    rejectNavigation = reject;
  });
  const { user, router, store } = await renderFavorites();

  // Inject a navigation failure: ordinary loader errors belong to the router's error boundary.
  vi.spyOn(router, "navigate").mockReturnValue(pendingNavigation);
  mocks.dispatch.mockImplementation(({ payload }: { payload: StudyFolder }) => {
    if (payload.tree === "managed") {
      store.dispatch(
        updateFilters({
          ...store.getState().filters,
          managed: { ...store.getState().filters.managed, directoryId: payload.directoryId },
        }),
      );
    }
  });

  await user.click(screen.getByRole("button", { name: "studies.showInExplorer" }));

  expect(store.getState().filters.managed.directoryId).toBe("folder");

  await act(async () => {
    rejectNavigation(error);
    await pendingNavigation.catch(() => undefined);
  });

  expect(mocks.enqueueError).toHaveBeenCalledWith("studies.error.showInExplorer", error);
  expect(screen.getByRole("button", { name: "studies.showInExplorer" })).toBeEnabled();
});

test("ignores a pending reveal after the user dismisses the Favorites popup", async () => {
  let resolveStudy: (study: StudyMetadata) => void = vi.fn();
  const pendingStudy = new Promise<StudyMetadata>((resolve) => {
    resolveStudy = resolve;
  });

  mocks.isMenuOpen = false;
  mocks.studies = {};
  mocks.dispatch.mockReturnValue({ unwrap: () => pendingStudy });
  const { user, router } = await renderFavorites();

  await user.click(screen.getByRole("button", { name: "studies.showInExplorer" }));
  act(() => screen.getByRole("menu").focus());
  await user.keyboard("{Escape}");

  await act(async () => {
    resolveStudy(createStudy());
    await pendingStudy;
  });

  expect(router.state.location.pathname).toBe("/");
  expect(mocks.dispatch).toHaveBeenCalledTimes(1);
});

test("ignores a pending reveal after navigation outside Favorites", async () => {
  let resolveStudy: (study: StudyMetadata) => void = vi.fn();
  const pendingStudy = new Promise<StudyMetadata>((resolve) => {
    resolveStudy = resolve;
  });

  mocks.studies = {};
  mocks.dispatch.mockReturnValue({ unwrap: () => pendingStudy });
  const { user, router } = await renderFavorites();

  await user.click(screen.getByRole("button", { name: "studies.showInExplorer" }));

  await act(async () => {
    await router.navigate({ to: "/tasks" });
  });

  expect(screen.getByRole("button", { name: "studies.showInExplorer" })).toBeEnabled();

  await act(async () => {
    resolveStudy(createStudy());
    await pendingStudy;
  });

  expect(router.state.location.pathname).toBe("/tasks");
  expect(mocks.dispatch).toHaveBeenCalledTimes(1);
});

test("ignores a pending reveal after the user selects another Explorer folder", async () => {
  let resolveStudy: (study: StudyMetadata) => void = vi.fn();
  const pendingStudy = new Promise<StudyMetadata>((resolve) => {
    resolveStudy = resolve;
  });

  mocks.studies = {};
  mocks.dispatch.mockReturnValue({ unwrap: () => pendingStudy });
  const { user, router, store } = await renderFavorites();

  await user.click(screen.getByRole("button", { name: "studies.showInExplorer" }));

  act(() => {
    store.dispatch(
      updateFilters({
        ...store.getState().filters,
        managed: { ...store.getState().filters.managed, directoryId: "another-folder" },
      }),
    );
  });

  await act(async () => {
    resolveStudy(createStudy());
    await pendingStudy;
  });

  expect(store.getState().filters.managed.directoryId).toBe("another-folder");
  expect(router.state.location.pathname).toBe("/");
  expect(mocks.dispatch).toHaveBeenCalledTimes(1);
  expect(screen.getByRole("button", { name: "studies.showInExplorer" })).toBeEnabled();
});

test("keyboard users can reach the popup action and return to the favorite", async () => {
  mocks.isMenuOpen = false;
  const { user, router } = await renderFavorites();
  const item = screen.getByRole("menuitem");
  const action = screen.getByRole("button", { name: "studies.showInExplorer" });

  expect(item).toHaveFocus();

  await user.tab();

  expect(action).toHaveFocus();

  await user.tab({ shift: true });

  expect(item).toHaveFocus();

  await user.tab();
  await user.keyboard("{Enter}");

  await waitFor(() => expect(router.state.location.pathname).toBe("/studies"));
});

test("Tab after the last popup action closes the menu", async () => {
  mocks.isMenuOpen = false;
  const { user } = await renderFavorites();

  await user.tab();
  await user.tab();

  await waitFor(() => expect(screen.queryByRole("menu")).not.toBeInTheDocument());
});

test("arrow navigation from a popup action moves to the next favorite", async () => {
  mocks.isMenuOpen = false;
  mocks.favorites.push({
    id: "study-second",
    name: "Second study",
    type: "study",
    original: { studyId: "second", studyName: "Second study" },
  });
  const { user } = await renderFavorites();

  await user.tab();
  await user.keyboard("{ArrowDown}");

  expect(screen.getByRole("menuitem", { name: /^Second study/ })).toHaveFocus();
});

test.each([
  {
    favorite: {
      id: "directory-folder",
      name: "Favorite folder",
      type: "directory",
      original: { directoryId: "folder", directoryName: "Favorite folder" },
    },
    target: { tree: "managed", directoryId: "folder", directoryIds: ["folder", "child"] },
  },
  {
    favorite: {
      id: "external-directory-folder",
      name: "Favorite folder",
      type: "externalDirectory",
      absolutePath: "/external/folder",
      original: { workspace: "external", path: "folder" },
    },
    target: { tree: "external", path: "/external/folder" },
  },
] satisfies Array<{ favorite: Favorite; target: unknown }>)(
  "folder favorites reveal their location in the Explorer ($favorite.type)",
  async ({ favorite, target }) => {
    mocks.favorites.push(favorite);
    const { user, router } = await renderFavorites();

    await user.click(screen.getByText("Favorite folder"));

    await waitFor(() => expect(router.state.location.pathname).toBe("/studies"));
    expect(mocks.dispatch).toHaveBeenCalledWith({ type: "reveal", payload: target });
  },
);
