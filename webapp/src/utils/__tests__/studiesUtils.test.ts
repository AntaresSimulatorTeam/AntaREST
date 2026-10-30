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

import type { StudyFilters } from "@/redux/ducks/studies";
import type { Directory } from "@/services/api/directories/types";
import { StorageMode, StudyType, type StudyMetadata } from "@/types/types";
import { filterStudies, getStudyFolder } from "../studiesUtils";

function createStudy(overrides: Partial<StudyMetadata> = {}): StudyMetadata {
  return {
    id: "study",
    name: "Study",
    creationDate: "2026-11-05",
    modificationDate: "2026-11-05",
    owner: { id: 1, name: "Owner" },
    editor: "Editor",
    author: "Author",
    type: StudyType.RAW,
    version: "9.3",
    workspace: "network",
    managed: true,
    archived: false,
    storageMode: StorageMode.FILESYSTEM,
    groups: [],
    publicMode: "NONE",
    directoryId: null,
    ...overrides,
  };
}

const directories: Directory[] = [
  { id: "parent", name: "Parent", parentId: null },
  { id: "folder", name: "Folder", parentId: "parent" },
  { id: "child", name: "Child", parentId: "folder" },
  { id: "grandchild", name: "Grandchild", parentId: "child" },
  { id: "sibling", name: "Sibling", parentId: "parent" },
];

describe("getStudyFolder", () => {
  test.each([null, undefined])("uses the managed root when directoryId is %s", (directoryId) => {
    expect(getStudyFolder(createStudy({ directoryId }), directories)).toEqual({
      tree: "managed",
      directoryId: null,
      directoryIds: null,
    });
  });

  test("includes only the selected managed directory and its descendants", () => {
    expect(getStudyFolder(createStudy({ directoryId: "folder" }), directories)).toEqual({
      tree: "managed",
      directoryId: "folder",
      directoryIds: ["folder", "child", "grandchild"],
    });
  });

  test.each([undefined, "study"])("uses the workspace root for external folder %s", (folder) => {
    const study = createStudy({ managed: false, folder });

    expect(getStudyFolder(study, directories)).toEqual({ tree: "external", path: "/network" });
  });

  test("external navigation and filtering agree on parents and descendant boundaries", () => {
    const selected = createStudy({ id: "selected", managed: false, folder: "/parent//study/" });
    const child = createStudy({ id: "child", managed: false, folder: "parent/child/study" });
    const sibling = createStudy({ id: "sibling", managed: false, folder: "parent-2/study" });
    const otherWorkspace = createStudy({ ...selected, id: "other-workspace", workspace: "other" });
    const studies = [selected, child, sibling, otherWorkspace, createStudy()];
    const path = "/network/parent";
    const filters: StudyFilters = {
      search: "",
      activeTree: "external",
      managed: { directoryId: null, directoryIds: null, showDescendants: false, collapsed: false },
      external: { path, showDescendants: false, collapsed: false },
      type: "all",
      management: "all",
      archive: "all",
      versions: [],
      users: [],
      groups: [],
      tags: [],
    };

    expect(getStudyFolder(selected, directories)).toEqual({ tree: "external", path });
    expect(filterStudies(filters, studies).map(({ id }) => id)).toEqual(["selected"]);
    expect(
      filterStudies(
        { ...filters, external: { ...filters.external, showDescendants: true } },
        studies,
      ).map(({ id }) => id),
    ).toEqual(["selected", "child"]);
  });
});
