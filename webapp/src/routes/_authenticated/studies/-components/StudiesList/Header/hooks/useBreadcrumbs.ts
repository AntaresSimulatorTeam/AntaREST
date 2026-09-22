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

import { useMemo } from "react";
import { TREE_ROOT_NAME } from "@/components/utils/constants";
import type { Directory } from "@/services/api/directories/types";
import { buildDirectoryTree, getDirectoryPath } from "../../../StudyTree/ManagedTree/utils";
import type { BreadcrumbItem } from "../types";

interface UseBreadcrumbsParams {
  activeTree: "managed" | "external";
  managedDirectoryId: string | null;
  externalPath: string;
  directories: Directory[];
}

export function useBreadcrumbs({
  activeTree,
  managedDirectoryId,
  externalPath,
  directories,
}: UseBreadcrumbsParams): BreadcrumbItem[] {
  return useMemo((): BreadcrumbItem[] => {
    const rootItem: BreadcrumbItem = {
      label: TREE_ROOT_NAME,
      id: null,
      path: null,
    };

    if (activeTree === "managed") {
      return buildManagedBreadcrumbs(rootItem, managedDirectoryId, directories);
    }

    return buildExternalBreadcrumbs(rootItem, externalPath);
  }, [activeTree, managedDirectoryId, externalPath, directories]);
}

function buildManagedBreadcrumbs(
  rootItem: BreadcrumbItem,
  directoryId: string | null,
  directories: Directory[],
): BreadcrumbItem[] {
  if (!directoryId) {
    return [rootItem];
  }

  const directoryTree = buildDirectoryTree(directories);
  const pathIds = getDirectoryPath(directoryTree, directoryId);
  const directoriesById: Record<string, Directory> = Object.fromEntries(
    directories.map((d: Directory) => [d.id, d]),
  );

  return [
    rootItem,
    ...pathIds.map(
      (id): BreadcrumbItem => ({
        label: directoriesById[id]?.name || id,
        id,
        path: null,
      }),
    ),
  ];
}

function buildExternalBreadcrumbs(rootItem: BreadcrumbItem, path: string): BreadcrumbItem[] {
  if (!path) {
    return [rootItem];
  }

  const pathParts = path.split("/").filter(Boolean);

  return [
    rootItem,
    ...pathParts.map(
      (part, index): BreadcrumbItem => ({
        label: part,
        id: null,
        path: `/${pathParts.slice(0, index + 1).join("/")}`,
      }),
    ),
  ];
}
