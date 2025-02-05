/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import { FIXTURES, FIXTURES_BUILD_STUDY_TREE } from "./fixtures";
import {
  buildStudyTree,
  insertFoldersIfNotExist,
  insertWorkspacesIfNotExist,
  mergeDeepRightStudyTree,
  innerJoin,
} from "../utils";
import type { NonStudyFolderDTO, StudyTreeNode } from "../types";

describe("StudyTree Utils", () => {
  describe("mergeStudyTreeAndFolders", () => {
    test.each(Object.values(FIXTURES))("$name", ({ studyTree, folders, expected }) => {
      const result = insertFoldersIfNotExist(studyTree, folders);
      expect(result).toEqual(expected);
    });

    test("should handle empty study tree", () => {
      const emptyTree: StudyTreeNode = {
        name: "Root",
        path: "/",
        children: [],
      };
      const result = insertFoldersIfNotExist(emptyTree, []);
      expect(result).toEqual(emptyTree);
    });

    test("should handle empty folders array", () => {
      const tree: StudyTreeNode = {
        name: "Root",
        path: "/",
        children: [{ name: "a", path: "/a", children: [] }],
      };
      const result = insertFoldersIfNotExist(tree, []);
      expect(result).toEqual(tree);
    });

    test("should handle invalid parent paths", () => {
      const tree: StudyTreeNode = {
        name: "Root",
        path: "/",
        children: [{ name: "a", path: "/a", children: [] }],
      };
      const invalidFolder: NonStudyFolderDTO = {
        name: "invalid",
        path: "/invalid",
        workspace: "nonexistent",
        parentPath: "/nonexistent",
      };
      const result = insertFoldersIfNotExist(tree, [invalidFolder]);
      expect(result).toEqual(tree);
    });

    test("should handle empty workspaces", () => {
      const tree: StudyTreeNode = {
        name: "Root",
        path: "/",
        children: [
          {
            name: "a",
            path: "/a",
            children: [{ name: "suba", path: "/a/suba", children: [] }],
          },
        ],
      };
      const workspaces: string[] = [];
      const result = insertWorkspacesIfNotExist(tree, workspaces);
      expect(result).toEqual(tree);
    });

    test("should merge workspaces", () => {
      const tree: StudyTreeNode = {
        name: "Root",
        path: "/",
        children: [
          {
            name: "a",
            path: "/a",
            children: [{ name: "suba", path: "/a/suba", children: [] }],
          },
        ],
      };
      const expected: StudyTreeNode = {
        name: "Root",
        path: "/",
        children: [
          {
            name: "a",
            path: "/a",
            children: [{ name: "suba", path: "/a/suba", children: [] }],
          },
          { name: "workspace1", path: "/workspace1", children: [] },
          { name: "workspace2", path: "/workspace2", children: [] },
        ],
      };

      const workspaces = ["a", "workspace1", "workspace2"];
      const result = insertWorkspacesIfNotExist(tree, workspaces);
      expect(result).toEqual(expected);
    });

    test.each(Object.values(FIXTURES_BUILD_STUDY_TREE))("$name", ({ studies, expected }) => {
      const result = buildStudyTree(studies);
      expect(result).toEqual(expected);
    });
  });

  test("merge two trees", () => {
    const lTree: StudyTreeNode = {
      name: "root",
      path: "/",
      children: [
        { name: "A", path: "/A", children: [] },
        { name: "B", path: "/B", children: [] },
      ],
    };
    const rTree: StudyTreeNode = {
      name: "root",
      path: "/",
      children: [
        { name: "A", path: "/A1", children: [] },
        { name: "C", path: "/C", children: [] },
      ],
    };

    const mergedTree = mergeDeepRightStudyTree(lTree, rTree);
    assert(mergedTree.children.length === 3, "Merged tree should have 3 children");
    assert(
      mergedTree.children.some((child) => child.name === "A"),
      "Node A should be in merged tree",
    );
    assert(
      mergedTree.children.some((child) => child.name === "B"),
      "Node B should be in merged tree",
    );
    assert(
      mergedTree.children.some((child) => child.name === "C"),
      "Node C should be in merged tree",
    );
    assert(
      mergedTree.children.some((child) => child.name === "A" && child.path === "/A1"),
      "Node A path should be /A1",
    );
  });

  test("merge two trees, empty tree case", () => {
    const emptyTree: StudyTreeNode = { name: "root", path: "/", children: [] };
    const singleNodeTree: StudyTreeNode = {
      name: "root",
      path: "/",
      children: [{ name: "A", path: "/A", children: [] }],
    };

    assert(
      mergeDeepRightStudyTree(emptyTree, emptyTree).children.length === 0,
      "Merging two empty trees should return an empty tree",
    );

    assert(
      mergeDeepRightStudyTree(singleNodeTree, emptyTree).children.length === 1,
      "Merging a tree with an empty tree should keep original children",
    );

    assert(
      mergeDeepRightStudyTree(emptyTree, singleNodeTree).children.length === 1,
      "Merging an empty tree with a tree should adopt its children",
    );
  });

  test("inner join", () => {
    const tree1: StudyTreeNode[] = [
      { name: "A", path: "/A", children: [] },
      { name: "B", path: "/B", children: [] },
    ];
    const tree2: StudyTreeNode[] = [
      { name: "A", path: "/A1", children: [] },
      { name: "C", path: "/C", children: [] },
    ];

    const result = innerJoin(tree1, tree2);
    assert(result.length === 1, "Should match one node");
    assert(result[0][0].name === "A" && result[0][1].name === "A");

    const result2 = innerJoin(tree1, tree1);
    assert(result2.length === 2, "Should match both nodes");
    assert(result2[0][0].name === "A" && result2[0][1].name === "A");
    assert(result2[1][0].name === "B" && result2[1][1].name === "B");
  });

  test("inner join, empty tree case", () => {
    const tree1: StudyTreeNode[] = [];
    const tree2: StudyTreeNode[] = [];
    assert(innerJoin(tree1, tree2).length === 0, "Empty trees should return no matches");

    const tree3: StudyTreeNode[] = [{ name: "X", path: "/X", children: [] }];
    assert(
      innerJoin(tree3, tree2).length === 0,
      "Tree with unmatched node should return no matches",
    );
    assert(
      innerJoin(tree3, tree2).length === 0,
      "Tree with unmatched node should return no matches",
    );
  });
});
