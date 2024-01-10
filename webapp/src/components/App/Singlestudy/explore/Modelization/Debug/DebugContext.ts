import { createContext, useContext } from "react";
import type { File } from "./utils";

const initialDebugContextValue = {
  onFileSelect: (file: File): void => {},
  reloadTreeData: (): void => {},
};

const DebugContext = createContext(initialDebugContextValue);

export const useDebugContext = (): typeof initialDebugContextValue =>
  useContext(DebugContext);

export default DebugContext;
