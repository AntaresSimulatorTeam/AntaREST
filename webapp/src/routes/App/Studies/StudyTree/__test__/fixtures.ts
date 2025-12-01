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

export const FIXTURES = {
  basicTree: {
    name: "Basic tree with single level",
    studyTree: {
      name: "Root",
      path: "/",
      children: [
        { name: "a", path: "/a", children: [] },
        { name: "b", path: "/b", children: [] },
      ],
    },
    folders: [
      {
        name: "folder1",
        path: "folder1",
        workspace: "a",
        parentPath: "/a",
      },
    ],
    expected: {
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
    },
  },
  hasChildren: {
    name: "Case where a folder is already in the tree, maybe because he has studies, but now the api return that the folder also contains non study folder",
    studyTree: {
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
    },
    folders: [
      {
        name: "folder1",
        path: "folder1",
        workspace: "a",
        parentPath: "/a",
        hasChildren: true,
      },
    ],
    expected: {
      name: "Root",
      path: "/",
      children: [
        {
          name: "a",
          path: "/a",
          children: [
            {
              name: "folder1",
              path: "/a/folder1",
              children: [],
              hasChildren: true,
            },
          ],
        },
        { name: "b", path: "/b", children: [] },
      ],
    },
  },
  nestedTree: {
    name: "Nested tree structure",
    studyTree: {
      name: "Root",
      path: "/",
      children: [
        {
          name: "a",
          path: "/a",
          children: [{ name: "suba", path: "/a/suba", children: [] }],
        },
      ],
    },
    folders: [
      {
        name: "folder1",
        path: "suba/folder1",
        workspace: "a",
        parentPath: "/a/suba",
      },
    ],
    expected: {
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
              children: [{ name: "folder1", path: "/a/suba/folder1", children: [] }],
            },
          ],
        },
      ],
    },
  },
  duplicateCase: {
    name: "Tree with potential duplicates",
    studyTree: {
      name: "Root",
      path: "/",
      children: [
        {
          name: "a",
          path: "/a",
          children: [{ name: "folder1", path: "/a/folder1", children: [] }],
        },
      ],
    },
    folders: [
      {
        name: "folder1",
        path: "/folder1",
        workspace: "a",
        parentPath: "/a",
      },
    ],
    expected: {
      name: "Root",
      path: "/",
      children: [
        {
          name: "a",
          path: "/a",
          children: [{ name: "folder1", path: "/a/folder1", children: [] }],
        },
      ],
    },
  },
  multipleFolders: {
    name: "Multiple folders merge",
    studyTree: {
      name: "Root",
      path: "/",
      children: [{ name: "a", path: "/a", children: [] }],
    },
    folders: [
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
      {
        name: "folder3",
        path: "/folder3",
        workspace: "a",
        parentPath: "/a",
        hasChildren: true,
      },
    ],
    expected: {
      name: "Root",
      path: "/",
      children: [
        {
          name: "a",
          path: "/a",
          children: [
            { name: "folder1", path: "/a/folder1", children: [] },
            { name: "folder2", path: "/a/folder2", children: [] },
            {
              name: "folder3",
              path: "/a/folder3",
              children: [],
              hasChildren: true,
            },
          ],
        },
      ],
    },
  },
};
