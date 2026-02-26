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
  buildDirectoryIndex,
  getDirectChildren,
  getDirectoryAncestors,
  toDirectoryPath,
} from "../utils";

/**
 * Builds a flat directory list representing:
 *
 * root
 * ├── directoryA        (id: "a")
 * │   ├── subA1      (id: "a1")
 * │   └── subA2      (id: "a2")
 * │       └── deep   (id: "a2d")
 * ├── directoryB        (id: "b")
 * └── directoryC        (id: "c")
 *
 * @returns A flat list of directories.
 */
function makeDirectories(): Directory[] {
  return [
    { id: "a", name: "directoryA", parentId: null },
    { id: "a1", name: "subA1", parentId: "a" },
    { id: "a2", name: "subA2", parentId: "a" },
    { id: "a2d", name: "deep", parentId: "a2" },
    { id: "b", name: "directoryB", parentId: null },
    { id: "c", name: "directoryC", parentId: null },
  ];
}

describe("buildDirectoryIndex", () => {
  test("every directory is retrievable by its id", () => {
    const directories = makeDirectories();
    const index = buildDirectoryIndex(directories);

    expect(index.size).toBe(directories.length);

    for (const directory of directories) {
      expect(index.get(directory.id)).toBe(directory);
    }
  });

  test("returns an empty map for an empty array", () => {
    expect(buildDirectoryIndex([]).size).toBe(0);
  });
});

describe("getDirectChildren", () => {
  const directories = makeDirectories();

  test("returns an empty array for a leaf directory", () => {
    expect(getDirectChildren("a2d", directories)).toEqual([]);
  });

  test("returns an empty array for an unknown parentId", () => {
    expect(getDirectChildren("nonexistent", directories)).toEqual([]);
  });

  test("results are sorted alphabetically (case-insensitive)", () => {
    const custom: Directory[] = [
      { id: "1", name: "Z-directory", parentId: null },
      { id: "2", name: "a-directory", parentId: null },
      { id: "3", name: "M-directory", parentId: null },
      { id: "4", name: "b-directory", parentId: null },
    ];
    const names = getDirectChildren(null, custom).map((directory) => directory.name);
    expect(names).toEqual(["a-directory", "b-directory", "M-directory", "Z-directory"]);
  });
});

describe("getDirectoryAncestors", () => {
  const index = buildDirectoryIndex(makeDirectories());

  test("returns a single-element array for a root-level directory", () => {
    const ids = getDirectoryAncestors("a", index).map((directory) => directory.id);
    expect(ids).toEqual(["a"]);
  });

  test("returns the full chain from root ancestor to a deeply nested directory", () => {
    const ids = getDirectoryAncestors("a2d", index).map((directory) => directory.id);
    expect(ids).toEqual(["a", "a2", "a2d"]);
  });
});

describe("toDirectoryPath", () => {
  const directories = makeDirectories();

  test('returns "" for root with no new directory path', () => {
    expect(toDirectoryPath({ id: null, newDirectoryPath: "" }, directories)).toBe("");
  });

  test("returns the directory name for a root-level directory", () => {
    expect(toDirectoryPath({ id: "a", newDirectoryPath: "" }, directories)).toBe("directoryA");
  });

  test("returns the full nested string for a deeply nested directory", () => {
    expect(toDirectoryPath({ id: "a2d", newDirectoryPath: "" }, directories)).toBe(
      "directoryA/subA2/deep",
    );
  });

  test("returns directory string + new directory path when both are present", () => {
    expect(toDirectoryPath({ id: "a2", newDirectoryPath: "newDir" }, directories)).toBe(
      "directoryA/subA2/newDir",
    );
  });

  test("returns just the new directory path when id is null", () => {
    expect(toDirectoryPath({ id: null, newDirectoryPath: "new" }, directories)).toBe("new");
  });

  test("returns directory string + multi-segment new directory path", () => {
    expect(toDirectoryPath({ id: "a", newDirectoryPath: "x/y/z" }, directories)).toBe(
      "directoryA/x/y/z",
    );
  });

  test('returns "" for unknown id with no new directory path', () => {
    expect(toDirectoryPath({ id: "nonexistent", newDirectoryPath: "" }, directories)).toBe("");
  });
});
