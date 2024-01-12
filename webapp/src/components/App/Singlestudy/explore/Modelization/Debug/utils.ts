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

/**
 * Maps file types and folder to their corresponding icon components.
 */
const iconByFileType: Record<FileType | "folder", SvgIconComponent> = {
  matrix: DatasetIcon,
  json: DataObjectIcon,
  folder: FolderIcon,
  file: TextSnippetIcon,
} as const;

/**
 * Gets the icon component for a given file type or folder.
 * @param {FileType | "folder"} type - The type of the file or "folder".
 * @returns {SvgIconComponent} The corresponding icon component.
 */
export const getFileIcon = (type: FileType | "folder"): SvgIconComponent => {
  return iconByFileType[type] || TextSnippetIcon;
};

/**
 * Determines the file type based on the tree data.
 * @param {TreeData} treeData - The data of the tree item.
 * @returns {FileType | "folder"} The determined file type or "folder".
 */
export const determineFileType = (treeData: TreeData): FileType | "folder" => {
  if (typeof treeData === "string") {
    if (
      treeData.startsWith("matrix://") ||
      treeData.startsWith("matrixfile://")
    ) {
      return "matrix";
    }
    if (treeData.startsWith("json://")) {
      return "json";
    }
  }
  return typeof treeData === "object" ? "folder" : "file";
};

/**
 * Filters out specific keys from the tree data.
 * @param {TreeData} data - The original tree data.
 * @returns {TreeData} The filtered tree data.
 */
export const filterTreeData = (data: TreeData): TreeData => {
  const excludedKeys = new Set(["Desktop", "study", "output", "logs"]);

  return Object.fromEntries(
    Object.entries(data).filter(([key]) => !excludedKeys.has(key)),
  );
};
