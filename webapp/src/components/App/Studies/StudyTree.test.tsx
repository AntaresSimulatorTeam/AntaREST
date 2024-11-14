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

import { mergeStudyTreeAndFolders } from "./StudyTree";
import { StudyTreeNode, NonStudyFolder } from "./utils";

describe("mergeStudyTreeAndFolder", () => {
  test("should merge study tree and folder correctly", () => {
    const studyTree: StudyTreeNode = {
      name: "Root",
      path: "/",
      children: [
        { name: "a", path: "/a", children: [] },
        { name: "b", path: "/b", children: [] },
      ],
    };
    const folder: NonStudyFolder = {
      name: "folder1",
      path: "folder1",
      workspace: "a",
      parentPath: "/a",
    };

    const result = mergeStudyTreeAndFolders(studyTree, [folder]);

    expect(result).toEqual({
      name: "Root",
      path: "/",
      children: [
        {
          name: "a",
          path: "/a",
          children: [{ name: "folder1", path: "/a/folder1", children: [] }],
        },
        { name: "b", path: "/b", children: [] },
      ],
    });
  });

  //   test("should handle empty study tree", () => {
  //     const studyTree: StudyTreeNode = { name: "Root", path: "/", children: [] };
  //     const folder: NonStudyFolder = {
  //       name: "folder1",
  //       path: "folder1",
  //       workspace: "a",
  //       parentPath: "/",
  //     };

  //     const result = mergeStudyTreeAndFolders(studyTree, [folder]);

  //     expect(result).toEqual({
  //       name: "Root",
  //       path: "/",
  //       children: [{ name: "folder1", path: "/folder1", children: [] }],
  //     });
  //   });

  test("should handle nested study tree and folder correctly", () => {
    const studyTree: StudyTreeNode = {
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
    const folder: NonStudyFolder = {
      name: "folder1",
      path: "suba/folder1",
      workspace: "a",
      parentPath: "/a/suba",
    };

    const result = mergeStudyTreeAndFolders(studyTree, [folder]);

    expect(result).toEqual({
      name: "Root",
      path: "/",
      children: [
        {
          name: "a",
          path: "/a",
          children: [
            {
              name: "suba",
              path: "/a/suba",
              children: [
                { name: "folder1", path: "/a/suba/folder1", children: [] },
              ],
            },
          ],
        },
      ],
    });
  });

  test("should not add duplicate folders", () => {
    const studyTree: StudyTreeNode = {
      name: "Root",
      path: "/",
      children: [
        {
          name: "a",
          path: "/a",
          children: [{ name: "folder1", path: "/a/folder1", children: [] }],
        },
      ],
    };
    const folder: NonStudyFolder = {
      name: "folder1",
      path: "/folder1",
      workspace: "a",
      parentPath: "/a",
    };

    const result = mergeStudyTreeAndFolders(studyTree, [folder]);

    expect(result).toEqual({
      name: "Root",
      path: "/",
      children: [
        {
          name: "a",
          path: "/a",
          children: [{ name: "folder1", path: "/a/folder1", children: [] }],
        },
      ],
    });
  });
});

describe("mergeStudyTreeAndFolders", () => {
  test("should merge multiple folders correctly", () => {
    const studyTree: StudyTreeNode = {
      name: "Root",
      path: "/",
      children: [{ name: "a", path: "/a", children: [] }],
    };
    const folders: NonStudyFolder[] = [
      {
        name: "folder1",
        path: "/folder1",
        workspace: "a",
        parentPath: "/a",
      },
      {
        name: "folder2",
        path: "/folder2",
        workspace: "a",
        parentPath: "/a",
      },
    ];

    const result = mergeStudyTreeAndFolders(studyTree, folders);

    expect(result).toEqual({
      name: "Root",
      path: "/",
      children: [
        {
          name: "a",
          path: "/a",
          children: [
            { name: "folder1", path: "/a/folder1", children: [] },
            { name: "folder2", path: "/a/folder2", children: [] },
          ],
        },
      ],
    });
  });
});
