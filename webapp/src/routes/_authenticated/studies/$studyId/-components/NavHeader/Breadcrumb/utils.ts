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

import {
  buildDirectoryTree,
  getDirectoryPath,
} from "@/routes/_authenticated/studies/-components/StudyTree/ManagedTree/utils";
import type { Directory } from "@/services/api/directories/types";

/**
 * Represents a single item in the breadcrumb navigation.
 *
 * For managed studies (directories API):
 * - id: The directory ID for navigation (null for root and study name)
 * - path: Always null (not used for managed studies)
 *
 * For external studies (path-based):
 * - id: Always null (not used for external studies)
 * - path: The filesystem path for navigation (null for study name)
 */
export interface BreadcrumbItem {
  label: string;
  id: string | null;
  path: string | null;
}

interface BuildExternalBreadcrumbsParams {
  studyName: string;
  workspaceName: string;
  folderPath?: string;
}

interface BuildManagedBreadcrumbsParams {
  studyName: string;
  directoryId: string | null;
  directories: Directory[];
}

/**
 * Builds breadcrumb items for External studies using filesystem paths.
 *
 * External studies are managed through the legacy Explorer API and use
 * filesystem paths for navigation. The breadcrumb structure is:
 * [workspace] > [folder1] > [folder2] > ... > [study name]
 *
 * Each breadcrumb item (except the study name) has a `path` property that
 * represents the filesystem path, which is used when clicking to filter
 * studies by that path in the external tree.
 *
 * @param params - The parameters for building external breadcrumbs
 * @param params.studyName - The study name (always the last segment)
 * @param params.workspaceName - The workspace name (always the first segment)
 * @param params.folderPath - The folder path from study metadata (e.g., "/folder1/folder2")
 * @returns Array of breadcrumb items with path-based navigation
 */
export function buildExternalBreadcrumbs({
  studyName,
  folderPath,
  workspaceName,
}: BuildExternalBreadcrumbsParams): BreadcrumbItem[] {
  const pathSegments = folderPath ? folderPath.split("/").filter(Boolean) : [];

  const breadcrumbSegments = [workspaceName, ...pathSegments];

  // When no folder path exists, return workspace root and study name
  if (!folderPath) {
    return [
      { label: workspaceName, id: null, path: `/${workspaceName}` },
      { label: studyName, id: null, path: null },
    ];
  }

  // Replace the last folder segment with the study name to provide clear navigation context.
  // This ensures users always see the study name as the final breadcrumb segment.
  breadcrumbSegments[breadcrumbSegments.length - 1] = studyName;

  // Build breadcrumb items with cumulative paths for navigation
  return breadcrumbSegments.map((segment, index) => {
    const isLastSegment = index === breadcrumbSegments.length - 1;

    return {
      label: segment,
      id: null,
      // Study name (last segment) has no path since it's not clickable for filtering
      path: isLastSegment ? null : `/${breadcrumbSegments.slice(0, index + 1).join("/")}`,
    };
  });
}

/**
 * Builds breadcrumb items for Managed studies using the directories API.
 *
 * Managed studies are organized in a hierarchical directory structure managed
 * by the backend. The breadcrumb structure is:
 * [root] > [directory1] > [directory2] > ... > [study name]
 *
 * @param params - The parameters for building managed breadcrumbs
 * @param params.studyName - The study name (always the last segment)
 * @param params.directoryId - The directory ID where the study is located (null for root)
 * @param params.directories - List of all directories from the API
 * @returns Array of breadcrumb items with directory-based navigation
 */
export function buildManagedBreadcrumbs({
  studyName,
  directoryId,
  directories,
}: BuildManagedBreadcrumbsParams): BreadcrumbItem[] {
  const rootItem: BreadcrumbItem = {
    label: "root",
    id: null,
    path: null,
  };

  // If no directory, study is at the managed root level
  if (!directoryId) {
    return [rootItem, { label: studyName, id: null, path: null }];
  }

  const directoryTree = buildDirectoryTree(directories);
  const pathIds = getDirectoryPath(directoryTree, directoryId);

  const directoriesById: Record<string, Directory> = Object.fromEntries(
    directories.map((dir: Directory) => [dir.id, dir]),
  );

  return [
    rootItem,
    ...pathIds.map((id) => ({
      label: directoriesById[id]?.name || id,
      id,
      path: null,
    })),
    { label: studyName, id: null, path: null },
  ];
}
