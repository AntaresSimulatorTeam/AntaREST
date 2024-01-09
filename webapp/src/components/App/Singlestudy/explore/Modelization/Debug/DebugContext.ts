import { createContext, useContext } from "react";
import { FileType, TreeData } from "./utils";

interface DebugContextProps {
  treeData: TreeData;
  onFileSelect: (fileType: FileType, filePath: string) => void;
  reloadTreeData: () => void;
}

const initialDebugContextValue: DebugContextProps = {
  treeData: {},
  onFileSelect: () => {},
  reloadTreeData: () => {},
};

export const DebugContext = createContext<DebugContextProps>(
  initialDebugContextValue,
);

export const useDebugContext = (): DebugContextProps =>
  useContext(DebugContext);
