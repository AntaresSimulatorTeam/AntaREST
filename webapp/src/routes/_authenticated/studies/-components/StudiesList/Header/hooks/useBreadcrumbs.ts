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

import { useSuspenseQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { directoryQueries } from "@/queries/directories/queries";
import type { Directory } from "@/services/api/directories/types";
import { buildDirectoryTree, getDirectoryPath } from "../../../StudyTree/ManagedTree/utils";
import type { BreadcrumbItem } from "../types";

interface UseBreadcrumbsParams {
  activeTree: "managed" | "external";
  managedDirectoryId: string | null;
  externalPath: string;
}

export function useBreadcrumbs({
  activeTree,
  managedDirectoryId,
  externalPath,
}: UseBreadcrumbsParams): BreadcrumbItem[] {
  const { data: directories } = useSuspenseQuery(directoryQueries.list());

  return useMemo((): BreadcrumbItem[] => {
    const homeItem: BreadcrumbItem = {
      label: "root",
      id: null,
      path: null,
    };

    if (activeTree === "managed") {
      return buildManagedBreadcrumbs(homeItem, managedDirectoryId, directories);
    }

    return buildExternalBreadcrumbs(homeItem, externalPath);
  }, [activeTree, managedDirectoryId, externalPath, directories]);
}

function buildManagedBreadcrumbs(
  homeItem: BreadcrumbItem,
  directoryId: string | null,
  directories: Directory[],
): BreadcrumbItem[] {
  if (!directoryId) {
    return [homeItem];
  }

  const directoryTree = buildDirectoryTree(directories);
  const pathIds = getDirectoryPath(directoryTree, directoryId);
  const directoriesById: Record<string, Directory> = Object.fromEntries(
    directories.map((d: Directory) => [d.id, d]),
  );

  return [
    homeItem,
    ...pathIds.map(
      (id): BreadcrumbItem => ({
        label: directoriesById[id]?.name || id,
        id,
        path: null,
      }),
    ),
  ];
}

function buildExternalBreadcrumbs(homeItem: BreadcrumbItem, path: string): BreadcrumbItem[] {
  if (!path) {
    return [homeItem];
  }

  const pathParts = path.split("/").filter(Boolean);

  return [
    homeItem,
    ...pathParts.map(
      (part, index): BreadcrumbItem => ({
        label: part,
        id: null,
        path: `/${pathParts.slice(0, index + 1).join("/")}`,
      }),
    ),
  ];
}
