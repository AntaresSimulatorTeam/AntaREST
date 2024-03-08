import DataObjectIcon from "@mui/icons-material/DataObject";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import FolderIcon from "@mui/icons-material/Folder";
import DatasetIcon from "@mui/icons-material/Dataset";
import { SvgIconComponent } from "@mui/icons-material";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type FileType = "json" | "file" | "matrix";

export interface File {
  fileType: FileType;
  filePath: string;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type TreeData = Record<string, any> | string;

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

//Maps file types and folder to their corresponding icon components.
const iconByFileType: Record<FileType | "folder", SvgIconComponent> = {
  matrix: DatasetIcon,
  json: DataObjectIcon,
  folder: FolderIcon,
  file: TextSnippetIcon,
} as const;

/**
 * Gets the icon component for a given file type or folder.
 *
 * @param type - The type of the file or "folder".
 * @returns The corresponding icon component.
 */
export const getFileIcon = (type: FileType | "folder"): SvgIconComponent => {
  return iconByFileType[type] || TextSnippetIcon;
};

/**
 * Determines the file type based on the tree data.
 *
 * @param treeData - The data of the tree item.
 * @returns The determined file type or "folder".
 */
export const determineFileType = (treeData: TreeData): FileType | "folder" => {
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
  return typeof treeData === "object" ? "folder" : "file";
};

/**
 * Filters out specific keys from the tree data.
 *
 * @param data - The original tree data.
 * @returns The filtered tree data.
 */
export const filterTreeData = (data: TreeData): TreeData => {
  const excludedKeys = new Set(["Desktop", "study", "logs"]);

  return Object.fromEntries(
    Object.entries(data).filter(([key]) => !excludedKeys.has(key)),
  );
};
