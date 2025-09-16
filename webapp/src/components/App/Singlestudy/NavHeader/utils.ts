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

import * as R from "ramda";
import { DEFAULT_WORKSPACE_NAME } from "@/components/common/utils/constants";

/**
 * Builds the complete folder path hierarchy for breadcrumb navigation.
 *
 * @param folderPath - The folder path from study metadata
 * @param workspaceName - The workspace name to include in the hierarchy
 * @param studyIdToRemove - Study ID to filter out from the path (API adds it automatically)
 * @returns Array of folder names representing the complete path hierarchy
 */
export function buildBreadcrumbPath(
  folderPath: string,
  workspaceName?: string,
  studyIdToRemove?: string,
): string[] {
  const pathSegments = folderPath.split("/").filter(Boolean);

  // Remove study ID if it's the last segment (API adds it automatically)
  if (studyIdToRemove) {
    const lastSegment = R.last(pathSegments);
    if (lastSegment === studyIdToRemove) {
      pathSegments.pop();
    }
  }

  // Build complete hierarchy including workspace (same pattern as StudyTree)
  return workspaceName ? [workspaceName, ...pathSegments] : pathSegments;
}

/**
 * Determines if the breadcrumb should be displayed based on the folder structure.
 *
 * @param pathHierarchy - Array of folder names in the hierarchy
 * @returns true if breadcrumb should be shown, false otherwise
 */
export function shouldShowBreadcrumb(pathHierarchy: string[]) {
  if (pathHierarchy.length === 0) {
    return false;
  }

  // Hide if only default workspace (no meaningful folder structure)
  if (pathHierarchy.length === 1 && pathHierarchy[0] === DEFAULT_WORKSPACE_NAME) {
    return false;
  }

  return true;
}
