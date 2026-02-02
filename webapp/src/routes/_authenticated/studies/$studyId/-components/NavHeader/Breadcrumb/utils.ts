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

interface BuildBreadcrumbPathParams {
  studyName: string;
  workspaceName: string;
  folderPath?: string;
}

/**
 * Builds the complete folder path segments for breadcrumb navigation.
 *
 * @param params - The parameters for building the breadcrumb path
 * @param params.studyName - The study name to always include at the end
 * @param params.workspaceName - The workspace name to include in the segments
 * @param params.folderPath - The folder path from study metadata
 * @returns Array of folder names representing the complete path segments
 */
export function buildBreadcrumbPath({
  studyName,
  folderPath,
  workspaceName,
}: BuildBreadcrumbPathParams) {
  const pathSegments = folderPath ? folderPath.split("/").filter(Boolean) : [];

  // Build complete hierarchy including workspace (same pattern as StudyTree)
  const breadcrumbSegments = [workspaceName, ...pathSegments];

  // When no folder path exists, ensure default workspace and study names are included
  // in the breadcrumb segments to maintain navigation context and enable users
  // to navigate back to the study overview or workspace listing
  if (!folderPath) {
    breadcrumbSegments.push(studyName);
    return breadcrumbSegments;
  }

  // Replace the last folder segment with the study name to provide clear navigation context
  // This ensures users always see the study name as the final breadcrumb segment
  // and can click it to return to the study overview page
  breadcrumbSegments[breadcrumbSegments.length - 1] = studyName;

  return breadcrumbSegments;
}
