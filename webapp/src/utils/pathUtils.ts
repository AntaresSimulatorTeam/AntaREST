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
