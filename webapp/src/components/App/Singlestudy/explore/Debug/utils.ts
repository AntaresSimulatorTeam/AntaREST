import DataObjectIcon from "@mui/icons-material/DataObject";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import ImageIcon from "@mui/icons-material/Image";
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

export type FileType = "json" | "matrix" | "text" | "image" | "folder";

export interface FileInfo {
  fileType: FileType;
  filename: string;
  filePath: string;
  treeData: TreeData;
}

export interface DataCompProps extends FileInfo {
  studyId: string;
  enableImport: boolean;
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
  image: ImageIcon,
  folder: FolderIcon,
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
    if (treeData.startsWith("file://") && treeData.endsWith(".ico")) {
      return "image";
    }
  }
  return isFolder(treeData) ? "folder" : "text";
}

////////////////////////////////////////////////////////////////
// Tree
////////////////////////////////////////////////////////////////

/**
 * Get parent paths of a given path.
 *
 * @example
 * getParentPaths("a/b/c/d"); // Returns: ["a", "a/b", "a/b/c"]
 *
 * @param path - The path from which to get the parent paths.
 * @returns The parent paths.
 */
export function getParentPaths(path: string) {
  return path
    .split("/")
    .slice(0, -1) // Remove the last item
    .map((_, index, arr) => arr.slice(0, index + 1).join("/"));
}
