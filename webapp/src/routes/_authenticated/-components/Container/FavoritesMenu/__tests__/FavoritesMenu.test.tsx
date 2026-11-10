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

import type { Directory } from "@/services/api/directories/types";
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
  RouterProvider,
} from "@tanstack/react-router";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import FavoritesMenu from "..";
import type { Favorite } from "../types";

const mocks = vi.hoisted(() => ({
  dispatch: vi.fn(),
  isMenuOpen: true,
  favorites: [] as Favorite[],
  directories: [] as Directory[],
}));

vi.mock("../useFavorites", () => ({ default: () => mocks.favorites }));
vi.mock("@/redux/hooks/useAppDispatch", () => ({ default: () => mocks.dispatch }));
vi.mock("@/redux/hooks/useAppSelector", () => ({
  default: (selector: () => unknown) => selector(),
}));
vi.mock("@/redux/selectors", () => ({
  isMenuOpen: () => mocks.isMenuOpen,
}));
vi.mock("@/redux/ducks/studies", () => ({
  requestStudyFolderReveal: (payload: unknown) => ({ type: "reveal", payload }),
}));
vi.mock("@/queries/directories/queries", () => ({ directoryQueries: { list: () => ({}) } }));
vi.mock("@tanstack/react-query", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@tanstack/react-query")>()),
  useSuspenseQuery: () => ({ data: mocks.directories }),
}));
vi.mock("react-i18next", async (importOriginal) => ({
  ...(await importOriginal<typeof import("react-i18next")>()),
  useTranslation: () => ({ t: (key: string) => key }),
}));
vi.mock("@/routes/-shared/components/studies/FavoriteToggle", () => ({
  default: () => <button type="button">studies.removeFavorite</button>,
}));

const favoriteStudy: Favorite = {
  id: "study-study-id",
  name: "Favorite study",
  type: "study",
  original: { studyId: "study-id", studyName: "Favorite study" },
};

async function renderFavorites() {
  const root = createRootRoute({
    component: () => (
      <>
        <FavoritesMenu />
        <Outlet />
      </>
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

  return { user, router };
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.dispatch.mockReset();

  mocks.isMenuOpen = true;
  mocks.favorites = [favoriteStudy];
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

    expect(screen.queryByTestId("FolderOpenIcon")).not.toBeInTheDocument();

    await user.click(screen.getByText("Favorite study"));

    await waitFor(() => expect(router.state.location.pathname).toBe("/studies/study-id"));
    expect(mocks.dispatch).not.toHaveBeenCalled();
  },
);

test("keyboard users can reach the popup action and return to the favorite", async () => {
  mocks.isMenuOpen = false;
  const { user } = await renderFavorites();
  const item = screen.getByRole("menuitem");
  const action = screen.getByRole("button", { name: "studies.removeFavorite" });

  expect(item).toHaveFocus();

  await user.tab();

  expect(action).toHaveFocus();

  await user.tab({ shift: true });

  expect(item).toHaveFocus();

  await user.tab();

  expect(action).toHaveFocus();
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
