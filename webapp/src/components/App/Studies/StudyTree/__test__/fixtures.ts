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

import { StudyType, type StudyMetadata } from "@/types/types";

function createStudyMetadata(folder: string, workspace: string): StudyMetadata {
  return {
    id: "test-study-id",
    name: "Test Study",
    creationDate: "2024-01-01",
    modificationDate: "2024-01-02",
    owner: { id: 1, name: "Owner 1" },
    type: StudyType.RAW,
    version: "v1",
    workspace,
    managed: false,
    archived: false,
    groups: [],
    folder,
    publicMode: "NONE",
  };
}

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

export const FIXTURES_BUILD_STUDY_TREE = {
  simpleCase: {
    name: "Basic case",
    studies: [createStudyMetadata("studies/team1/myFolder", "workspace")],
    expected: {
      name: "root",
      path: "",
      children: [
        {
          name: "default",
          path: "/default",
          children: [],
        },
        {
          name: "workspace",
          path: "/workspace",
          children: [
            {
              name: "studies",
              path: "/workspace/studies",
              children: [
                {
                  name: "team1",
                  path: "/workspace/studies/team1",
                  children: [],
                },
              ],
            },
          ],
        },
      ],
    },
  },
  multiplieStudies: {
    name: "Multiple studies case",
    studies: [
      createStudyMetadata("studies/team1/study", "workspace"),
      createStudyMetadata("studies/team2/study", "workspace"),
      createStudyMetadata("studies/team3/study", "workspace"),
      createStudyMetadata("archives/team4/study", "workspace2"),
    ],
    expected: {
      name: "root",
      path: "",
      children: [
        {
          name: "default",
          path: "/default",
          children: [],
        },
        {
          name: "workspace",
          path: "/workspace",
          children: [
            {
              name: "studies",
              path: "/workspace/studies",
              children: [
                {
                  name: "team1",
                  path: "/workspace/studies/team1",
                  children: [],
                },
                {
                  name: "team2",
                  path: "/workspace/studies/team2",
                  children: [],
                },
                {
                  name: "team3",
                  path: "/workspace/studies/team3",
                  children: [],
                },
              ],
            },
          ],
        },
        {
          name: "workspace2",
          path: "/workspace2",
          children: [
            {
              name: "archives",
              path: "/workspace2/archives",
              children: [
                {
                  name: "team4",
                  path: "/workspace2/archives/team4",
                  children: [],
                },
              ],
            },
          ],
        },
      ],
    },
  },
};
