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
  updateStudyFilters,
} from "../studies";

vi.mock("@/redux/store", () => ({ default: { dispatch: vi.fn() } }));

test("revealing a managed folder selects and opens its section while preserving other filters", () => {
  const initial = studiesReducer(
    undefined,
    updateStudyFilters({
      search: "scenario",
      type: "variants",
      activeTree: "external",
      managed: { collapsed: true, showDescendants: true },
      external: { path: "/workspace/Other", collapsed: true, showDescendants: true },
    }),
  );
  const action = requestStudyFolderReveal({
    tree: "managed",
    directoryId: "target",
    directoryIds: ["target", "child"],
  });

  const result = studiesReducer(initial, action);

  expect(result.filters).toEqual({
    ...initial.filters,
    activeTree: "managed",
    managed: {
      ...initial.filters.managed,
      collapsed: false,
      directoryId: "target",
      directoryIds: ["target", "child"],
    },
  });
  expect(result.folderRevealRequest).toEqual(action.payload);
});

test("revealing an external folder opens only its section", () => {
  const initial = studiesReducer(
    undefined,
    updateStudyFilters({
      activeTree: "managed",
      managed: { directoryId: "other", directoryIds: ["other"], collapsed: true },
      external: { path: "/workspace/Old", collapsed: true },
    }),
  );

  const result = studiesReducer(
    initial,
    requestStudyFolderReveal({
      tree: "external",
      path: "/workspace/Target",
    }),
  );

  expect(result.filters).toEqual({
    ...initial.filters,
    activeTree: "external",
    external: { ...initial.filters.external, path: "/workspace/Target", collapsed: false },
  });
});

test("repeated reveals get distinct requests and an older completion cannot clear the latest", () => {
  const folder = { tree: "managed", directoryId: null, directoryIds: null } as const;
  const first = requestStudyFolderReveal(folder);
  const second = requestStudyFolderReveal(folder);

  expect(first.payload.requestId).not.toBe(second.payload.requestId);

  const pending = studiesReducer(studiesReducer(undefined, first), second);
  const afterOldCompletion = studiesReducer(
    pending,
    finishStudyFolderReveal(first.payload.requestId),
  );

  expect(afterOldCompletion.folderRevealRequest).toEqual(second.payload);
  expect(
    studiesReducer(afterOldCompletion, finishStudyFolderReveal(second.payload.requestId))
      .folderRevealRequest,
  ).toBeNull();
});

test("manual navigation cancels a pending reveal", () => {
  const pending = studiesReducer(
    undefined,
    requestStudyFolderReveal({
      tree: "external",
      path: "/workspace/Target",
    }),
  );

  const result = studiesReducer(
    pending,
    updateStudyFilters({
      activeTree: "managed",
      managed: { directoryId: null, directoryIds: null },
    }),
  );

  expect(result.folderRevealRequest).toBeNull();
});
