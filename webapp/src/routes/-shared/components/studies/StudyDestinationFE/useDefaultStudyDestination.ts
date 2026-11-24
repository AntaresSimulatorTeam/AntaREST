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

import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudyFilters } from "@/redux/selectors";
import type { Directory } from "@/services/api/directories/types";
import type { DirectoryDestination } from "./types";

/**
 * Returns the current managed directory, falling back to root for external or stale selections.
 *
 * @param directories - Available managed directories.
 * @returns Initial destination for a new or imported study.
 */
export function useDefaultStudyDestination(directories: Directory[]): DirectoryDestination {
  const { activeTree, managed } = useAppSelector(getStudyFilters);
  const directoryId =
    activeTree === "managed" && directories.some(({ id }) => id === managed.directoryId)
      ? managed.directoryId
      : null;

  return { directoryId, newSubdirectoriesPath: "" };
}
