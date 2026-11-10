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
import { DIRECTORIES, FAVORITE_STUDY, FOLDER_CASES } from "./fixtures";

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

async function renderFavorites({ expanded = true, favorites = [FAVORITE_STUDY] } = {}) {
  mocks.isMenuOpen = expanded;
  mocks.favorites = favorites;
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
  await screen.findByText(favorites[0].name);

  return { user, router };
}

beforeEach(() => {
  mocks.dispatch.mockReset();
  mocks.directories = DIRECTORIES;
});

afterEach(() => {
  vi.restoreAllMocks();
});

test.each([true, false])(
  "primary favorite opens the study (expanded sidebar: %s)",
  async (expanded) => {
    const { user, router } = await renderFavorites({ expanded });

    await user.click(screen.getByText(FAVORITE_STUDY.name));

    await waitFor(() => expect(router.state.location.pathname).toBe("/studies/study-id"));
    expect(mocks.dispatch).not.toHaveBeenCalled();
  },
);

test("custom keyboard navigation reaches actions and returns to favorite rows", async () => {
  const folder = FOLDER_CASES[0].favorite;
  const { user } = await renderFavorites({
    expanded: false,
    favorites: [FAVORITE_STUDY, folder],
  });
  const studyItem = screen.getByRole("menuitem", { name: new RegExp(FAVORITE_STUDY.name) });

  await user.tab();

  expect(screen.getAllByRole("button", { name: "studies.removeFavorite" })[0]).toHaveFocus();

  await user.tab({ shift: true });

  expect(studyItem).toHaveFocus();

  await user.tab();
  await user.keyboard("{ArrowDown}");

  expect(screen.getByRole("menuitem", { name: new RegExp(folder.name) })).toHaveFocus();
});

test.each(FOLDER_CASES)(
  "folder favorites reveal their location in the Explorer ($favorite.type)",
  async ({ favorite, target }) => {
    const { user, router } = await renderFavorites({ favorites: [favorite] });

    await user.click(screen.getByText(favorite.name));

    await waitFor(() => expect(router.state.location.pathname).toBe("/studies"));
    expect(mocks.dispatch).toHaveBeenCalledWith({ type: "reveal", payload: target });
  },
);
