/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import DataObjectIcon from "@mui/icons-material/DataObject";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import BlockIcon from "@mui/icons-material/Block";
import FolderIcon from "@mui/icons-material/Folder";
import DatasetIcon from "@mui/icons-material/Dataset";
import { SvgIconComponent } from "@mui/icons-material";
import * as RA from "ramda-adjunct";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type TreeFile = string | string[];

export interface TreeFolder {
  [key: string]: TreeFile | TreeFolder;
}

export type TreeData = TreeFolder | TreeFile;

export type FileType = "json" | "matrix" | "text" | "folder" | "unsupported";

export interface FileInfo {
  fileType: FileType;
  filename: string;
  filePath: string;
  treeData: TreeData;
}

export interface DataCompProps extends FileInfo {
  studyId: string;
  setSelectedFile: (file: FileInfo) => void;
  reloadTreeData: () => void;
}

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

const URL_SCHEMES = {
  MATRIX: ["matrix://", "matrixfile://"],
  JSON: "json://",
  FILE: "file://",
} as const;

const SUPPORTED_EXTENSIONS = [
  ".txt",
  ".log",
  ".csv",
  ".tsv",
  ".ini",
  ".yml",
] as const;

// Maps file types to their corresponding icon components.
const iconByFileType: Record<FileType, SvgIconComponent> = {
  matrix: DatasetIcon,
  json: DataObjectIcon,
  text: TextSnippetIcon,
  folder: FolderIcon,
  unsupported: BlockIcon,
} as const;

/**
 * Gets the icon component for a given file type.
 *
 * @param type - The type of the file.
 * @returns The corresponding icon component.
 */
export function getFileIcon(type: FileType): SvgIconComponent {
  return iconByFileType[type];
}

export function isFolder(treeData: TreeData): treeData is TreeFolder {
  return RA.isPlainObj(treeData);
}

/**
 * Gets the file type based on the tree data.
 *
 * @param treeData - The data of the tree item.
 * @returns The corresponding file type.
 */
export function getFileType(treeData: TreeData): FileType {
  if (isFolder(treeData)) {
    return "folder";
  }

  if (typeof treeData === "string") {
    if (URL_SCHEMES.MATRIX.some((scheme) => treeData.startsWith(scheme))) {
      return "matrix";
    }

    if (treeData.startsWith(URL_SCHEMES.JSON)) {
      return "json";
    }

    // Handle regular files with file:// prefix
    // All files except matrices and json-formatted content use this prefix
    // We filter to only allow extensions that can be properly displayed (.txt, .log, .csv, .tsv, .ini)
    // Other extensions (like .RDS or .xlsx) are marked as unsupported since they can't be shown in the UI
    return treeData.startsWith(URL_SCHEMES.FILE) &&
      SUPPORTED_EXTENSIONS.some((ext) => treeData.endsWith(ext))
      ? "text"
      : "unsupported";
  }

  return "text";
}

/**
 * Checks if a path is protected from deletion
 *
 * @param path - Path to check
 * @returns Whether the path is protected
 */
export function isProtected(path: string): boolean {
  // user/expansion folder and its contents must not be deleted
  return path === "user/expansion" || path.startsWith("user/expansion/");
}
