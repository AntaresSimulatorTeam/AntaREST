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
import { sortByName } from "@/services/utils";
import type { DirectoryDestination } from "./types";

/**
 * Creates a `Map` from a flat directory list for O(1) id-based lookups.
 *
 * @param directories - Flat array of {@link Directory} objects.
 * @returns `Map` of directory id → {@link Directory}.
 */
export function mapDirectoriesById(directories: Directory[]): Map<string, Directory> {
  return new Map(directories.map((directory) => [directory.id, directory]));
}

/**
 * Returns direct children of the given parent, sorted alphabetically (case-insensitive).
 *
 * @param parentId - Parent directory id, or `null` for root-level directories.
 * @param directories - Flat array of Directory objects.
 * @returns Sorted array of direct child directories.
 */
export function getDirectChildren(parentId: string | null, directories: Directory[]): Directory[] {
  return sortByName(directories.filter((directory) => directory.parentId === parentId));
}

/**
 * Returns the ancestor chain from the root down to the given directory (inclusive).
 *
 * E.g. for root → a → b → c, returns [a, b, c].
 *
 * @param id - Directory id to start from.
 * @param index - Pre-built directory map from {@link mapDirectoriesById}.
 * @returns Ordered array from root ancestor to the given directory.
 */
export function getDirectoryAncestors(id: string, index: Map<string, Directory>): Directory[] {
  const chain: Directory[] = [];
  let current = index.get(id);

  while (current) {
    chain.unshift(current);
    current = current.parentId ? index.get(current.parentId) : undefined;
  }

  return chain;
}

/**
 * Resolves a {@link DirectoryDestination} into the slash-separated directory path
 * that legacy API endpoints (`moveStudy`, `copyStudy`) expect.
 *
 * The active directory ID is resolved to its ancestor name chain, then
 * joined with `newSubdirectoriesPath` (the optional path of new sub-directories
 * to create). Only present parts are joined, so the result is always clean.
 *
 * TODO: Move to the API layer once the Tanstack Query migration is complete.
 *
 * @param directory - The structured directory destination from the form.
 * @param directories - Flat directory list (should be freshly fetched at call time).
 * @returns Slash-separated directory path (e.g. `"directoryA/subB/newDir"`), or `""` for root.
 */
export function toDirectoryPath(directory: DirectoryDestination, directories: Directory[]): string {
  const index = mapDirectoriesById(directories);

  const base = directory.directoryId
    ? getDirectoryAncestors(directory.directoryId, index)
        .map((dir) => dir.name)
        .join("/")
    : "";

  return [base, directory.newSubdirectoriesPath].filter(Boolean).join("/");
}
