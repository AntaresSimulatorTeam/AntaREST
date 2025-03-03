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

import DataObjectIcon from "@mui/icons-material/DataObject";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import BlockIcon from "@mui/icons-material/Block";
import FolderIcon from "@mui/icons-material/Folder";
import DatasetIcon from "@mui/icons-material/Dataset";
import type { SvgIconComponent } from "@mui/icons-material";
import * as RA from "ramda-adjunct";
import type { StudyMetadata } from "../../../../../types/types";
import type { MatrixDataDTO } from "@/components/common/Matrix/shared/types";

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

interface ContentParsingOptions {
  filePath: string;
  fileType: string;
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

const URL_SCHEMES = {
  MATRIX: ["matrix://", "matrixfile://"],
  JSON: "json://",
  FILE: "file://",
} as const;

const SUPPORTED_EXTENSIONS = [".txt", ".log", ".csv", ".tsv", ".ini", ".yml", ".json"] as const;

// Maps file types to their corresponding icon components.
const iconByFileType: Record<FileType, SvgIconComponent> = {
  matrix: DatasetIcon,
  json: DataObjectIcon,
  text: TextSnippetIcon,
  folder: FolderIcon,
  unsupported: BlockIcon,
} as const;

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

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
      SUPPORTED_EXTENSIONS.some((ext) => treeData.toLowerCase().endsWith(ext.toLowerCase()))
      ? "text"
      : "unsupported";
  }

  return "text";
}

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
    // TODO: remove when Xpansion tool configuration will be moved to "input/expansion" directory
    !(filePath === "user/expansion" || filePath.startsWith("user/expansion/"))
  );
}

/**
 * Checks if a file path is within the output folder
 *
 * @param path - The file path to check
 * @returns Whether the path is in the output folder
 */
export function isInOutputFolder(path: string): boolean {
  return path.startsWith("output/");
}

/**
 * Determines if .txt files content is empty
 *
 * @param text - Content of .txt to check
 * @returns boolean indicating if content is effectively empty
 */
export function isEmptyContent(text: string | string[]): boolean {
  if (Array.isArray(text)) {
    return !text || text.every((line) => typeof line === "string" && !line.trim());
  }

  return typeof text === "string" && !text.trim();
}

/**
 * !Temporary workaround for matrix data display in output folders.
 *
 * Context:
 * In output folders, matrix data can be returned by the API in two different formats:
 * 1. As an unparsed JSON string containing the matrix data
 * 2. As an already parsed MatrixDataDTO object
 *
 * This inconsistency exists because the API's matrix parsing behavior differs between
 * output folders and other locations. Additionally, there's a UI requirement to display
 * matrices from output folders as raw text rather than formatted tables.
 *
 * The workaround consists of three functions:
 * 1. getEffectiveFileType: Forces matrix files in output folders to use text display
 * 2. parseResponse: Handles the dual format nature of the API response
 * 3. parseContent: Orchestrates the parsing logic based on file location and type
 *
 * TODO: This temporary solution will be removed once:
 * - The API provides consistent matrix parsing across all folders
 * - UI requirements for matrix display are finalized
 */

/**
 * Forces matrix files in output folders to be displayed as text
 * This is necessary because matrices in output folders need to be shown
 * in their raw format rather than as formatted tables
 *
 * @param filePath - Path to the file being displayed
 * @param originalType - Original file type as determined by the system
 * @returns Modified file type (forces 'text' for matrices in output folders)
 */
export function getEffectiveFileType(filePath: string, originalType: FileType): FileType {
  if (isInOutputFolder(filePath) && originalType === "matrix") {
    return "text";
  }

  return originalType;
}

/**
 * Formats a 2D number array into a string representation
 *
 * @param matrix - 2D array of numbers to format
 * @returns String representation of the matrix
 */
function formatMatrixToString(matrix: number[][]): string {
  return matrix.map((row) => row.map((val) => val.toString()).join("\t")).join("\n");
}

/**
 * Handles parsing of matrix data from the API, dealing with both
 * string and pre-parsed object formats
 *
 * @param res - API response containing matrix data (either MatrixDataDTO or string)
 * @returns Extracted matrix data as a string
 */
function parseResponse(res: string | MatrixDataDTO): string {
  if (typeof res === "object") {
    // Handle case where API has already parsed the JSON into MatrixDataDTO
    return formatMatrixToString(res.data);
  }

  try {
    // Handle case where API returns unparsed JSON string
    // Replace special numeric values with their string representations
    const sanitizedJson = res.replace(/NaN/g, '"NaN"').replace(/Infinity/g, '"Infinity"');

    const parsed = JSON.parse(sanitizedJson);
    return formatMatrixToString(parsed.data);
  } catch {
    // If JSON parsing fails, assume it's plain text
    return res;
  }
}

/**
 * Main content parsing function that orchestrates the matrix display workaround
 *
 * @param content - Raw content from the API (either string or parsed object)
 * @param options - Configuration options including file path and type
 * @returns Processed content ready for display
 */
export function parseContent(content: string, options: ContentParsingOptions): string {
  const { filePath, fileType } = options;

  if (isInOutputFolder(filePath) && fileType === "matrix") {
    // Apply special handling for matrices in output folders
    return parseResponse(content);
  }

  return content || "";
}

// !End of Matrix Display Workaround
