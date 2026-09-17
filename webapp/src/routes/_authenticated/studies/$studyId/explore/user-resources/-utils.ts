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

import type {
  UserResourceFolder,
  UserResourcesTree,
} from "@/services/api/studies/userResources/types";
import { getFileExtension } from "@/utils/fileUtils";
import type { SvgIconComponent } from "@mui/icons-material";
import BlockIcon from "@mui/icons-material/Block";
import DataObjectIcon from "@mui/icons-material/DataObject";
import FolderIcon from "@mui/icons-material/Folder";
import ImageIcon from "@mui/icons-material/Image";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type TreeItemData = UserResourceFolder | string;

export type TreeItemType = "json" | "text" | "image" | "folder" | "unsupported";

export interface TreeItemInfo {
  type: TreeItemType;
  name: string;
  path: string;
  data: TreeItemData;
}

export interface DataCompProps extends TreeItemInfo {
  studyId: string;
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const ROOT_FOLDER_PATH = "";
export const ROOT_FOLDER_NAME = "root";

const SUPPORTED_TEXT_EXTENSIONS = [
  "txt",
  "xml",
  "properties",
  "log",
  "csv",
  "tsv",
  "ini",
  "yml",
  "json",
] as const;

const SUPPORTED_IMAGE_EXTENSIONS = ["png", "jpg", "jpeg", "gif", "svg"] as const;

const iconByTreeItemType: Record<TreeItemType, SvgIconComponent> = {
  json: DataObjectIcon,
  text: TextSnippetIcon,
  image: ImageIcon,
  folder: FolderIcon,
  unsupported: BlockIcon,
} as const;

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

/**
 * Gets the icon component for a given tree item type.
 *
 * @param type - The type of the tree item.
 * @returns The corresponding icon component.
 */
export function getTreeItemIcon(type: TreeItemType): SvgIconComponent {
  return iconByTreeItemType[type];
}

/**
 * Checks if a tree item is a folder.
 *
 * @param treeItem - The tree item to check.
 * @returns True if the tree item is a folder, false otherwise.
 */
export function isTreeItemFolder(treeItem: TreeItemData): treeItem is UserResourceFolder {
  return typeof treeItem === "object";
}

/**
 * Gets the type of a tree item.
 *
 * @param treeItem - The tree item to determine the type for.
 * @returns The corresponding tree item type.
 */
export function getTreeItemType(treeItem: TreeItemData): TreeItemType {
  if (isTreeItemFolder(treeItem)) {
    return "folder";
  }

  const fileExtension = getFileExtension(treeItem);

  if (SUPPORTED_TEXT_EXTENSIONS.some((ext) => fileExtension === ext.toLowerCase())) {
    if (fileExtension === "json") {
      return "json";
    }
    return "text";
  }

  if (SUPPORTED_IMAGE_EXTENSIONS.some((ext) => fileExtension === ext.toLowerCase())) {
    return "image";
  }

  return "unsupported";
}

/**
 * Retrieves a tree item from the user resources tree based on the provided path segments.
 *
 * @param pathSegments - The segments of the path to the desired tree item.
 * @param tree - The tree data to search within.
 * @returns The tree item corresponding to the path segments, or undefined if not found.
 */
export function getTreeItem(
  pathSegments: string[],
  tree: UserResourcesTree | UserResourceFolder,
): UserResourceFolder | string | undefined {
  if (pathSegments.length === 0) {
    return undefined;
  }

  const [firstSegment, ...restSegments] = pathSegments;

  if (restSegments.length === 0) {
    return (
      tree.directories.find((dir) => dir.name === firstSegment) ??
      tree.files.find((filename) => filename === firstSegment)
    );
  }

  const nextDirectory = tree.directories.find((dir) => dir.name === firstSegment);

  return nextDirectory ? getTreeItem(restSegments, nextDirectory) : undefined;
}
