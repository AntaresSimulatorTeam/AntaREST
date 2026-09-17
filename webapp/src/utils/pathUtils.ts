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

/**
 * Get parent paths of a given path.
 *
 * @example
 * getParentPaths("a/b/c/d"); // Returns: ["a", "a/b", "a/b/c"]
 *
 * @param path - The path from which to get the parent paths.
 * @returns The parent paths.
 */
export function getParentPaths(path: string) {
  return path
    .split("/")
    .slice(0, -1) // Remove the last item
    .map((_, index, arr) => arr.slice(0, index + 1).join("/"));
}

/**
 * Get the last segment of a given path.
 *
 * @example
 * getLastPathSegment("a/b/c/d"); // Returns: "d"
 * getLastPathSegment("a/b/c/d/"); // Returns: "d"
 *
 * @param path - The path from which to get the last segment.
 * @returns The last segment of the path.
 */
export function getLastPathSegment(path: string) {
  const segments = path.replace(/\/+$/, "").split("/");
  return segments[segments.length - 1];
}

/**
 * Join multiple paths into a single path, ensuring that there are no duplicate slashes.
 *
 * @example
 * joinPaths("a/b", "c/d"); // Returns: "a/b/c/d"
 * joinPaths("a/b/", "/c/d"); // Returns: "a/b/c/d"
 * joinPaths("/a/b/", "/c/d/"); // Returns: "/a/b/c/d/"
 *
 * @param paths - The paths to join.
 * @returns The joined path.
 */
export function joinPaths(...paths: string[]): string {
  const joined = paths.join("/").replace(/\/+/g, "/");
  return joined;
}
