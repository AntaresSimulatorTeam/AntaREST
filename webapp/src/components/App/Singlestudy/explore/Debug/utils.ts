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
import type { StudyMetadata } from "../../../../../common/types";

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
  canEdit: boolean;
  setSelectedFile: (file: FileInfo) => void;
  reloadTreeData: () => void;
}

////////////////////////////////////////////////////////////////
// File Info
////////////////////////////////////////////////////////////////

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
    // Handle matrix files
    if (
      treeData.startsWith("matrix://") ||
      treeData.startsWith("matrixfile://")
    ) {
      return "matrix";
    }

    // Handle files displayed as JSON by the API even though they are .ini files in the filesystem.
    // The json:// prefix or .json extension indicates the content should be viewed as JSON.
    if (treeData.startsWith("json://") || treeData.endsWith(".json")) {
      return "json";
    }

    // Handle regular files with file:// prefix
    // All files except matrices and json-formatted content use this prefix
    // We filter to only allow extensions that can be properly displayed (.txt, .log, .csv, .tsv, .ini)
    // Other extensions (like .RDS or .xlsx) are marked as unsupported since they can't be shown in the UI
    if (treeData.startsWith("file://")) {
      const supportedTextExtensions = [".txt", ".log", ".csv", ".tsv", ".ini"];

      // Check if the file ends with any of the supported extensions
      if (supportedTextExtensions.some((ext) => treeData.endsWith(ext))) {
        return "text";
      }

      // Any other extension with file:// prefix is unsupported
      return "unsupported";
    }
  }

  // Default to text for any other string content
  return "text";
}

////////////////////////////////////////////////////////////////
// Rights
////////////////////////////////////////////////////////////////

/**
 * Checks if a study's file can be edited.
 *
 * @param study  - The study where the file is located.
 * @param filePath - The path of the file.
 * @returns True if the file can be edited, false otherwise.
 */
export function canEditFile(study: StudyMetadata, filePath: string): boolean {
  return (
    !study.archived &&
    (filePath === "user" || filePath.startsWith("user/")) &&
    // To remove when Xpansion tool configuration will be moved to "input/expansion" directory
    !(filePath === "user/expansion" || filePath.startsWith("user/expansion/"))
  );
}
