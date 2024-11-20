/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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
import { mergeStudyTreeAndFolders } from ".";
import { NonStudyFolder, StudyTreeNode } from "../utils";
import { FIXTURES } from "./fixtures";

describe("StudyTree Utils", () => {
  describe("mergeStudyTreeAndFolders", () => {
    test.each(Object.values(FIXTURES))(
      "$name",
      ({ studyTree, folders, expected }) => {
        const result = mergeStudyTreeAndFolders(studyTree, folders);
        expect(result).toEqual(expected);
      },
    );

    test("should handle empty study tree", () => {
      const emptyTree: StudyTreeNode = {
        name: "Root",
        path: "/",
        children: [],
      };
      const result = mergeStudyTreeAndFolders(emptyTree, []);
      expect(result).toEqual(emptyTree);
    });

    test("should handle empty folders array", () => {
      const tree: StudyTreeNode = {
        name: "Root",
        path: "/",
        children: [{ name: "a", path: "/a", children: [] }],
      };
      const result = mergeStudyTreeAndFolders(tree, []);
      expect(result).toEqual(tree);
    });

    test("should handle invalid parent paths", () => {
      const tree: StudyTreeNode = {
        name: "Root",
        path: "/",
        children: [{ name: "a", path: "/a", children: [] }],
      };
      const invalidFolder: NonStudyFolder = {
        name: "invalid",
        path: "/invalid",
        workspace: "nonexistent",
        parentPath: "/nonexistent",
      };
      const result = mergeStudyTreeAndFolders(tree, [invalidFolder]);
      expect(result).toEqual(tree);
    });
  });
});
