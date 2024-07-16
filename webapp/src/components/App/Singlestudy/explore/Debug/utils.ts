import DataObjectIcon from "@mui/icons-material/DataObject";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import FolderIcon from "@mui/icons-material/Folder";
import DatasetIcon from "@mui/icons-material/Dataset";
import { SvgIconComponent } from "@mui/icons-material";
import * as RA from "ramda-adjunct";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type FileType = "json" | "matrix" | "file" | "folder";

export interface FileInfo {
  fileType: FileType;
  filePath: string;
}

export type TreeFile = string | string[];

export interface TreeFolder {
  [key: string]: TreeFile | TreeFolder;
}

export type TreeData = TreeFolder | TreeFile;

////////////////////////////////////////////////////////////////
// File Info
////////////////////////////////////////////////////////////////

// Maps file types to their corresponding icon components.
const iconByFileType: Record<FileType, SvgIconComponent> = {
  matrix: DatasetIcon,
  json: DataObjectIcon,
  folder: FolderIcon,
  file: TextSnippetIcon,
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
  if (typeof treeData === "string") {
    if (
      treeData.startsWith("matrix://") ||
      treeData.startsWith("matrixfile://")
    ) {
      return "matrix";
    }
    if (treeData.startsWith("json://") || treeData.endsWith(".json")) {
      return "json";
    }
  }
  return isFolder(treeData) ? "folder" : "file";
}
