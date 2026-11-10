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
  type StudyFolder,
} from "../studies";

vi.mock("@/redux/store", () => ({ default: { dispatch: vi.fn() } }));

const MANAGED_ROOT = { tree: "managed", directoryId: null, directoryIds: null } as const;
const EXTERNAL_FOLDER = { tree: "external", path: "/workspace/Target" } as const;

test.each([
  {
    folder: { tree: "managed", directoryId: "target", directoryIds: ["target", "child"] },
    selection: { directoryId: "target", directoryIds: ["target", "child"] },
  },
  { folder: EXTERNAL_FOLDER, selection: { path: EXTERNAL_FOLDER.path } },
] satisfies Array<{ folder: StudyFolder; selection: object }>)(
  "revealing a $folder.tree folder opens only its section and preserves other filters",
  ({ folder, selection }) => {
    const initial = studiesReducer(
      undefined,
      updateStudyFilters({
        search: "scenario",
        type: "variants",
        activeTree: folder.tree === "managed" ? "external" : "managed",
        managed: { directoryId: "other", collapsed: true, showDescendants: true },
        external: { path: "/workspace/Other", collapsed: true, showDescendants: true },
      }),
    );
    const action = requestStudyFolderReveal(folder);

    const result = studiesReducer(initial, action);

    expect(result.filters).toEqual({
      ...initial.filters,
      activeTree: folder.tree,
      [folder.tree]: { ...initial.filters[folder.tree], ...selection, collapsed: false },
    });
    expect(result.folderRevealRequest).toEqual(action.payload);
  },
);

test("repeated reveals get distinct requests and an older completion cannot clear the latest", () => {
  const first = requestStudyFolderReveal(MANAGED_ROOT);
  const second = requestStudyFolderReveal(MANAGED_ROOT);

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
  const pending = studiesReducer(undefined, requestStudyFolderReveal(EXTERNAL_FOLDER));

  const result = studiesReducer(
    pending,
    updateStudyFilters({
      activeTree: "managed",
      managed: { directoryId: null, directoryIds: null },
    }),
  );

  expect(result.folderRevealRequest).toBeNull();
});
